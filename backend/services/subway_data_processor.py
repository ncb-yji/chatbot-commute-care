import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from config import Config

class SubwayDataProcessor:
    """지하철 API 응답 데이터를 가공하는 전용 클래스
    
    지하철 실시간 데이터의 파싱, 시간 계산, 종점 처리 등
    순수한 데이터 변환 로직만을 담당합니다.
    """

    def __init__(self):
        # 노선 매핑
        self.subway_lines = {
            "1001": "1호선", "1002": "2호선", "1003": "3호선", "1004": "4호선",
            "1005": "5호선", "1006": "6호선", "1007": "7호선", "1008": "8호선",
            "1009": "9호선", "1061": "중앙선", "1063": "경의중앙선", "1065": "공항철도",
            "1067": "경춘선", "1075": "수인분당선", "1077": "신분당선", "1092": "우이신설선",
            "1093": "서해선", "1081": "경강선", "1032": "GTX-A"
        }
        
        # 노선 줄임말 매핑
        self.line_shortcuts = {
            # 숫자 노선
            "1": "1호선", "2": "2호선", "3": "3호선", "4": "4호선",
            "5": "5호선", "6": "6호선", "7": "7호선", "8": "8호선", "9": "9호선",
            
            # 특수 노선 줄임말
            "중앙": "중앙선",
            "경의": "경의중앙선", "경의중앙": "경의중앙선",
            "공항": "공항철도", "공항철도": "공항철도",
            "경춘": "경춘선",
            "수인": "수인분당선", "분당": "수인분당선", "수인분당": "수인분당선",
            "신분당": "신분당선",
            "우이": "우이신설선", "신설": "우이신설선", "우이신설": "우이신설선",
            "서해": "서해선",
            "경강": "경강선",
            "GTX": "GTX-A", "gtx": "GTX-A", "GTX-A": "GTX-A"
        }

    def parse_arrival_time_from_seconds(self, seconds_str: str) -> int:
        """초 단위 도착시간을 파싱합니다."""
        try:
            return int(seconds_str)
        except (ValueError, TypeError):
            return -1

    def parse_arrival_time_from_message(self, arrival_msg: str) -> int:
        """도착 메시지에서 시간을 추출합니다."""
        if not arrival_msg:
            return -1
        
        # "X분 Y초 후 도착" 형태 파싱
        if "분" in arrival_msg and "초" in arrival_msg:
            match = re.search(r'(\d+)분\s*(\d+)초', arrival_msg)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                return minutes * 60 + seconds
        
        # "X분 후 도착" 형태 파싱
        elif "분" in arrival_msg:
            match = re.search(r'(\d+)분', arrival_msg)
            if match:
                minutes = int(match.group(1))
                return minutes * 60
        
        # "곧 도착" 등의 경우
        elif "곧" in arrival_msg or "잠시" in arrival_msg:
            return 30  # 30초로 가정
        
        # "도착" 또는 "출발" 등의 경우
        elif "도착" in arrival_msg or "출발" in arrival_msg or "진입" in arrival_msg:
            return 0
        
        return -1  # 파싱 실패

    def get_base_time(self, recptn_dt: Optional[str] = None) -> datetime:
        """기준 시간을 가져옵니다 (recptnDt 또는 현재 시간).
        
        ✨ 개선사항: datetime.strptime 실패 시 fallback 처리 추가
        """
        if recptn_dt:
            try:
                # recptnDt 형식: "20250109105500" (YYYYMMDDHHMMSS)
                return datetime.strptime(recptn_dt, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError) as e:
                # recptnDt 파싱 실패시 현재 시간 사용
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"recptnDt 파싱 실패 ({recptn_dt}): {e} - 현재 시간 사용")
                return datetime.now()
        else:
            return datetime.now()

    def format_time_reference(self, base_time: datetime) -> tuple[str, str]:
        """시간 기준점을 포맷팅합니다."""
        time_reference = base_time.strftime("%H:%M:%S")
        
        # 사용자 친화적인 형식으로 변환: [2025/7/9 오전 10:55] 기준
        year = base_time.year
        month = base_time.month
        day = base_time.day
        ampm = '오전' if base_time.hour < 12 else '오후'
        hour12 = base_time.hour if base_time.hour <= 12 else base_time.hour - 12
        if hour12 == 0:
            hour12 = 12
        minute = base_time.minute
        time_reference_formatted = f"[{year}/{month}/{day} {ampm} {hour12}:{minute:02d}] 기준"
        
        return time_reference, time_reference_formatted

    def create_time_info_dict(self, arrival_time_formatted: str, remaining_time_formatted: str, 
                              arrival_time_text: str, time_reference: str, time_reference_formatted: str) -> Dict:
        """시간 정보 딕셔너리를 생성합니다."""
        return {
            "arrival_time_formatted": arrival_time_formatted,
            "remaining_time_formatted": remaining_time_formatted,
            "arrival_time_text": arrival_time_text,
            "time_reference": time_reference,
            "time_reference_formatted": time_reference_formatted
        }

    def handle_zero_second_arrival(self, arrival_msg: str, time_reference: str, time_reference_formatted: str) -> Dict:
        """0초 도착 시간 특별 처리를 합니다."""
        current_time = datetime.now()
        current_time_formatted = self.format_korean_time(current_time)
        
        if "진입" in arrival_msg:
            return self.create_time_info_dict(current_time_formatted, "진입 중", "진입 중", time_reference, time_reference_formatted)
        elif "출발" in arrival_msg:
            return self.create_time_info_dict(current_time_formatted, "출발", "출발", time_reference, time_reference_formatted)
        elif "도착" in arrival_msg:
            return self.create_time_info_dict(current_time_formatted, "도착", "도착", time_reference, time_reference_formatted)
        else:
            return self.create_time_info_dict(current_time_formatted, "0초", "곧 도착", time_reference, time_reference_formatted)

    def format_korean_time(self, arrival_datetime: datetime) -> str:
        """한국어 시간 형식으로 포맷팅합니다."""
        time_str = arrival_datetime.strftime("%p %I:%M").replace("AM", "오전").replace("PM", "오후")
        # 한국어 시간 형식에 맞게 앞의 0 제거 (예: "오전 01:30" -> "오전 1:30")
        return time_str.replace(" 0", " ")

    def format_remaining_time(self, arrival_time_seconds: int) -> tuple[str, str]:
        """남은 시간을 포맷팅합니다."""
        if arrival_time_seconds < 60:
            remaining_time_formatted = f"{arrival_time_seconds}초"
            arrival_time_text = f"{arrival_time_seconds}초 후"
        else:
            minutes = arrival_time_seconds // 60
            seconds = arrival_time_seconds % 60
            if seconds > 0:
                remaining_time_formatted = f"{minutes}분 {seconds}초"
                arrival_time_text = f"{minutes}분 {seconds}초 후"
            else:
                remaining_time_formatted = f"{minutes}분"
                arrival_time_text = f"{minutes}분 후"
        
        return remaining_time_formatted, arrival_time_text

    def calculate_time_info(self, arrival_time_seconds: int, arrival_msg: str, recptn_dt: Optional[str] = None) -> Dict:
        """도착 시간 정보를 계산합니다."""
        base_time = self.get_base_time(recptn_dt)
        current_time = datetime.now()  # 현재 시간
        
        # time_reference_formatted는 현재 시간 기준으로 생성
        time_reference, time_reference_formatted = self.format_time_reference(current_time)

        # 🔧 0초 특별 처리 (이미 도착/진입/출발한 열차)
        if arrival_time_seconds == 0:
            return self.handle_zero_second_arrival(arrival_msg, time_reference, time_reference_formatted)
        
        # 도착 시간이 유효한 경우 (1초 이상)
        if arrival_time_seconds > 0:
            # 실제 도착 시각 계산 (API 응답 시간 기준)
            arrival_datetime = base_time + timedelta(seconds=arrival_time_seconds)
            arrival_time_formatted = self.format_korean_time(arrival_datetime)
            
            # 현재 시간 기준으로 실제 남은 시간 계산
            time_diff = arrival_datetime - current_time
            actual_remaining_seconds = int(time_diff.total_seconds())
            
            # 남은 시간이 음수인 경우 (이미 지난 시간) 처리
            if actual_remaining_seconds <= 0:
                remaining_time_formatted = "곧 도착"
                arrival_time_text = "곧 도착"
            else:
                # 실제 남은 시간으로 포맷팅
                remaining_time_formatted, arrival_time_text = self.format_remaining_time(actual_remaining_seconds)
        else:
            # 도착 시간을 파싱할 수 없는 경우 원본 메시지 사용
            arrival_time_formatted = "정보 없음"
            remaining_time_formatted = "정보 없음"
            arrival_time_text = arrival_msg if arrival_msg else "정보 없음"
        
        return self.create_time_info_dict(arrival_time_formatted, remaining_time_formatted, 
                                         arrival_time_text, time_reference, time_reference_formatted)

    def extract_destination_from_direction(self, direction: str) -> str:
        """direction 필드에서 종착역명을 추출합니다."""
        if not direction:
            return ""
        
        # "을지로입구방면" -> "을지로입구"
        if direction.endswith("방면"):
            return direction[:-2]  # 마지막 2글자 "방면" 제거
        
        # "종로3가 방향" -> "종로3가" 
        if " 방향" in direction:
            return direction.replace(" 방향", "")
        
        # 기타 패턴들
        direction = direction.replace("행", "").replace("방면", "").replace("방향", "")
        
        return direction.strip()

    def extract_line_number_from_subway_id(self, subway_id: str) -> str:
        """subway_id에서 노선 번호를 추출합니다 (레거시 지원용)."""
        # subway_id를 노선 번호로 변환하는 매핑 (숫자 노선만)
        line_mapping = {
            "1001": "1", "1002": "2", "1003": "3", "1004": "4",
            "1005": "5", "1006": "6", "1007": "7", "1008": "8", 
            "1009": "9"
        }
        return line_mapping.get(subway_id, "")

    def parse_train_line_info(self, train_line_nm: str) -> dict:
        """trainLineNm에서 행선지, 다음역, 열차유형을 파싱합니다.
        
        Args:
            train_line_nm: "중앙보훈병원행 - 국회의사당방면 (급행)" 형태의 문자열
            
        Returns:
            dict: {
                "destination": "중앙보훈병원",
                "next_station": "국회의사당", 
                "train_type_info": "급행"
            }
        """
        if not train_line_nm:
            return {
                "destination": "",
                "next_station": "",
                "train_type_info": ""
            }
        
        # 기본값 설정
        destination = ""
        next_station = ""
        train_type_info = ""
        
        # 괄호 안의 열차 유형 정보 추출 (급행, 일반 등) 
        # 괄호 안의 내용 추출
        bracket_match = re.search(r'\(([^)]+)\)', train_line_nm)
        if bracket_match:
            train_type_info = bracket_match.group(1)
            # 괄호 부분 제거
            train_line_nm = re.sub(r'\s*\([^)]+\)', '', train_line_nm)
        
        # " - " 기준으로 분리
        if " - " in train_line_nm:
            parts = train_line_nm.split(" - ")
            
            # 첫 번째 부분에서 행선지 추출
            if len(parts) >= 1:
                destination_part = parts[0].strip()
                if destination_part.endswith("행"):
                    destination = destination_part[:-1]  # "행" 제거
                else:
                    destination = destination_part
            
            # 두 번째 부분에서 다음역 추출
            if len(parts) >= 2:
                next_station_part = parts[1].strip()
                if next_station_part.endswith("방면"):
                    next_station = next_station_part[:-2]  # "방면" 제거
                else:
                    next_station = next_station_part
        else:
            # " - "가 없는 경우, 전체를 행선지로 처리
            if train_line_nm.endswith("행"):
                destination = train_line_nm[:-1]
            else:
                destination = train_line_nm
        
        return {
            "destination": destination.strip(),
            "next_station": next_station.strip(),
            "train_type_info": train_type_info.strip()
        }

    def is_line_matched(self, line_name: str, subway_id: str, target_line: str) -> bool:
        """단일 노선이 매칭되는지 확인합니다."""
        # 1. 정확한 노선명 매칭
        if target_line == line_name:
            return True
        
        # 2. 줄임말 매핑을 통한 매칭 (예: "수인" -> "수인분당선")
        if target_line in self.line_shortcuts:
            full_line_name = self.line_shortcuts[target_line]
            if full_line_name == line_name:
                return True
        
        # 3. "9호선" 형태로 매칭
        if f"{target_line}호선" == line_name:
            return True
        
        # 4. 레거시 지원: 숫자만으로 매칭 (subway_id에서 추출)
        if target_line.isdigit():
            line_number = self.extract_line_number_from_subway_id(subway_id)
            if target_line == line_number:
                return True
        
        # 5. 부분 문자열 매칭 (기존 방식)
        if target_line in line_name:
            return True
        
        return False

    def is_terminal_train(self, destination: str, next_station: str) -> bool:
        """종점 열차인지 확인합니다."""
        if not destination or not next_station:
            return False
        
        destination_clean = destination.strip()
        next_station_clean = next_station.strip()
        
        return (destination_clean != "" and 
                next_station_clean != "" and
                destination_clean == next_station_clean)

    def _extract_basic_info(self, arrival: Dict) -> Dict:
        """기본 정보를 추출합니다."""
        subway_id = arrival.get("subwayId", "")
        line_name = self.subway_lines.get(subway_id, subway_id)
        arrival_msg = arrival.get("arvlMsg2", "")
        arrival_code = arrival.get("arvlCd", "")
        
        return {
            "subway_id": subway_id,
            "line_name": line_name,
            "arrival_msg": arrival_msg,
            "arrival_code": arrival_code,
            "recptn_dt": arrival.get("recptnDt", "")
        }

    def _parse_arrival_times(self, arrival: Dict, arrival_msg: str) -> int:
        """도착 시간을 파싱합니다."""
        arrival_time_seconds = self.parse_arrival_time_from_seconds(arrival.get("barvlDt", ""))
        if arrival_time_seconds == -1:
            arrival_time_seconds = self.parse_arrival_time_from_message(arrival_msg)
        return arrival_time_seconds

    def _extract_train_info(self, arrival: Dict) -> Dict:
        """열차 정보를 추출합니다."""
        train_line_nm = arrival.get("trainLineNm", "")
        parsed_train_info = self.parse_train_line_info(train_line_nm)
        
        destination = parsed_train_info["destination"] or self.extract_destination_from_direction(train_line_nm)
        next_station_from_train_line = parsed_train_info["next_station"]
        train_type_from_line = parsed_train_info["train_type_info"]
        
        return {
            "direction": train_line_nm,
            "destination": destination,
            "next_station_from_direction": next_station_from_train_line,
            "train_type_from_direction": train_type_from_line
        }

    def _determine_train_type(self, arrival: Dict, train_type_from_line: str) -> Dict:
        """열차 유형을 결정합니다.
        
        ✨ 개선사항: Config에서 열차 유형 매핑 가져오기
        """
        btraint_status = arrival.get("btrainSttus", "")
        
        # Config에서 열차 유형 매핑 가져오기
        train_type_mapping = Config.TRAIN_TYPE_MAPPING
        
        # 우선순위: trainLineNm의 괄호 안 정보 > btrainSttus 필드
        train_type = train_type_from_line if train_type_from_line else btraint_status
        
        # 표준화된 열차 유형으로 변환
        normalized_train_type = train_type_mapping.get(train_type, train_type or "일반")
        
        return {
            "train_type": normalized_train_type,
            "is_express": normalized_train_type in ["급행", "특급", "ITX", "KTX"]
        }

    def _extract_station_info(self, arrival: Dict) -> Dict:
        """역 정보를 추출합니다."""
        return {
            "station_id": arrival.get("statnId", ""),
            "previous_station_id": arrival.get("statnFid", ""),
            "next_station_id": arrival.get("statnTid", ""),
            "updn_line": arrival.get("updnLine", ""),
            "arrival_detail": arrival.get("arvlMsg3", "")
        }

    def process_single_arrival(self, arrival: Dict, station_name: str) -> Dict:
        """단일 도착 정보를 처리합니다.
        
        ✨ 개선사항: 메서드 분리로 가독성 향상
        """
        # 1. 기본 정보 추출
        basic_info = self._extract_basic_info(arrival)
        
        # 2. 도착 시간 파싱
        arrival_time_seconds = self._parse_arrival_times(arrival, basic_info["arrival_msg"])
        
        # 3. 열차 정보 추출
        train_info = self._extract_train_info(arrival)
        
        # 4. 열차 유형 결정
        train_type_info = self._determine_train_type(arrival, train_info["train_type_from_direction"])
        
        # 5. 역 정보 추출
        station_info = self._extract_station_info(arrival)
        
        # 6. 종점 처리
        is_terminal = self.is_terminal_train(train_info["destination"], train_info["next_station_from_direction"])
        
        # 7. 시간 정보 계산
        time_info = self.calculate_time_info(arrival_time_seconds, basic_info["arrival_msg"], basic_info["recptn_dt"])
        
        # 8. 결과 통합
        return {
            **basic_info,
            "station": station_name,
            **train_info,
            **train_type_info,
            **station_info,
            "arrival_time": arrival_time_seconds,
            "arrival_time_formatted": time_info["arrival_time_formatted"],
            "remaining_time_formatted": time_info["remaining_time_formatted"],
            "arrival_time_text": time_info["arrival_time_text"],
            "time_reference": time_info["time_reference"],
            "time_reference_formatted": time_info["time_reference_formatted"],
            "is_terminal": is_terminal,
            "arrival_message": basic_info["arrival_msg"]
        }

    def filter_arrivals_by_lines(self, arrivals: List[Dict], target_lines: List[str]) -> List[Dict]:
        """지정된 노선들로 도착 정보를 필터링합니다."""
        filtered_arrivals = []
        
        for arrival in arrivals:
            line_name = arrival["line_name"]
            subway_id = arrival["subway_id"]
            
            # 노선 매칭 체크
            for target_line in target_lines:
                if self.is_line_matched(line_name, subway_id, target_line):
                    filtered_arrivals.append(arrival)
                    break  # 하나라도 매칭되면 추가하고 다음 arrival로
        
        return filtered_arrivals 