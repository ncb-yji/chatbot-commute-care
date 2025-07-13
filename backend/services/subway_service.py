import requests
from config import Config
from typing import Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
import re
from .subway_data_processor import SubwayDataProcessor

class SubwayService:
    """서울 지하철 API 통신 전용 클래스
    
    API 호출과 응답 처리에만 집중하며,
    데이터 가공은 SubwayDataProcessor에 위임합니다.
    
    ✨ 개선사항: 향상된 예외 처리와 로깅
    """

    def __init__(self):
        self.api_key = Config.SEOUL_API_KEY
        self.base_url = Config.SEOUL_API_BASE_URL
        self.logger = logging.getLogger(__name__)
        
        # 데이터 처리기 초기화
        self.data_processor = SubwayDataProcessor()
        
        # 성능 최적화: 세션 재사용 및 연결 풀링
        self.session = requests.Session()
        
        # 연결 풀링 및 재시도 설정
        retry_strategy = Retry(
            total=2,  # 최대 재시도 횟수
            backoff_factor=0.1,  # 재시도 간격
            status_forcelist=[429, 500, 502, 503, 504]  # 재시도할 HTTP 상태 코드
        )
        
        adapter = HTTPAdapter(
            pool_connections=10,  # 연결 풀 크기
            pool_maxsize=20,      # 최대 연결 수
            max_retries=retry_strategy
        )
        
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 기본 헤더 설정
        self.session.headers.update({
            'User-Agent': 'CommuteCareChatbot/1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
        
        # 역 매핑 데이터 미리 로드 (성능 최적화)
        from .station_data import STATION_ID_TO_NAME
        self.station_mapping = STATION_ID_TO_NAME

    def _normalize_station_name(self, station_name: str) -> str:
        """역 이름을 정규화합니다.
        
        ✨ 개선사항: 정교한 역 이름 정규화 함수 분리
        
        Args:
            station_name: 원본 역 이름
            
        Returns:
            str: 정규화된 역 이름
        """
        if not station_name:
            return ""
        
        # 1. 공백 제거
        normalized = station_name.strip()
        
        # 2. "역" 제거 (끝에 있는 경우만)
        if normalized.endswith("역"):
            normalized = normalized[:-1]
        
        # 3. 특수 문자 및 괄호 내용 제거 (예: "강남(신분당선)", "홍대입구(2호선)")
        normalized = re.sub(r'\([^)]*\)', '', normalized)
        
        # 4. 연속된 공백을 하나로 변경
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # 5. 다시 공백 제거
        normalized = normalized.strip()
        
        self.logger.debug(f"역 이름 정규화: '{station_name}' → '{normalized}'")
        return normalized

    def _create_error_response(self, message: str, error_detail: Optional[str] = None) -> Dict:
        """에러 응답을 생성합니다."""
        if error_detail:
            self.logger.error(f"SubwayService 오류: {message} - {error_detail}")
        else:
            self.logger.error(f"SubwayService 오류: {message}")
        
        return {
            "status": "error",
            "message": message,
            "arrivals": []
        }

    def get_realtime_arrival(self, station_name: str, target_lines: Optional[List[str]] = None) -> Dict:
        """지하철 실시간 도착정보를 조회합니다.
        
        ✨ 개선사항: 향상된 예외 처리와 로깅
        """
        self.logger.info(f"실시간 도착정보 조회 시작 - 역: {station_name}, 노선: {target_lines}")
        
        # 🔧 역 이름 정규화 (개선된 정규화 함수 사용)
        clean_station_name = self._normalize_station_name(station_name)
        url = f"{self.base_url}/{self.api_key}/json/realtimeStationArrival/0/{Config.MAX_ARRIVALS}/{clean_station_name}"
        
        try:
            # 성능 최적화: 3초 타임아웃 설정
            self.logger.debug(f"API 호출 시작: {url}")
            response = self.session.get(url, timeout=3)
            response.raise_for_status()
            
            data = response.json()
            self.logger.debug(f"API 응답 수신 성공 - 역: {station_name}")
            
            # API 응답 확인
            if "realtimeArrivalList" not in data:
                return self._create_error_response(f"{station_name}에 대한 실시간 정보가 없습니다.")
            
            arrival_list = data["realtimeArrivalList"]
            
            if not arrival_list:
                self.logger.info(f"도착 예정 열차 없음 - 역: {station_name}")
                return {
                    "status": "success",
                    "station": station_name,
                    "message": f"{station_name}에 현재 도착 예정인 열차가 없습니다.",
                    "arrivals": []
                }
            
            # 🔄 데이터 처리를 SubwayDataProcessor에 위임
            processed_arrivals = []
            
            for arrival in arrival_list:
                try:
                    processed_arrival = self.data_processor.process_single_arrival(arrival, station_name)
                    
                    # 🚇 종점인 열차는 제외
                    if not processed_arrival["is_terminal"]:
                        processed_arrivals.append(processed_arrival)
                        
                except Exception as e:
                    self.logger.warning(f"개별 도착 정보 처리 중 오류 발생: {e} - 데이터: {arrival}")
                    continue  # 개별 오류는 건너뛰고 계속 진행
            
            # 특정 노선 필터링 (사용자가 노선을 지정한 경우)
            if target_lines:
                original_count = len(processed_arrivals)
                processed_arrivals = self.data_processor.filter_arrivals_by_lines(processed_arrivals, target_lines)
                self.logger.info(f"노선 필터링 완료 - 원본: {original_count}개, 필터링 후: {len(processed_arrivals)}개")
            
            self.logger.info(f"실시간 도착정보 조회 완료 - 역: {station_name}, 결과: {len(processed_arrivals)}개")
            
            return {
                "status": "success",
                "station": station_name,
                "arrivals": processed_arrivals,
                "filtered_by_lines": target_lines if target_lines else []
            }
            
        except requests.exceptions.Timeout:
            return self._create_error_response("지하철 정보 조회 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.", "Timeout")
        except requests.exceptions.ConnectionError:
            return self._create_error_response("지하철 정보 서버에 연결할 수 없습니다. 네트워크를 확인해주세요.", "Connection Error")
        except requests.exceptions.HTTPError as e:
            return self._create_error_response(f"지하철 정보 조회 중 서버 오류가 발생했습니다.", f"HTTP Error: {str(e)}")
        except requests.exceptions.RequestException as e:
            return self._create_error_response(f"지하철 정보를 가져오는 중 오류가 발생했습니다.", str(e))
        except Exception as e:
            return self._create_error_response(f"데이터 처리 중 예기치 않은 오류가 발생했습니다.", str(e))

    def get_multiple_stations_info(self, station_names: List[str]) -> Dict:
        """여러 역의 실시간 도착 정보를 한 번에 조회합니다."""
        results = {}
        
        for station in station_names:
            results[station] = self.get_realtime_arrival(station)
        
        return {
            "stations": results,
            "total_count": len(station_names),
            "success_count": sum(1 for result in results.values() if result["status"] == "success")
        } 