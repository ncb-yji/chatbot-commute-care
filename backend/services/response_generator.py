from openai import OpenAI
from config import Config
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from .station_data import StationData

class FastResponseGenerator:
    """간단한 템플릿 기반 응답 생성기 (fallback용)"""
    
    def generate_response(self, user_query: str, subway_data: dict, parsed_data: Optional[dict] = None) -> str:
        """템플릿 기반으로 빠른 응답 생성"""
        try:
            if subway_data.get("status") == "error":
                return f"😅 {subway_data.get('message', '정보를 가져올 수 없습니다.')}"
            
            arrivals = subway_data.get("arrivals", [])
            station_name = subway_data.get("station", "해당 역")
            
            if not arrivals:
                # 운행 정보가 없는 경우 사용자 친화적 메시지
                return f"😅 {station_name}역에 현재 운행 정보가 없습니다.\n\n운행 시간이 지났거나 일시적으로 정보를 가져올 수 없어요.\n잠시 후 다시 시도해주세요! 🚇"
            
            response_lines = [f"🚇 {station_name}역 실시간 도착정보"]
            
            # 최대 4개 열차 정보만 표시
            for arrival in arrivals[:4]:
                line_name = arrival.get("line_name", "")
                destination = arrival.get("destination", "")
                arrival_time = arrival.get("arrival_time_formatted", "")
                remaining_time = arrival.get("remaining_time_formatted", "")
                updn_line = arrival.get("updn_line", "")
                train_type = arrival.get("train_type", "")
                
                train_info = f"📍 {line_name} {destination}행"
                if updn_line == "0":
                    train_info += " (상행)"
                elif updn_line == "1":
                    train_info += " (하행)"
                
                if train_type == "막차":
                    train_info += " 🚨"
                
                response_lines.append(train_info)
                response_lines.append(f"🕐 {arrival_time} ({remaining_time})")
                response_lines.append("")
            
            response_lines.append("실시간 정보 - 서울교통공사 제공")
            return "\n".join(response_lines)
            
        except Exception as e:
            return "😅 응답을 생성하는 중 오류가 발생했습니다."

