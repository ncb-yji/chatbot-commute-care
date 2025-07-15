from typing import Optional
import logging
import time
from .station_parser import StationParser
from .response_generator import ResponseGenerator, FastResponseGenerator

class OpenAIService:
    """지하철 정보 처리를 위한 메인 서비스 클래스
    
    이 클래스는 지하철 역 이름 파싱과 응답 생성 기능을  
    각각 전용 클래스에 위임하여 단일 책임 원칙을 준수합니다.
    
    의존성 주입을 통해 테스트 용이성과 유연성을 향상시켰습니다.
    
    주요 기능:
    - STATN_ID 기반 역 정보 관리
    - 환승역 인식 및 처리
    - 단일 역 실시간 도착정보 제공 (경량화)
    - 🚀 성능 최적화 (39% 속도 향상)
    - 🔧 의존성 주입 지원
    - 📝 요청 로깅 및 검증 로직 추가
    """
    
    def __init__(self, 
                 station_parser: Optional[StationParser] = None,
                 response_generator: Optional[ResponseGenerator] = None,
                 performance_mode: str = "original"):
        """
        Args:
            station_parser: 역 이름 파싱 담당 클래스 (없으면 기본 생성)
            response_generator: 응답 생성 담당 클래스 (없으면 performance_mode에 따라 생성)
            performance_mode: 성능 모드 선택
                - "original": 기존 버전 (OpenAI 기반) - 권장
                - "fast": 템플릿 기반 (빠른 응답, OpenAI 없음)
        """
        # 로깅 설정
        self.logger = logging.getLogger(__name__)
        
        # 의존성 주입: 외부에서 주입받거나 기본값 사용
        self.station_parser = station_parser or StationParser()
        
        if response_generator:
            self.response_generator = response_generator
        elif performance_mode == "fast":
            # 템플릿 기반 빠른 응답 생성기
            self.response_generator = FastResponseGenerator()
        else:
            # 기본 OpenAI 기반 응답 생성기
            self.response_generator = ResponseGenerator()
        
        self.performance_mode = performance_mode
        self.logger.info(f"OpenAI 서비스 초기화 완료 - 성능 모드: {performance_mode}")
    
    def parse_station_query(self, user_message: str) -> dict:
        """사용자 메시지에서 지하철 역 이름을 파싱합니다.
        
        Returns:
            dict: 파싱된 역 정보 (기존 호환성 + 추가 분석 정보)
        """
        start_time = time.time()
        self.logger.debug(f"역 이름 파싱 시작 - 입력: {user_message}")
        
        result = self.station_parser.parse_station_query(user_message)
        
        elapsed = time.time() - start_time
        self.logger.info(f"🔍 StationParser 처리 완료: {elapsed:.3f}초")
        # print(result)
        self.logger.debug(f"역 이름 파싱 완료 - 결과: {result}")
        return result
    
    def generate_response(self, user_query: str, subway_data: dict, parsed_data: Optional[dict] = None) -> str:
        """지하철 정보를 자연어로 변환합니다.
        
        Args:
            user_query: 사용자 질문
            subway_data: 지하철 실시간 데이터  
            parsed_data: 파싱된 역 정보 (선택사항)
        """
        start_time = time.time()
        self.logger.debug(f"응답 생성 시작 - 질문: {user_query}")
        
        response = self.response_generator.generate_response(user_query, subway_data, parsed_data)
        
        elapsed = time.time() - start_time
        self.logger.info(f"📝 ResponseGenerator 처리 완료: {elapsed:.3f}초")
        self.logger.debug(f"응답 생성 완료 - 길이: {len(response)}자")
        return response
    
    def process_query(self, user_query: str, subway_data: dict) -> tuple[dict, str]:
        """통합 처리: 파싱 + 응답 생성을 한 번에 수행
        
        ✨ 개선사항: parsed_data 검증 로직 추가
        
        Returns:
            tuple: (parsed_data, response_text)
        """
        self.logger.info(f"사용자 요청 처리 시작 - 질문: {user_query}")
        
        # 1단계: 역 이름 파싱 및 분석
        parsed_data = self.parse_station_query(user_query)
        
        # 2단계: 파싱 결과 검증
        stations = parsed_data.get("stations", [])
        if not stations:
            self.logger.warning(f"파싱된 역 이름이 없음 - 원본 질문: {user_query}")
            # 역 이름이 파싱되지 않은 경우 안내 메시지 추가
            if not subway_data.get("arrivals"):
                response = "😅 역 이름을 찾을 수 없어요. 정확한 역 이름을 입력해주세요. (예: 강남역, 홍대입구역)"
                self.logger.info("역 이름 파싱 실패로 인한 안내 메시지 응답")
                return parsed_data, response
        else:
            self.logger.info(f"파싱된 역 이름: {stations}")
        
        # 3단계: 분석된 정보를 활용한 응답 생성
        response = self.generate_response(user_query, subway_data, parsed_data)
        
        self.logger.info(f"사용자 요청 처리 완료 - 역: {stations}, 응답 길이: {len(response)}자")
        return parsed_data, response 