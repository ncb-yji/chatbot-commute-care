from openai import OpenAI
from config import Config
import json
import re
import logging
import time
from .station_data import StationData

class StationParser:
    """지하철 역 이름 파싱 전용 클래스"""

    # OpenAI 클라이언트와 역 데이터를 초기화
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        # 실제 서비스라면 logging 설정
        self.logger = logging.getLogger(__name__)
        # 역 정보 데이터 초기화
        self.station_data = StationData()

    # 사용자 메시지에서 지하철 역 이름을 추출하고 구조화된 정보로 반환
    def parse_station_query(self, user_message: str) -> dict:
        """사용자 메시지에서 지하철 역 이름을 파싱합니다.
        
        ✨ 개선사항: 정확도 향상을 위한 프롬프트 보강
        """

        # few-shot 예시를 system prompt에 포함
        system_prompt = """
        당신은 지하철 정보 파싱 전문가입니다. 
        사용자의 메시지에서 지하철 역 이름을 추출하세요.

        ⚠️ 중요한 금지사항:
        - 일반적인 단어는 역 이름으로 인식하지 마세요: "언제", "어디", "어떻게", "정보", "도착", "시간", "몇시", "가고", "에서", "으로", "까지", "지하철", "전철", "알려", "줘", "주세요", "좀", "빨리", "빠르게", "지금", "현재", "오늘", "내일", "어제"
        - 의문사나 조사는 제외하세요: "어디", "언제", "어떻게", "왜", "무엇", "누구", "에서", "으로", "까지", "에게", "한테", "와", "과", "의", "을", "를", "이", "가", "은", "는"
        - 시간 관련 단어도 제외하세요: "몇시", "시간", "분", "초", "오전", "오후", "새벽", "아침", "점심", "저녁", "밤"

        🎯 특별한 역 이름 인식 규칙:
        - "동대문역사" → "동대문역사문화공원"으로 인식하세요
        - "문화공원" → "동대문역사문화공원"으로 인식하세요
        - "DDP" → "동대문역사문화공원"으로 인식하세요
        - "홍대" → "홍대입구"로 인식하세요
        - "건대" → "건대입구"로 인식하세요
        - "숭실대" → "숭실대입구"로 인식하세요
        - "총신대" → "총신대입구"로 인식하세요
        - "성신여대" → "성신여대입구"로 인식하세요
        - "한성대" → "한성대입구"로 인식하세요
        - "동묘" → "동묘앞"으로 인식하세요
        - "대학로" → "혜화"로 인식하세요
        - "남대문" → "회현"으로 인식하세요

        응답은 반드시 다음 JSON 형식으로 해주세요:
        {
            "stations": ["역이름1", "역이름2"],
            "lines": ["9", "2호선", "1"],
            "query_type": "arrival_info"
        }

        - 역 이름에서 "역"이 있다면 제거하고 응답하세요 (예: "강남역" → "강남")
        - 역 이름에서 "역"이 없으면 그대로 응답하세요 (예: "신목동" → "신목동")
        - 노선 정보가 있으면 추출하세요 (예: "9호선" → "9", "2호선" → "2", "경의선" → "경의선")
        - 첫 번째 역만 추출하세요 (여러 역이 언급되어도 첫 번째만)
        - 역 이름이 없으면 빈 배열을 반환하세요
        - 노선 정보가 없으면 빈 배열을 반환하세요

        예시)
        사용자: 강남역 도착시간 알려줘
        응답:
        {
            "stations": ["강남"],
            "lines": [],
            "query_type": "arrival_info"
        }

        사용자: 당산 9호선
        응답:
        {
            "stations": ["당산"],
            "lines": ["9"],
            "query_type": "arrival_info"
        }

        사용자: 모란 8
        응답:
        {
            "stations": ["모란"],
            "lines": ["8"],
            "query_type": "arrival_info"
        }

        사용자: 정자 수인
        응답:
        {
            "stations": ["정자"],
            "lines": ["수인"],
            "query_type": "arrival_info"
        }

        사용자: 당산 분당
        응답:
        {
            "stations": ["당산"],
            "lines": ["분당"],
            "query_type": "arrival_info"
        }

        사용자: 언제 도착해?
        응답:
        {
            "stations": [],
            "lines": [],
            "query_type": "arrival_info"
        }

        사용자: 지하철 정보 알려줘
        응답:
        {
            "stations": [],
            "lines": [],
            "query_type": "arrival_info"
        }
        """

        response = None
        try:
            # OpenAI API 호출 시간 측정
            openai_start = time.time()
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,  # Config에서 모델 설정 가져오기
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0
            )
            openai_time = time.time() - openai_start
            self.logger.info(f"🤖 OpenAI API 호출 (파싱): {openai_time:.3f}초")
            content = response.choices[0].message.content
            # 프리프로세싱 - JSON 코드블록 제거
            if content:
                cleaned_content = content.strip()
                cleaned_content = cleaned_content.replace("```json", "").replace("```", "")
                result = json.loads(cleaned_content)
                
                # OpenAI 파싱 결과 로그
                self.logger.info(f"🔍 OpenAI 파싱 결과: stations={result.get('stations', [])}, lines={result.get('lines', [])}")
                
                # 파싱된 역 이름들을 검증하고 보강
                validated_result = self._validate_and_enhance_stations(result)
                self.logger.info(f"✅ 검증 후 최종 결과: stations={validated_result.get('stations', [])}, lines={validated_result.get('lines', [])}")
                return validated_result 
            else:
                raise ValueError("응답이 비어 있음")

        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"JSON 파싱 실패: {e}")
            regex_result = self.extract_stations_regex(user_message)
            self.logger.info(f"🔄 정규식 백업 파싱 결과: stations={regex_result.get('stations', [])}, lines={regex_result.get('lines', [])}")
            return {
                "stations": regex_result.get("stations", []),
                "lines": regex_result.get("lines", []),
                "query_type": "arrival_info"
            }
        except Exception as e:
            self.logger.error(f"OpenAI API 오류: {e}")
            regex_result = self.extract_stations_regex(user_message)
            self.logger.info(f"🔄 정규식 백업 파싱 결과: stations={regex_result.get('stations', [])}, lines={regex_result.get('lines', [])}")
            return {
                "stations": regex_result.get("stations", []),
                "lines": regex_result.get("lines", []),
                "query_type": "arrival_info"
            }

    # 정규식을 사용하여 텍스트에서 지하철 역 이름과 노선 정보를 추출 (OpenAI 실패 시 백업)
    def extract_stations_regex(self, text: str) -> dict:
        """정규식을 사용해 역 이름과 노선 정보를 추출합니다.
        
        ✨ 개선사항: 
        - False Positive 방지를 위한 정규식 패턴 개선
        - Config에서 금지어 목록 가져오기
        """
        # Config에서 금지어 목록 가져오기
        forbidden_words = Config.FORBIDDEN_WORDS
        
        # 1. "역"이 포함된 패턴: "강남역", "신목동역" 등
        pattern_with_station = r'([가-힣]{2,}(?:[0-9]*))역'
        matches_with_station = re.findall(pattern_with_station, text)
        
        # 2. "역"이 없는 패턴: 더 엄격한 조건으로 개선
        # 한글 2~4글자 + 앞뒤 경계 조건
        pattern_without_station = r'(?:^|[\s,.!?]|도착|정보|에서|으로|까지|가고|까지|에)([가-힣]{2,4}(?:[0-9]*))(?=[\s,.!?]|도착|정보|에서|으로|까지|가고|$)'
        matches_without_station = re.findall(pattern_without_station, text)
        
        # 결과 합치기
        all_matches = []
        
        # "역"이 포함된 매치를 먼저 추가
        for match in matches_with_station:
            cleaned = match.strip()
            if cleaned and len(cleaned) >= 2 and cleaned not in forbidden_words:
                all_matches.append(cleaned)
        
        # "역"이 없는 매치 추가 (중복 제거 및 금지어 필터링)
        for match in matches_without_station:
            cleaned = match.strip()
            if (cleaned and 
                len(cleaned) >= 2 and 
                cleaned not in forbidden_words and
                not any(cleaned in existing for existing in all_matches)):
                all_matches.append(cleaned)
        
        # 노선 정보 추출 (기존 로직 유지)
        line_patterns = Config.LINE_PATTERNS
        
        extracted_lines = []
        for pattern in line_patterns:
            matches = re.findall(pattern, text)
            extracted_lines.extend(matches)
        
        # 중복 제거 및 결과 반환
        unique_stations = list(set(all_matches))
        unique_lines = list(set(extracted_lines))
        
        return {
            "stations": unique_stations,
            "lines": unique_lines
        }

    def _validate_and_enhance_stations(self, parsed_result: dict) -> dict:
        """파싱된 역 이름들을 검증하고 정규화합니다. (경량화)"""
        stations = parsed_result.get("stations", [])
        target_lines = parsed_result.get("lines", [])
        
        # 노선명 정규화
        normalized_target_lines = []
        for line in target_lines:
            normalized_line = self._normalize_line_name(line)
            if normalized_line:
                normalized_target_lines.append(normalized_line)
        
        # 역 이름 정규화 (첫 번째 역만 처리)
        validated_stations = []
        
        if stations:
            station = stations[0]  # 첫 번째 역만 처리 (경량화)
            normalized_station = station.strip()

            # 역 정보 가져오기 및 이름 보정
            station_info = self.station_data.get_station_info(normalized_station)

            if station_info["line_count"] == 0 and not normalized_station.endswith("역"):
                station_with_station = normalized_station + "역"
                station_info = self.station_data.get_station_info(station_with_station)
                if station_info["line_count"] > 0:
                    normalized_station = station_with_station

            if station_info["line_count"] == 0 and normalized_station.endswith("역"):
                station_without_station = normalized_station[:-1]
                station_info = self.station_data.get_station_info(station_without_station)
                if station_info["line_count"] > 0:
                    normalized_station = station_without_station

            validated_stations.append(normalized_station)

        return {
            "stations": validated_stations,
            "lines": normalized_target_lines,
            "query_type": parsed_result.get("query_type", "arrival_info")
        }


    # 경량화: 복잡한 역 분석 로직 제거됨

    def _normalize_line_name(self, input_line: str) -> str:
        """사용자 입력 노선명을 실제 노선명으로 정규화합니다."""
        if not input_line:
            return ""
        
        # 입력값 정리
        clean_input = input_line.strip()
        
        # StationData에서 실제 노선명 목록 가져오기
        valid_line_names = self.station_data.get_valid_line_names()
        
        # 1. 정확한 매칭 시도
        if clean_input in valid_line_names:
            return clean_input
        
        # 2. 숫자만 입력된 경우 (예: "1", "2", "9")
        if clean_input.isdigit():
            target_line = f"{clean_input}호선"
            if target_line in valid_line_names:
                return target_line
        
        # 3. 부분 매칭 시도 (예: "수인분당", "경의중앙", "공항")
        for line_name in valid_line_names:
            # "수인분당" -> "수인분당선" 매칭
            if clean_input in line_name or line_name.replace("선", "").replace("호선", "") == clean_input:
                return line_name
        
        # 4. 특별 케이스 처리
        special_cases = {
            "수인분당": "수인분당선",
            "경의중앙": "경의중앙선", 
            "공항": "공항철도",
            "우이신설": "우이신설선",
            "신분당": "신분당선",
            "중앙": "중앙선",
            "경춘": "경춘선",
            "신림": "신림선",
            "인천1": "인천1호선",
            "인천2": "인천2호선",
            "GTX": "GTX-A"
        }
        
        if clean_input in special_cases:
            return special_cases[clean_input]
        
        # 5. 호선이 붙은 경우 처리 (예: "1호선", "2호선")
        if clean_input.endswith("호선"):
            if clean_input in valid_line_names:
                return clean_input
        
        # 6. 매칭되지 않은 경우 원본 반환
        return clean_input