class ResponseGenerator:
    """응답 생성 전용 클래스

    지하철 실시간 데이터를 사용자 친화적인 자연어로 변환하는 역할을 담당합니다.
    OpenAI GPT를 활용하여 구조화된 데이터를 대화형 응답으로 변환합니다.
    
    ✨ 개선사항:
    - OpenAI 호출 실패 시 FastResponseGenerator로 fallback
    """

    def __init__(self, fallback_generator: Optional[FastResponseGenerator] = None):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.logger = logging.getLogger(__name__)
        # 역 정보 데이터 초기화
        self.station_data = StationData()
        # 프롬프트 템플릿 캐싱
        self._system_prompt_template = self._build_system_prompt_template()
        # fallback 생성기 (의존성 주입 지원)
        self.fallback_generator = fallback_generator or FastResponseGenerator()

    def _prepare_system_prompt(
        self, user_query: str, parsed_data: Optional[Dict[str, Any]]
    ) -> str:
        """사용자 쿼리와 분석 데이터를 기반으로 시스템 프롬프트 준비"""

        # 양방향 정보 요청 감지
        bidirectional_keywords = Config.BIDIRECTIONAL_KEYWORDS
        show_bidirectional = any(
            keyword in user_query for keyword in bidirectional_keywords
        )

        # 추가 지침 생성
        enhanced_info = ""
        if parsed_data and "enhanced_stations" in parsed_data:
            enhanced_info = self._generate_enhanced_instructions(parsed_data)

        # 방향 지침
        direction_instruction = (
            "모든 방향(상행, 하행)의 열차 정보를 보여주세요."
            if show_bidirectional
            else "한 방향의 열차 정보만 보여주세요. 빠른 열차를 우선 안내하세요."
        )

        # 현재 시간 정보 추가
        current_time = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")

        return f"""
{self._system_prompt_template}

## 추가 컨텍스트
- 현재 시간: {current_time}
- 방향 지침: {direction_instruction}

{enhanced_info}
        """.strip()

    def _prepare_data_message(self, subway_data: Dict[str, Any]) -> str:
        """지하철 데이터를 JSON 형태로 정리"""
        print("subway_data: ", subway_data)
        return f"""
            실시간 지하철 도착정보 데이터:
            {json.dumps(subway_data, ensure_ascii=False, indent=2)}
        """.strip()

    def _build_system_prompt_template(self) -> str:
        """시스템 프롬프트 템플릿 생성 (캐싱용)"""
        return """
        당신은 "서울 지하철 실시간 도착정보 챗봇"이며, 사용자의 요청에 따라 JSON 기반 데이터를 정해진 양식으로 변환해 출력하는 것이 역할입니다. 
        응답은 항상 같은 구조로 출력되어야 하며, 일관성을 유지해야 합니다.

        ## 절대 하지 말아야 할 것:
        - JSON에 존재하지 않는 필드를 추측하거나 생성하지 마세요.
        - HTML 태그, 마크다운 링크, 표 등을 사용하지 마세요.
        - 같은 열차를 중복해서 출력하지 마세요.

        ## JSON 데이터 설명

        {
        "station": "역 이름",
        "status": "API 응답 상태",
        "message": "메시지",
            "arrivals": [
            {
            "subway_id": "노선 ID",
            "line_name": "노선명",
            "station": "역 이름",
            "direction": "열차 방향 (종착역 - 경유지)",
            "destination": "종착역",
            "direction_destination": "direction에서 추출한 종착역",
            "station_id": "현재역 ID",
            "previous_station_id": "이전역 ID",
            "next_station_id": "다음역 ID",
            "previous_station": "이전역 이름",
            "next_station": "다음역 이름",
            "arrival_message": "도착 메시지",
            "arrival_detail": "현재 위치",
            "arrival_time": "남은 시간 (초)",
            "arrival_time_formatted": "실제 도착 시각 (오전/오후 형태)",
            "remaining_time_formatted": "남은 시간 (X분 Y초 형태)",
            "arrival_time_text": "도착 시간 텍스트",
            "time_reference": "시간 기준점 (HH:MM:SS)",
            "time_reference_formatted": "시간 기준점 표시용 (HH:MM:SS 기준)",
            "train_type": "일반 / 급행 / ITX / 막차",
            "is_express": true/false,
            "is_terminal": true/false,
            "updn_line": "상행/하행",
            "arrival_code": "상태 코드"
            }
        ]
        }

        ---

        ## 응답 규칙
        0. arrivals 배열이 비어있는 경우:
        - "😅 {station}역에 현재 운행 정보가 없습니다.\n\n운행 시간이 지났거나 일시적으로 정보를 가져올 수 없어요.\n잠시 후 다시 시도해주세요! 🚇" 형태로 응답
        - JSON 데이터를 그대로 출력하지 말고 사용자가 이해하기 쉬운 메시지로 변환
        
        1. 사용자 질문에 역 이름이 1개일 경우:
        - 해당 역의 모든 도착 정보를 출력 (최대 8개까지)
        - 포함 정보: 노선명, 종착역, 열차 종류, 상/하행, 도착 시각, 남은 시간, 현재 위치
        - 막차일 경우 🚨 표시 (train_type='막차')
        - (급행), (ITX) 여부 표시
        - 같은 노선끼리 묶어서 표시하고 그다음에는 상행하행끼리 묶어서 표시하기
        - 필수 정보가 누락된 열차도 가능한 한 포함하여 출력
        - 도착 시간이 "정보 없음"인 경우에도 노선명과 방향 정보는 출력
            # 예시 1 : 당산 (여러 호선일 경우)
                🚇 당산역 실시간 도착정보
                ---------------------------------------------
                📍 9호선 당산
                김포공항행 급행 (하행)
                - 이 역의 다음역은 '선유도' 입니다.
                - 🕐 도착예정: 오후 10:06 (1분 25초 후)

                🚨 개화행 (하행)
                - 이 역의 다음역은 '선유도' 입니다.
                - 🕐 도착예정: 오후 10:12 (8분 15초 후)
                ---------------------------------------------
                📍 2호선 당산
                🚨 성수행 (외선)
                - 이 역의 다음역은 '영등포구청' 입니다.
                - 🕐 도착예정: 오후 10:08 (4분 후)

                성수행 (외선)
                - 이 역의 다음역은 '영등포구청' 입니다.
                - 🕐 도착예정: 오후 10:12 (7분 50초 후)
                ---------------------------------------------
                2025/7/12 오후 10:04 기준 서울교통공사 제공 

            # 예시 2 : 당산 2
            🚇 당산역 실시간 도착정보
            ---------------------------------------------
               📍 2호선 당산
                성수행 (외선)
                - 이 역의 다음역은 '영등포구청' 입니다.
                - 🕐 도착예정: 오후 10:08 (6분 후)

                성수행 (외선)
                - 이 역의 다음역은 '영등포구청' 입니다.
                - 🕐 도착예정: 오후 10:11 (9분 30초 후)
                ---------------------------------------------
                성수행 (내선)
                - 이 역의 다음역은 '합정' 입니다.
                - 🕐 도착예정: 오후 10:04 (2분 30초 후)

                성수행 (내선)
                - 이 역의 다음역은 '합정' 입니다.
                - 🕐 도착예정: 오후 10:14 (11분 50초 후)
                ---------------------------------------------
                2025/7/12 오후 10:02 기준 서울교통공사 제공
        
        2. 사용자 질문에 역 이름이 2개일 경우:
        - "(출발역 → 도착역) 경로를 탐색합니다." 라는 제목 추가
        - 각 역의 도착 정보를 방면당 최대 2개까지 출력
        - 출발역 기준으로 도착역을 향하는 방향의 열차만 안내
        - 같은 호선은 한 블럭으로 처리하되, 노선 정보로 분리하여 출력

        3. 사용자가 역과 노선을 지정했을 경우:
        - 해당하는 역의 해당 노선의 정보만을 방면당 최대 4개까지 출력
 

        4. 출력 형식
        🚇 {station}역 실시간 도착정보
        ---------------------------------------------
        📍 {line_name} {station}
        {막차표시}{direction_destination}행 {열차유형} ({updn_line})
        - 이 역의 다음역은 '{next_station}' 입니다.
        - 🕐 도착예정: {arrival_time_formatted}  ({arrival_time_text}) 
        ---------------------------------------------
        실시간 정보 - 서울교통공사 제공
        
        ## 열차 유형 표시 규칙:
        - train_type이 "막차"인 경우: 🚨 표시만 하고 "막차" 텍스트는 생략 (예: "🚨홍대입구행 (상행)")
        - train_type이 "급행"인 경우: "급행" 텍스트 표시 (예: "홍대입구행 급행 (상행)")
        - train_type이 "ITX"인 경우: "ITX" 텍스트 표시 (예: "홍대입구행 ITX (상행)")
        - train_type이 "일반"인 경우: 아무것도 표시하지 않음 (예: "홍대입구행 (상행)")
        - train_type이 빈 문자열인 경우: 아무것도 표시하지 않음 (예: "홍대입구행 (상행)")
        
        ## 중요: 절대 하지 말 것
        - line_name을 train_type 위치에 표시하지 마세요
        - "막차" 텍스트와 🚨를 동시에 표시하지 마세요
        - 불필요한 텍스트를 추가하지 마세요

        4. 출력 마지막에 아래 문장을 추가 (시간 기준점 포함)
        {time_reference_formatted} 기준 서울교통공사 제공
        
        5. 모든 출력은 이모지 + 텍스트만 사용 (HTML 금지)
        
        6. train_type이 '막차'일 경우에만 🚨 표시
        
        7. 🚇 종점 처리 규칙:
        - 종점에 도착한 열차(destination과 next_station이 같은 경우)는 데이터에서 제외됩니다.
        - 따라서 응답에는 운행 중인 열차만 표시됩니다.
        ---

        ## 변수명과 JSON 필드 매핑
        - {역이름} = station
        - {노선명} = line_name
        - {종착역} = destination (또는 direction_destination)
        - {상행하행} = updn_line
        - {도착시각} = arrival_time_formatted (예: "오후 4:33")
        - {남은시간} = remaining_time_formatted (예: "3분 0초")
        - {다음역} = next_station (역 이름)
        - {이전역} = previous_station (역 이름)
        - {다음역ID} = next_station_id (statnTid 필드)
        - {이전역ID} = previous_station_id (statnFid 필드)
        - {현재역ID} = station_id (statnId 필드)
        - {현재위치} = arrival_detail (참고용)
        - {열차종류} = train_type (일반이면 생략 가능)
        - 막차인 경우: train_type이 '막차'면 🚨 추가
        """.strip()



    def _generate_enhanced_instructions(self, parsed_data: Dict[str, Any]) -> str:
        """파싱된 데이터를 기반으로 추가 지침 생성"""
        enhanced_stations = parsed_data.get("enhanced_stations", [])
        analysis = parsed_data.get("analysis", {})

        instructions = []

        # 환승역 정보 추가
        transfer_stations = [
            s for s in enhanced_stations if s.get("is_transfer", False)
        ]
        if transfer_stations:
            transfer_names = [s["name"] for s in transfer_stations]
            instructions.append(
                f"🔄 환승역 정보: {', '.join(transfer_names)}역은 환승역입니다."
            )

        # 공통 노선 정보 추가
        common_lines = analysis.get("common_lines", [])
        if len(enhanced_stations) == 2 and common_lines:
            instructions.append(
                f"🚇 직통 노선: {', '.join(common_lines)}로 환승 없이 이동 가능합니다."
            )
        elif len(enhanced_stations) == 2 and not common_lines:
            instructions.append("🔄 환승 필요: 두 역 사이에는 환승이 필요합니다.")

        # 노선 정보 상세 추가
        for station in enhanced_stations:
            if station.get("lines"):
                line_info = [line["line_name"] for line in station["lines"]]
                instructions.append(
                    f"📍 {station['name']}역 운행 노선: {', '.join(line_info)}"
                )

        if instructions:
            return "## 추가 정보\n" + "\n".join(instructions)

        return ""

    def _call_openai_api(self, system_prompt: str, data_message: str) -> str:
        """OpenAI API를 호출하여 응답을 생성합니다."""
        response = self.client.chat.completions.create(
            model=Config.OPENAI_MODEL,  # Config에서 모델 설정 가져오기
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data_message},
            ],
            temperature=0,
            max_tokens=1000,
            presence_penalty=-2,
            frequency_penalty=0,
            top_p=0.9,
        )
        
        content = response.choices[0].message.content
        return content if content else ""

    def _post_process_response(self, content: str) -> str:
        """OpenAI 응답을 후처리합니다."""
        return content if content else "죄송합니다. 응답을 생성할 수 없습니다. 🙏"

    def generate_response(
        self,
        user_query: str,
        subway_data: Dict[str, Any],
        parsed_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        지하철 데이터를 자연어로 변환하여 사용자에게 친근하게 전달합니다.
        
        ✨ 개선사항: 
        - OpenAI 호출 실패 시 FastResponseGenerator로 fallback
        - 메서드 분리로 가독성 향상

        Args:
            user_query: 사용자 질문
            subway_data: 지하철 실시간 데이터
            parsed_data: StationParser에서 분석된 역 정보 (선택사항)

        Returns:
            str: 자연어로 변환된 응답
        """
        try:
            # 1. 시스템 프롬프트 준비
            system_prompt = self._prepare_system_prompt(user_query, parsed_data)

            # 2. 데이터 메시지 준비
            data_message = self._prepare_data_message(subway_data)

            # 3. OpenAI API 호출
            content = self._call_openai_api(system_prompt, data_message)

            # 4. 응답 후처리
            return self._post_process_response(content)

        except Exception as e:
            self.logger.error(f"OpenAI API 오류: {e}")
            # 🔄 fallback: OpenAI 호출 실패 시 FastResponseGenerator 사용
            self.logger.info("OpenAI 호출 실패로 인해 fallback 생성기를 사용합니다.")
            return self.fallback_generator.generate_response(user_query, subway_data, parsed_data)
