# 🚇 CommuteCare - 출퇴근 도우미 챗봇

지하철 실시간 도착정보를 제공하는 AI 챗봇 애플리케이션입니다.

## 📋 프로젝트 개요

사용자가 자연어로 질문하면 ChatGPT가 출발지/목적지를 파싱하고, 서울열린데이터 API를 통해 지하철 실시간 도착정보를 제공하는 웹 애플리케이션입니다.

### 주요 기능
- 🤖 자연어 처리 기반 지하철 정보 조회
- 📊 실시간 도착정보 제공
- 💬 직관적인 채팅 인터페이스
- 📱 반응형 웹 디자인

## 🏗️ 시스템 구조

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React 웹앱    │───▶│  FastAPI 서버   │───▶│  서울열린데이터  │
│  (프론트엔드)    │    │   (백엔드)      │    │     API        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │   (ChatGPT)     │
                       └─────────────────┘
```

## 🛠️ 기술 스택

### 프론트엔드
- **React** 18.2.0
- **Axios** - HTTP 클라이언트
- **Lucide React** - 아이콘
- **CSS3** - 스타일링

### 백엔드
- **FastAPI** - 웹 프레임워크
- **Python** 3.7+
- **OpenAI API** - 자연어 처리
- **Requests** - HTTP 클라이언트

### 외부 API
- **OpenAI GPT-3.5-turbo** - 자연어 처리
- **서울열린데이터** - 지하철 실시간 도착정보

## 🚀 설치 및 실행

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd 03-chatbot-commute-care
```

### 2. 백엔드 설정
```bash
cd backend

# 가상환경 생성 (선택사항)
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
# .env 파일 생성 후 다음 내용 추가:
# OPENAI_API_KEY=your_openai_api_key_here
# SEOUL_API_KEY=6178467767797a733130384e6e705574

# 서버 실행
python main.py
```

### 3. 프론트엔드 설정
```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm start
```

## 📡 API 엔드포인트

### 백엔드 API (http://localhost:8001)

| 메소드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/` | API 상태 확인 |
| GET | `/health` | 헬스 체크 |
| POST | `/chat` | 챗봇 대화 처리 |
| GET | `/stations/{station_name}` | 특정 역 정보 조회 |
| GET | `/test-openai` | OpenAI API 테스트 |
| GET | `/test-subway` | 지하철 API 테스트 |

## 💬 사용 예시

### 지원하는 질문 형태
- "강남역 도착정보 알려줘"
- "홍대입구역 언제 와?"
- "신촌역 실시간 정보"
- "건대입구역 지하철 정보"

### API 호출 예시
```bash
# 챗봇 대화
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "강남역 도착정보 알려줘"}'

# 특정 역 정보 조회
curl "http://localhost:8001/stations/강남"
```

## 🎯 동작 흐름

1. **사용자 입력**: 웹 인터페이스에서 지하철 관련 질문 입력
2. **자연어 처리**: ChatGPT가 역 이름과 의도 파싱
3. **데이터 조회**: 서울열린데이터 API에서 실시간 도착정보 조회
4. **응답 생성**: ChatGPT가 자연어로 최종 답변 생성
5. **결과 표시**: 웹 인터페이스에 친근한 형태로 정보 제공

## 📁 프로젝트 구조

```
03-chatbot-commute-care/
├── backend/
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── config.py            # 환경 설정
│   ├── requirements.txt     # Python 의존성
│   ├── README.md           # 백엔드 문서
│   └── services/
│       ├── __init__.py
│       ├── openai_service.py    # OpenAI API 서비스
│       └── subway_service.py    # 지하철 API 서비스
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js          # 메인 React 컴포넌트
│   │   ├── App.css         # 메인 스타일
│   │   ├── index.js        # React 진입점
│   │   └── index.css       # 전역 스타일
│   ├── package.json        # Node.js 의존성
│   └── README.md          # 프론트엔드 문서
└── README.md              # 프로젝트 메인 문서
```

## 🔧 개발 환경

- **Node.js** 16.0+
- **Python** 3.7+
- **NPM** 8.0+

## 🚨 주의사항

1. **OpenAI API 키 필수**: 백엔드 실행 전 `.env` 파일에 OpenAI API 키 설정 필요
2. **CORS 설정**: 프론트엔드와 백엔드 간 통신을 위한 CORS 설정 확인
3. **API 제한**: 서울열린데이터 API 호출 제한 고려

## 🐛 문제 해결

### 백엔드 관련
- **OpenAI API 오류**: `.env` 파일에 올바른 API 키 설정 확인
- **지하철 API 오류**: 역 이름을 정확히 입력 (예: "강남역" → "강남")
- **CORS 오류**: `config.py`의 `ALLOWED_ORIGINS` 설정 확인

### 프론트엔드 관련
- **서버 연결 오류**: 백엔드 서버 실행 상태 확인
- **API 응답 없음**: 백엔드 환경변수 설정 확인
- **스타일 깨짐**: 브라우저 캐시 삭제 후 새로고침

## 📄 라이센스

이 프로젝트는 MIT 라이센스를 따릅니다.

## 🤝 기여

버그 리포트, 기능 요청, 풀 리퀘스트를 환영합니다!

---

**CommuteCare** - 더 나은 출퇴근을 위한 스마트한 동반자 🚇✨ 