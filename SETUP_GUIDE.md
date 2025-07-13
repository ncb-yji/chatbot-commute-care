# 🚀 Commute Care 설정 및 실행 가이드

## 📥 1. 프로젝트 클론 및 기본 설정

```bash
# 1. 프로젝트 클론
git clone https://github.com/your-username/03-chatbot-commute-care.git
cd 03-chatbot-commute-care

# 2. 백엔드 가상환경 생성 및 활성화
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Python 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt
```

## ⚙️ 2. 환경변수 설정

```bash
# 루트 디렉토리로 이동
cd ..

# 환경변수 파일 생성
cp .env.example .env
```

**.env 파일 편집** (중요! 🔑)
```bash
# 실제 API 키로 변경하세요
SEOUL_API_KEY=your_actual_seoul_api_key_here
OPENAI_API_KEY=your_actual_openai_api_key_here
PORT=8000
LOG_LEVEL=INFO
```

### API 키 발급 방법

**🚇 서울 지하철 API 키**
1. [서울 열린데이터 광장](https://data.seoul.go.kr/) 접속
2. 회원가입 후 로그인
3. 마이페이지 → 인증키 신청
4. "지하철 실시간 도착정보" API 신청

**🤖 OpenAI API 키**
1. [OpenAI 플랫폼](https://platform.openai.com/) 접속
2. 회원가입 후 로그인
3. API Keys 메뉴에서 새 키 생성
4. 결제 정보 등록 (사용량 기반 과금)

## 🖥️ 3. 백엔드 실행

```bash
# backend 디렉토리에서 (가상환경 활성화 상태)
cd backend
python main.py

# 또는 uvicorn으로 직접 실행
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 백엔드 확인
- 🔗 **API 서버**: http://localhost:8000
- 📚 **API 문서**: http://localhost:8000/docs
- 🏥 **헬스 체크**: http://localhost:8000/health

## 🌐 4. 프론트엔드 실행

**새 터미널 창을 열고:**

```bash
# 프로젝트 루트에서 frontend로 이동
cd frontend

# Node.js 의존성 설치
npm install

# React 개발 서버 실행
npm start
```

### 프론트엔드 확인
- 🌐 **웹 애플리케이션**: http://localhost:3000

## 🐳 5. Docker로 한 번에 실행 (선택사항)

Docker가 설치되어 있다면 더 간단하게 실행할 수 있습니다:

```bash
# 환경변수 설정 후 (위의 .env 파일 설정 필수)
docker-compose up --build

# 백그라운드 실행
docker-compose up -d --build
```

## ✅ 6. 정상 작동 확인

### 백엔드 테스트
```bash
# 헬스 체크
curl http://localhost:8000/health

# 지하철 정보 테스트
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "강남역 도착정보 알려줘"}'
```

### 프론트엔드 테스트
1. 브라우저에서 http://localhost:3000 접속
2. "강남역 도착정보 알려줘" 입력
3. 챗봇 응답 확인

## 🔧 문제 해결

### 자주 발생하는 문제들

**1. 포트 충돌 오류**
```bash
# 포트 사용 확인
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# 프로세스 종료 (Windows)
taskkill /PID [PID번호] /F
```

**2. Python 패키지 오류**
```bash
# 가상환경 재생성
deactivate
rmdir /s venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**3. API 키 오류**
- `.env` 파일이 루트 디렉토리에 있는지 확인
- API 키에 따옴표나 공백이 있는지 확인
- 서울 API 키 활성화 상태 확인

**4. CORS 오류**
- 백엔드가 먼저 실행되고 있는지 확인
- `backend/config.py`의 CORS_ORIGINS 설정 확인

**5. Node.js 오류**
```bash
# 캐시 정리
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

## 📱 사용법

1. **웹 브라우저**에서 http://localhost:3000 접속
2. **지하철역 이름** 입력 (예: "강남역", "홍대입구역")
3. **실시간 도착정보** 확인

### 예시 질문들
- "강남역 도착정보 알려줘"
- "홍대입구역 언제 와?"
- "신촌역 실시간 정보"
- "건대입구역 지하철 상황"

## 🚀 개발 모드 vs 프로덕션 모드

### 개발 모드 (현재)
- 백엔드: `python main.py` 또는 `uvicorn --reload`
- 프론트엔드: `npm start`
- 핫 리로드 지원

### 프로덕션 모드
```bash
# Docker Compose 사용
docker-compose up -d --build

# 또는 각각 빌드
cd frontend && npm run build
cd ../backend && uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📊 모니터링

### 로그 확인
```bash
# 백엔드 로그 (터미널에서 확인)
# 프론트엔드 로그 (브라우저 개발자 도구)

# Docker 로그
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 성능 확인
- **백엔드 응답시간**: API 문서에서 테스트
- **프론트엔드 로딩**: 브라우저 네트워크 탭
- **메모리 사용량**: 작업 관리자 또는 `docker stats`

## 🎯 다음 단계

1. **클라우드 배포**: `deploy/` 디렉토리의 스크립트 사용
2. **기능 확장**: 새로운 지하철 노선 추가
3. **UI 개선**: React 컴포넌트 커스터마이징
4. **API 확장**: 새로운 엔드포인트 추가

---

## 🆘 도움이 필요하다면

- 📖 **상세 문서**: `README_DOCKER.md` 참조
- 🚀 **배포 가이드**: `deploy/README.md` 참조
- 🔧 **API 문서**: http://localhost:8000/docs
- 💬 **이슈 리포트**: GitHub Issues 활용

**Happy Coding! 🎉** 