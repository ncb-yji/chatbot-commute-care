# 🚀 Commute Care 설정 및 실행 가이드

## 🐍 0. Python 설치 (필수 사전 준비)

### Windows 10/11 사용자

**방법 1: 공식 웹사이트에서 설치 (권장)**
1. [Python 공식 웹사이트](https://www.python.org/downloads/) 접속
2. **"Download Python 3.11.x"** 버튼 클릭 (최신 3.11 버전 권장)
3. 다운로드한 설치 파일 실행
4. ⚠️ **중요**: "Add Python to PATH" 체크박스 반드시 선택
5. "Install Now" 클릭하여 설치

**방법 2: Microsoft Store (간편)**
1. Windows 키 + R → "ms-windows-store:" 입력
2. "Python 3.11" 검색하여 설치

**설치 확인**
```cmd
# 명령 프롬프트(CMD) 또는 PowerShell에서 확인
python --version
pip --version
```

### macOS 사용자

**방법 1: 공식 웹사이트 (권장)**
1. [Python 공식 웹사이트](https://www.python.org/downloads/) 접속
2. macOS용 Python 3.11.x 다운로드
3. .pkg 파일 실행하여 설치

**방법 2: Homebrew (개발자 권장)**
```bash
# Homebrew가 없다면 먼저 설치
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 설치
brew install python@3.11
```

**설치 확인**
```bash
python3 --version
pip3 --version
```

### Ubuntu/Linux 사용자

```bash
# 시스템 업데이트
# Python 3.11 및 필수 도구 설치
sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# 기본 python 명령어 설정 (선택사항)
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1
sudo update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
```

**설치 확인**
```bash
python --version  # 또는 python3 --version
pip --version      # 또는 pip3 --version
```

## 📥 1. 프로젝트 클론 및 기본 설정

### Git 설치 확인
```bash
# Git이 설치되어 있는지 확인
git --version

# 없다면 설치:
# Windows: https://git-scm.com/download/win
# macOS: brew install git
# Ubuntu: sudo apt install git
```

### 프로젝트 다운로드
```bash
# 1. 프로젝트 클론
git clone https://github.com/your-username/03-chatbot-commute-care.git
cd 03-chatbot-commute-care

# 2. 백엔드 디렉토리로 이동
cd backend
```

### Python 가상환경 생성 및 활성화

**Windows (명령 프롬프트/PowerShell)**
```cmd
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
venv\Scripts\activate

# 성공 시 프롬프트 앞에 (venv) 표시됨
```

**macOS/Linux**
```bash
# 가상환경 생성
python3 -m venv venv
# 또는
python -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 성공 시 프롬프트 앞에 (venv) 표시됨
```

### Python 의존성 설치
```bash
# pip 최신 버전으로 업그레이드
python -m pip install --upgrade pip

# 프로젝트 의존성 설치
pip install -r requirements.txt

# 설치 확인
pip list
```

**설치 중 오류 발생 시:**
- **Windows**: Visual Studio Build Tools 설치 필요할 수 있음
- **macOS**: Xcode Command Line Tools 설치: `xcode-select --install`
- **Ubuntu**: 빌드 도구 설치: `sudo apt install build-essential python3-dev`

## ⚙️ 2. 환경변수 설정

### .env 파일 생성
```bash
# 프로젝트 루트 디렉토리로 이동
cd ..

# .env 파일 생성 (Windows)
copy nul .env

# .env 파일 생성 (macOS/Linux)  
touch .env
```

### .env 파일 편집 (중요! 🔑)
텍스트 에디터로 `.env` 파일을 열고 다음 내용을 입력:

```env
# 서울 지하철 실시간 API 키 (필수)
SEOUL_API_KEY=your_actual_seoul_api_key_here

# OpenAI API 키 (필수)
OPENAI_API_KEY=sk-your_actual_openai_api_key_here

# 서버 설정
PORT=8000
LOG_LEVEL=INFO

# CORS 설정 (개발용)
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

### API 키 발급 방법

**🚇 서울 지하철 API 키 (무료)**
1. [서울 열린데이터 광장](https://data.seoul.go.kr/) 접속
2. 회원가입 후 로그인
3. **마이페이지** → **인증키 신청**
4. **"지하철 실시간 도착정보"** API 신청
5. 승인 후 인증키를 `.env` 파일에 복사

**🤖 OpenAI API 키 (유료)**
1. [OpenAI 플랫폼](https://platform.openai.com/) 접속
2. 회원가입 후 로그인
3. **API Keys** 메뉴 → **Create new secret key**
4. 키 이름 입력 후 생성
5. ⚠️ **중요**: 키를 즉시 복사 (다시 볼 수 없음)
6. **Billing** 메뉴에서 결제 정보 등록 (최소 $5 충전 권장)

## 🖥️ 3. 백엔드 실행

### 기본 실행 방법
```bash
# backend 디렉토리에서 (가상환경 활성화 상태)
cd backend

# 방법 1: 직접 실행
python main.py

# 방법 2: uvicorn으로 실행 (개발 모드)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 방법 3: 프로덕션 모드
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 백엔드 정상 작동 확인
**터미널에서 확인:**
```bash
# 헬스 체크
curl http://localhost:8000/health

# 또는 웹 브라우저에서 접속:
```
- 🔗 **API 서버**: http://localhost:8000
- 📚 **API 문서**: http://localhost:8000/docs  
- 🏥 **헬스 체크**: http://localhost:8000/health

**정상 실행 시 터미널 출력 예시:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345]
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## 🌐 4. 프론트엔드 실행

### Node.js 설치 (프론트엔드용)

**Windows:**
1. [Node.js 공식 웹사이트](https://nodejs.org/) 접속
2. **LTS 버전** 다운로드 (18.x 이상 권장)
3. 설치 파일 실행

**macOS:**
```bash
# Homebrew 사용
brew install node

# 또는 공식 웹사이트에서 다운로드
```

**Ubuntu:**
```bash
# NodeSource 저장소 추가
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# Node.js 설치
sudo apt-get install -y nodejs
```

**설치 확인:**
```bash
node --version
npm --version
```

### React 애플리케이션 실행

**새 터미널 창을 열고:**

```bash
# 프로젝트 루트에서 frontend로 이동
cd frontend

# Node.js 의존성 설치 (첫 실행 시만)
npm install

# React 개발 서버 실행
npm start
```

### 프론트엔드 확인
- 🌐 **웹 애플리케이션**: http://localhost:3000
- 자동으로 브라우저가 열림

## 🐳 5. Docker로 한 번에 실행 (고급 사용자)

### Docker 설치
- **Windows/macOS**: [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치
- **Ubuntu**: [Docker Engine 설치 가이드](https://docs.docker.com/engine/install/ubuntu/) 참조

### Docker Compose 실행
```bash
# 환경변수 설정 후 (.env 파일 필수)
docker-compose up --build

# 백그라운드 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

## ✅ 6. 정상 작동 확인

### 전체 시스템 테스트

**1. API 테스트 (터미널)**
```bash
# 헬스 체크
curl http://localhost:8000/health

# 지하철 정보 테스트
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "강남역 도착정보 알려줘"}'
```

**2. 웹 인터페이스 테스트**
1. 브라우저에서 http://localhost:3000 접속
2. 채팅 입력창에 **"강남역 도착정보 알려줘"** 입력
3. 챗봇 응답 확인 (보통 5-10초 소요)

### 예시 테스트 질문들
```
"강남역 도착정보 알려줘"
"홍대입구역 지하철 언제 와?"
"신촌역 실시간 정보"
"건대입구역 2호선"
"모란 8호선"
```

## 🔧 문제 해결

### 1. Python 관련 오류

**"python을 찾을 수 없습니다" 오류**
- Windows: Python 설치 시 "Add to PATH" 체크 확인
- 시스템 재시작 후 다시 시도
- 환경변수에 Python 경로 수동 추가

**가상환경 활성화 오류**
```bash
# Windows에서 실행 정책 오류 시
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 가상환경 재생성
deactivate
rmdir /s venv    # Windows
rm -rf venv      # macOS/Linux
python -m venv venv
```

### 2. 의존성 설치 오류

**pip 설치 오류**
```bash
# pip 업그레이드
python -m pip install --upgrade pip

# 캐시 정리
pip cache purge

# 개별 패키지 재설치
pip install --no-cache-dir fastapi uvicorn
```

**빌드 도구 오류**
- **Windows**: [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) 설치
- **macOS**: `xcode-select --install`
- **Ubuntu**: `sudo apt install build-essential python3-dev`

### 3. 포트 충돌 오류

**포트 8000/3000이 이미 사용 중**
```bash
# Windows - 포트 사용 프로세스 확인
netstat -ano | findstr :8000
taskkill /PID [PID번호] /F

# macOS/Linux
lsof -i :8000
kill -9 [PID번호]

# 다른 포트 사용
uvicorn main:app --port 8001  # 백엔드
PORT=3001 npm start          # 프론트엔드
```

### 4. API 키 관련 오류

**API 키 인식 안됨**
- `.env` 파일이 **프로젝트 루트**에 있는지 확인
- API 키에 따옴표나 공백 없는지 확인
- 파일 인코딩이 UTF-8인지 확인

**서울 API 오류**
- [서울 열린데이터 광장](https://data.seoul.go.kr/)에서 키 상태 확인
- 일일 호출 한도 초과 여부 확인

**OpenAI API 오류**
- 잔액 부족 확인 (최소 $5 필요)
- API 키 유효성 확인
- 사용량 한도 확인

### 5. CORS 오류

**프론트엔드에서 백엔드 접근 불가**
- 백엔드가 먼저 실행되고 있는지 확인
- `backend/config.py`의 CORS_ORIGINS 설정 확인
- 브라우저 캐시 정리

### 6. Node.js/React 오류

**npm 설치 오류**
```bash
# 캐시 정리
npm cache clean --force

# node_modules 재설치
rm -rf node_modules package-lock.json
npm install

# Node.js 버전 확인 (18.x 이상 필요)
node --version
```

## 📱 사용법 및 기능

### 기본 사용법
1. **웹 브라우저**에서 http://localhost:3000 접속
2. **지하철역 이름** 입력
3. **Enter 키** 또는 **전송 버튼** 클릭
4. **실시간 도착정보** 확인 (5-10초 소요)

### 지원하는 질문 형태
- **역 이름만**: "강남역", "홍대입구역"
- **자연어 질문**: "강남역 도착정보 알려줘", "홍대 언제 와?"
- **특정 호선**: "강남역 2호선", "모란 8호선"
- **상행/하행**: "강남역 상행선", "홍대 하행"

### 지원 지하철 노선
- 1호선 ~ 9호선
- 경의중앙선, 경춘선, 수인분당선
- 신분당선, 우이신설선, 김포골드라인 등

## 🚀 개발 환경 vs 프로덕션 환경

### 개발 환경 (현재 설정)
```bash
# 백엔드: 자동 재시작 활성화
uvicorn main:app --reload

# 프론트엔드: 핫 리로드 활성화  
npm start
```

### 프로덕션 환경
```bash
# 프론트엔드 빌드
cd frontend && npm run build

# 백엔드 프로덕션 실행
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000

# 또는 Docker 사용
docker-compose up -d --build
```

## 📊 성능 모니터링

### 응답 시간 확인
- **정상 범위**: 5-10초
- **OpenAI API**: 전체 시간의 80-90%
- **지하철 API**: 전체 시간의 1-5%

### 로그 확인
```bash
# 백엔드 로그 (터미널)
# 상세한 성능 정보 포함

# 브라우저 개발자 도구 (F12)
# 네트워크 탭에서 API 호출 시간 확인
```

### Docker 환경 모니터링
```bash
# 컨테이너 상태 확인
docker-compose ps

# 리소스 사용량 확인
docker stats

# 로그 실시간 보기
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 🎯 다음 단계

### 클라우드 배포
- **Ubuntu 서버**: `deploy/ubuntu-deploy.sh` 실행
- **Kakao Cloud**: `deploy/kakao-cloud-deploy.sh` 사용
- **상세 가이드**: `deploy/README.md` 참조

### 기능 확장
- 새로운 지하철 노선 추가
- 실시간 알림 기능
- 즐겨찾기 역 설정

### 성능 최적화
- OpenAI API 모델 변경 (gpt-3.5-turbo)
- 응답 캐싱 시스템 구축
- 스트리밍 응답 구현

---

## 🆘 도움이 필요하다면

- 📖 **Docker 상세 문서**: `README_DOCKER.md` 참조  
- 🚀 **배포 가이드**: `deploy/README.md` 참조
- 🔧 **API 문서**: http://localhost:8000/docs
- 💬 **이슈 리포트**: GitHub Issues 활용

**Happy Coding! 🎉** 