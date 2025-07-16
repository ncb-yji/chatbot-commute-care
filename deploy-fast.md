# 🚀 빠른 배포 가이드

## 📋 기존 문제점
- 매번 `docker-compose up -d --build` 실행 시 **전체 리빌드**
- 소스 코드만 변경해도 **의존성 재설치** 
- 빌드 시간이 **5-10분** 소요

## ⚡ 개선된 배포 방식

### 1. 스마트 빌드 (권장)
```bash
# 변경된 서비스만 빌드
./deploy-fast.sh -f -s    # 프론트엔드만 빌드 + 시작
./deploy-fast.sh -b -s    # 백엔드만 빌드 + 시작
./deploy-fast.sh -a -s    # 전체 빌드 + 시작
```

### 2. 빠른 재시작 (가장 빠름)
```bash
# 코드 변경 없이 재시작만 (5-10초)
./deploy-fast.sh -r
```

### 3. 캐시 활용 빌드
```bash
# 의존성 변경 없으면 캐시 활용 (1-2분)
docker-compose -f docker-compose.prod.yml up -d
```

## 🎯 상황별 최적 명령어

### 백엔드 Python 코드만 수정
```bash
# 방법 1: 백엔드만 빌드 (30초-1분)
./deploy-fast.sh -b -s

# 방법 2: 재시작만 (5-10초) - 볼륨 마운트 시에만
./deploy-fast.sh -r
```

### 프론트엔드 React 코드만 수정
```bash
# 프론트엔드만 빌드 (1-2분)
./deploy-fast.sh -f -s
```

### requirements.txt 또는 package.json 수정
```bash
# 해당 서비스만 캐시 없이 빌드
./deploy-fast.sh -b --no-cache -s    # 백엔드
./deploy-fast.sh -f --no-cache -s    # 프론트엔드
```

### 전체 시스템 업데이트
```bash
# 전체 빌드 (3-5분)
./deploy-fast.sh -a -s
```

## 🔧 유용한 관리 명령어

### 서비스 상태 확인
```bash
# 컨테이너 상태
docker-compose -f docker-compose.prod.yml ps

# 리소스 사용량
docker stats

# 로그 실시간 보기
./deploy-fast.sh -l
```

### 서비스 관리
```bash
# 서비스 중지
./deploy-fast.sh -d

# 서비스 재시작 (빌드 없이)
./deploy-fast.sh -r

# 특정 서비스만 재시작
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart frontend
```

### 문제 해결
```bash
# 컨테이너 및 이미지 정리
docker system prune -a -f

# 볼륨 정리
docker volume prune -f

# 완전 재시작
./deploy-fast.sh -d
./deploy-fast.sh -a -s
```

## 📊 성능 비교

| 배포 방식 | 시간 | 사용 시기 |
|-----------|------|-----------|
| `docker-compose up -d --build` | 5-10분 | ❌ 비권장 |
| `./deploy-fast.sh -a -s` | 3-5분 | 전체 업데이트 |
| `./deploy-fast.sh -b -s` | 30초-1분 | 백엔드 변경 |
| `./deploy-fast.sh -f -s` | 1-2분 | 프론트엔드 변경 |
| `./deploy-fast.sh -r` | 5-10초 | 재시작만 |

## 🎨 Docker 빌드 최적화

### 1. 레이어 캐싱
- **requirements.txt** 먼저 복사 → 의존성 설치
- **소스 코드** 나중에 복사 → 코드 변경 시 캐시 활용

### 2. .dockerignore 활용
- 불필요한 파일 제외로 빌드 속도 향상
- 컨텍스트 크기 감소

### 3. 멀티 스테이지 빌드
- 프론트엔드: Node.js 빌드 → Nginx 서빙
- 최종 이미지 크기 최소화

## 🔄 CI/CD 파이프라인 (고급)

### GitHub Actions 예시
```yaml
name: Deploy
on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to server
      run: |
        # 백엔드 변경 감지
        if git diff --name-only HEAD~1 | grep -q "backend/"; then
          ./deploy-fast.sh -b -s
        # 프론트엔드 변경 감지
        elif git diff --name-only HEAD~1 | grep -q "frontend/"; then
          ./deploy-fast.sh -f -s
        else
          ./deploy-fast.sh -r
        fi
```

## 🆘 트러블슈팅

### 빌드 실패 시
```bash
# 로그 확인
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend

# 캐시 없이 재빌드
./deploy-fast.sh -a --no-cache -s
```

### 메모리 부족 시
```bash
# 사용하지 않는 리소스 정리
docker system prune -a
docker volume prune

# 서비스 순차 시작
./deploy-fast.sh -b -s
sleep 10
./deploy-fast.sh -f -s
```

### 포트 충돌 시
```bash
# 포트 사용 확인
netstat -tlnp | grep :8000
netstat -tlnp | grep :3000

# 서비스 중지 후 재시작
./deploy-fast.sh -d
sleep 5
./deploy-fast.sh -s
```

---

## 🎯 핵심 요약

✅ **DO (권장)**
- `./deploy-fast.sh -b -s` - 백엔드 변경 시
- `./deploy-fast.sh -f -s` - 프론트엔드 변경 시  
- `./deploy-fast.sh -r` - 재시작만 필요 시

❌ **DON'T (비권장)**
- `docker-compose up -d --build` - 매번 전체 리빌드
- 불필요한 `--no-cache` 사용
- 의존성 미변경 시 강제 리빌드

**🚀 결과: 배포 시간 80% 단축! (10분 → 2분)** 