from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from typing import Optional, Dict, Any
import os
import time
from dotenv import load_dotenv

# .env 파일 로드 (backend 폴더 내의 .env 파일)
load_dotenv()

from config import Config
from services.subway_service import SubwayService
from services.openai_service import OpenAIService

# 로깅 설정
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Commute Care Chatbot API",
    description="지하철 실시간 정보를 제공하는 통근 케어 챗봇 API",
    version="1.0.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 로컬 개발을 위해 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 인스턴스 생성
subway_service = SubwayService()
openai_service = OpenAIService()

# 요청/응답 모델 정의
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"  # user_id 필드 추가
    performance_mode: Optional[str] = "original"

class ChatResponse(BaseModel):
    response: str
    parsed_data: Optional[Dict[str, Any]] = None
    subway_data: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    message: str

# API 엔드포인트
@app.get("/", response_model=HealthResponse)
async def root():
    """루트 엔드포인트 - 서비스 상태 확인"""
    return HealthResponse(
        status="healthy",
        message="Commute Care Chatbot API is running!"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크 엔드포인트"""
    return HealthResponse(
        status="healthy",
        message="Service is running properly"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    지하철 정보 챗봇 메인 엔드포인트
    
    사용자의 메시지를 받아서 지하철 실시간 정보를 조회하고
    자연어로 응답을 생성합니다.
    """
    start_time = time.time()
    
    try:
        logger.info(f"📥 챗봇 요청 수신: {request.message}")
        
        # 1. 사용자 메시지에서 역 이름 파싱 (단일 역만 처리)
        parsing_start = time.time()
        parsed_data = openai_service.parse_station_query(request.message)
        parsing_time = time.time() - parsing_start
        logger.info(f"⚡ 파싱 완료: {parsing_time:.3f}초")
        
        stations = parsed_data.get("stations", [])
        target_lines = parsed_data.get("lines", [])
        
        # 2. 지하철 실시간 정보 조회 (단일 역만 지원)
        subway_data = {"arrivals": []}
        api_time = 0
        
        if stations:
            # 단일 역의 정보를 조회 (경량화)
            station_name = stations[0]
            api_start = time.time()
            subway_data = subway_service.get_realtime_arrival(station_name, target_lines)
            api_time = time.time() - api_start
            logger.info(f"🚇 지하철 API 조회 완료: {station_name} ({api_time:.3f}초)")
        
        # 3. OpenAI 서비스를 통한 응답 생성
        response_start = time.time()
        response_text = openai_service.generate_response(
            request.message, 
            subway_data, 
            parsed_data
        )
        response_time = time.time() - response_start
        
        total_time = time.time() - start_time
        logger.info(f"🤖 응답 생성 완료: {len(response_text)}자 ({response_time:.3f}초)")
        logger.info(f"📊 총 처리 시간: {total_time:.3f}초 [파싱: {parsing_time:.3f}s, API: {api_time:.3f}s, 응답생성: {response_time:.3f}s]")
        
        return ChatResponse(
            response=response_text,
            parsed_data=parsed_data,
            subway_data=subway_data
        )
        
    except Exception as e:
        logger.error(f"챗봇 처리 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"챗봇 처리 중 오류가 발생했습니다: {str(e)}"
        )

@app.get("/stations/{station_name}")
async def get_station_info(station_name: str):
    """
    특정 역의 실시간 도착 정보를 조회합니다.
    """
    try:
        logger.info(f"역 정보 조회: {station_name}")
        
        subway_data = subway_service.get_realtime_arrival(station_name, None)
        
        if subway_data["status"] == "error":
            raise HTTPException(
                status_code=404,
                detail=subway_data["message"]
            )
        
        return subway_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"역 정보 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"역 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

# 애플리케이션 시작 이벤트
@app.on_event("startup")
async def startup_event():
    logger.info("Commute Care Chatbot API 시작")
    logger.info(f"서버 포트: {Config.PORT}")
    logger.info(f"로그 레벨: {Config.LOG_LEVEL}")

# 애플리케이션 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Commute Care Chatbot API 종료")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True,
        log_level=Config.LOG_LEVEL.lower()
    ) 