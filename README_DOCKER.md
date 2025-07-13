# 🐳 Docker 배포 가이드

## 📋 사전 준비사항

### 1. 필요한 API 키 발급

**서울 열린데이터 광장 API 키**
1. [서울 열린데이터 광장](https://data.seoul.go.kr/) 회원가입
2. 마이페이지 > 인증키 신청
3. "지하철 실시간 도착정보" API 신청

**OpenAI API 키**
1. [OpenAI 플랫폼](https://platform.openai.com/) 회원가입
2. API Keys 메뉴에서 새 키 생성
3. 결제 정보 등록 (사용량 기반 과금)

### 2. 환경변수 설정

```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 실제 API 키 입력
# SEOUL_API_KEY=your_actual_seoul_api_key
# OPENAI_API_KEY=your_actual_openai_api_key
```

## 🚀 로컬 Docker 실행

### 전체 서비스 실행
```bash
# Docker Compose로 전체 서비스 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d --build
```

### 개별 서비스 실행
```bash
# 백엔드만 실행
docker-compose up backend

# 프론트엔드만 실행
docker-compose up frontend
```

### 접속 URL
- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

## ☁️ 클라우드 배포

### AWS ECS (Elastic Container Service)

1. **ECR 레포지토리 생성**
```bash
# AWS CLI 설치 및 설정 후
aws ecr create-repository --repository-name commute-care-backend
aws ecr create-repository --repository-name commute-care-frontend
```

2. **이미지 빌드 및 푸시**
```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin {account-id}.dkr.ecr.ap-northeast-2.amazonaws.com

# 백엔드 이미지
docker build -t commute-care-backend ./backend
docker tag commute-care-backend:latest {account-id}.dkr.ecr.ap-northeast-2.amazonaws.com/commute-care-backend:latest
docker push {account-id}.dkr.ecr.ap-northeast-2.amazonaws.com/commute-care-backend:latest

# 프론트엔드 이미지
docker build -t commute-care-frontend ./frontend
docker tag commute-care-frontend:latest {account-id}.dkr.ecr.ap-northeast-2.amazonaws.com/commute-care-frontend:latest
docker push {account-id}.dkr.ecr.ap-northeast-2.amazonaws.com/commute-care-frontend:latest
```

3. **ECS 태스크 정의 생성**
   - AWS 콘솔에서 ECS 서비스 생성
   - 태스크 정의에서 환경변수 설정

### Google Cloud Run

1. **gcloud CLI 설치 및 인증**
```bash
gcloud auth login
gcloud config set project your-project-id
```

2. **이미지 빌드 및 배포**
```bash
# 백엔드 배포
gcloud builds submit --tag gcr.io/your-project-id/commute-care-backend ./backend
gcloud run deploy commute-care-backend \
  --image gcr.io/your-project-id/commute-care-backend \
  --platform managed \
  --region asia-northeast1 \
  --set-env-vars SEOUL_API_KEY=your_key,OPENAI_API_KEY=your_key

# 프론트엔드 배포
gcloud builds submit --tag gcr.io/your-project-id/commute-care-frontend ./frontend
gcloud run deploy commute-care-frontend \
  --image gcr.io/your-project-id/commute-care-frontend \
  --platform managed \
  --region asia-northeast1
```

### Azure Container Instances

```bash
# 리소스 그룹 생성
az group create --name commute-care-rg --location koreacentral

# 컨테이너 그룹 생성
az container create \
  --resource-group commute-care-rg \
  --name commute-care-app \
  --image commute-care-backend:latest \
  --environment-variables SEOUL_API_KEY=your_key OPENAI_API_KEY=your_key \
  --ports 8000 \
  --dns-name-label commute-care-backend
```

### 카카오 클라우드 (Kakao i Cloud)

**Docker Compose 배포**
```bash
# 카카오 클라우드 전용 설정 사용
cd deploy
docker-compose -f kakao-cloud.yml up -d --build
```

**Kubernetes 배포**
```bash
# 환경변수 설정
export SEOUL_API_KEY='your_seoul_api_key'
export OPENAI_API_KEY='your_openai_api_key'

# 카카오 클라우드 배포 스크립트 실행
cd deploy
./kakao-cloud-deploy.sh all

# 개별 작업 실행
./kakao-cloud-deploy.sh build    # 이미지 빌드만
./kakao-cloud-deploy.sh deploy   # 배포만
./kakao-cloud-deploy.sh rollback # 롤백
./kakao-cloud-deploy.sh cleanup  # 리소스 정리
```

### Ubuntu 서버 배포

```bash
# Ubuntu 서버에 자동 배포
cd deploy
./ubuntu-deploy.sh production

# 스테이징 환경으로 배포
./ubuntu-deploy.sh staging
```

## 🔧 트러블슈팅

### 공통 문제

**포트 충돌**
```bash
# 사용 중인 포트 확인
netstat -an | findstr :3000
netstat -an | findstr :8001

# 다른 포트 사용시 docker-compose.yml 수정
```

**환경변수 로드 안됨**
```bash
# .env 파일 위치 확인 (프로젝트 루트에 있어야 함)
# API 키에 특수문자가 있으면 따옴표로 감싸기
OPENAI_API_KEY="sk-..."
```

**빌드 실패**
```bash
# Docker 캐시 클리어
docker system prune -a

# 강제 리빌드
docker-compose build --no-cache
```

### 백엔드 문제

**Python 모듈 찾을 수 없음**
- `backend/requirements.txt`에 모든 필요한 패키지가 포함되어 있는지 확인
- Docker 이미지 재빌드

**API 응답 오류**
- 서울 API 키가 올바른지 확인
- API 사용량 제한 확인
- 네트워크 연결 상태 확인

### 프론트엔드 문제

**API 연결 실패**
- Nginx 설정에서 백엔드 프록시 설정 확인
- CORS 설정 확인
- 네트워크 연결 확인

## 📊 모니터링

### 로그 확인
```bash
# 전체 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 헬스 체크
```bash
# 백엔드 헬스 체크
curl http://localhost:8000/health

# 프론트엔드 접근 확인
curl http://localhost:3000
```

## 🎯 성능 최적화

### 프로덕션 최적화
- 멀티스테이지 빌드 사용 (이미 적용됨)
- 이미지 크기 최소화를 위한 alpine 이미지 사용
- 불필요한 파일 제외를 위한 .dockerignore 설정

### 스케일링
```bash
# 서비스 복제
docker-compose up --scale backend=3 --scale frontend=2
```

## 🔐 보안 고려사항

1. **환경변수 보안**
   - `.env` 파일을 Git에 커밋하지 마세요
   - 프로덕션에서는 시크릿 관리 서비스 사용

2. **네트워크 보안**
   - HTTPS 설정
   - 방화벽 규칙 적용
   - API 키 로테이션

3. **컨테이너 보안**
   - 최신 베이스 이미지 사용
   - 취약점 스캔 실행
   - 최소 권한 원칙 적용 