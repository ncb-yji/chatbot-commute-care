# 🚀 배포 설정 및 스크립트

이 디렉토리에는 다양한 클라우드 환경에 Commute Care 애플리케이션을 배포하기 위한 설정 파일과 스크립트가 포함되어 있습니다.

## 📁 파일 구조

```
deploy/
├── kakao-cloud.yml              # 카카오 클라우드용 Docker Compose 설정
├── kakao-cloud-kubernetes.yml   # 카카오 클라우드 Kubernetes 배포 설정
├── kakao-cloud-deploy.sh        # 카카오 클라우드 배포 스크립트
├── ubuntu-deploy.sh             # Ubuntu 서버 배포 스크립트
└── README.md                    # 이 파일
```

## 🎯 사용 목적별 선택 가이드

### 1. 로컬 개발 환경
- **파일**: `../docker-compose.yml`
- **용도**: 개발 및 테스트
- **명령어**: `docker-compose up --build`

### 2. 카카오 클라우드 배포
- **Docker Compose**: `kakao-cloud.yml`
- **Kubernetes**: `kakao-cloud-kubernetes.yml` + `kakao-cloud-deploy.sh`
- **특징**: 한국 리전 최적화, 높은 성능

### 3. Ubuntu 서버 배포
- **파일**: `ubuntu-deploy.sh`
- **용도**: 자체 서버 또는 VPS
- **특징**: 자동 설치, 모니터링, 백업

## 📋 배포 전 준비사항

### 1. API 키 준비
```bash
# 환경변수 설정
export SEOUL_API_KEY='your_seoul_api_key'
export OPENAI_API_KEY='your_openai_api_key'
```

### 2. Docker 및 필수 도구 설치
```bash
# Docker 설치 (Ubuntu 기준)
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# kubectl 설치 (Kubernetes 배포시)
curl -LO "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

## 🚀 배포 방법

### 카카오 클라우드 - Docker Compose
```bash
cd deploy
docker-compose -f kakao-cloud.yml up -d --build
```

### 카카오 클라우드 - Kubernetes
```bash
cd deploy
chmod +x kakao-cloud-deploy.sh
./kakao-cloud-deploy.sh all
```

### Ubuntu 서버
```bash
cd deploy
chmod +x ubuntu-deploy.sh
./ubuntu-deploy.sh production
```

## 🔧 트러블슈팅

### 권한 오류
```bash
# 스크립트 실행 권한 부여
chmod +x *.sh
```

### 환경변수 누락
```bash
# .env 파일 생성
cp ../.env.example .env
# 실제 API 키 입력 후 저장
```

### 포트 충돌
```bash
# 사용 중인 포트 확인
netstat -tlnp | grep :8000
netstat -tlnp | grep :80
```

## 📊 모니터링

### 로그 확인
```bash
# Docker Compose
docker-compose logs -f

# Kubernetes
kubectl logs -f deployment/commute-care-backend -n commute-care
```

### 상태 확인
```bash
# Docker Compose
docker-compose ps

# Kubernetes
kubectl get pods -n commute-care
```

## 🔄 업데이트 및 롤백

### 업데이트
```bash
# 새 버전 배포
./kakao-cloud-deploy.sh all

# Ubuntu 서버 업데이트
./ubuntu-deploy.sh production
```

### 롤백
```bash
# Kubernetes 롤백
./kakao-cloud-deploy.sh rollback

# Ubuntu 서버 롤백 (수동)
sudo systemctl stop commute-care
sudo cp -r /opt/commute-care_backup_* /opt/commute-care
sudo systemctl start commute-care
```

## 🔐 보안 고려사항

1. **API 키 관리**
   - 환경변수로 관리
   - Kubernetes Secret 사용
   - 정기적 로테이션

2. **네트워크 보안**
   - 방화벽 설정
   - HTTPS 적용
   - 불필요한 포트 차단

3. **접근 제어**
   - kubectl 접근 권한 관리
   - 서버 SSH 키 관리
   - 로그 모니터링

## 💡 최적화 팁

1. **성능 최적화**
   - 컨테이너 리소스 제한 설정
   - 로드 밸런싱 구성
   - 캐싱 활용

2. **비용 최적화**
   - 자동 스케일링 설정
   - 개발 환경 자동 종료
   - 로그 로테이션 설정

3. **운영 최적화**
   - 헬스 체크 강화
   - 모니터링 대시보드 구성
   - 자동 백업 설정 