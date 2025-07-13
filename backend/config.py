import os
from typing import List

class Config:
    """애플리케이션 설정 클래스"""
    
    # 서울 지하철 API 설정
    SEOUL_API_KEY = os.getenv("SEOUL_API_KEY", "sample_key")
    SEOUL_API_BASE_URL = "http://swopenapi.seoul.go.kr/api/subway"
    MAX_ARRIVALS = 10
    
    # OpenAI API 설정
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = "gpt-4o-mini"
    
    # CORS 설정
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # 양방향 키워드 설정
    BIDIRECTIONAL_KEYWORDS: List[str] = [
        "양방향", "둘다", "모든 방향", "전체", "상하행", "내외선"
    ]
    
    # 서버 설정
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", "8000"))
    
    # 로깅 설정
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO") 