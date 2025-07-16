#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 도움말 함수
show_help() {
    echo "사용법: ./deploy-fast.sh [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help          도움말 표시"
    echo "  -f, --frontend      프론트엔드만 빌드"
    echo "  -b, --backend       백엔드만 빌드"
    echo "  -a, --all           전체 빌드 (기본값)"
    echo "  -s, --start         빌드 후 시작"
    echo "  -r, --restart       재시작 (빌드 없이)"
    echo "  -d, --down          서비스 중지"
    echo "  -l, --logs          로그 보기"
    echo "  --no-cache          캐시 없이 빌드"
    echo ""
    echo "예시:"
    echo "  ./deploy-fast.sh -f -s    # 프론트엔드만 빌드하고 시작"
    echo "  ./deploy-fast.sh -b       # 백엔드만 빌드"
    echo "  ./deploy-fast.sh -r       # 재시작 (빌드 없이)"
    echo "  ./deploy-fast.sh -l       # 로그 보기"
}

# 기본값 설정
BUILD_FRONTEND=false
BUILD_BACKEND=false
BUILD_ALL=false
START_SERVICES=false
RESTART_SERVICES=false
DOWN_SERVICES=false
SHOW_LOGS=false
NO_CACHE=false
COMPOSE_FILE="docker-compose.prod.yml"

# 인자 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--frontend)
            BUILD_FRONTEND=true
            shift
            ;;
        -b|--backend)
            BUILD_BACKEND=true
            shift
            ;;
        -a|--all)
            BUILD_ALL=true
            shift
            ;;
        -s|--start)
            START_SERVICES=true
            shift
            ;;
        -r|--restart)
            RESTART_SERVICES=true
            shift
            ;;
        -d|--down)
            DOWN_SERVICES=true
            shift
            ;;
        -l|--logs)
            SHOW_LOGS=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            show_help
            exit 1
            ;;
    esac
done

# 기본값 설정 (아무 옵션이 없으면 전체 빌드)
if [ "$BUILD_FRONTEND" = false ] && [ "$BUILD_BACKEND" = false ] && [ "$BUILD_ALL" = false ] && [ "$RESTART_SERVICES" = false ] && [ "$DOWN_SERVICES" = false ] && [ "$SHOW_LOGS" = false ]; then
    BUILD_ALL=true
fi

# 환경 변수 확인
if [ ! -f ".env" ]; then
    log_error ".env 파일이 존재하지 않습니다."
    log_info "SETUP_GUIDE.md를 참고하여 .env 파일을 생성하세요."
    exit 1
fi

# Docker 및 docker-compose 확인
if ! command -v docker &> /dev/null; then
    log_error "Docker가 설치되지 않았습니다."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "docker-compose가 설치되지 않았습니다."
    exit 1
fi

# 서비스 중지
if [ "$DOWN_SERVICES" = true ]; then
    log_info "서비스 중지 중..."
    docker-compose -f $COMPOSE_FILE down
    log_success "서비스가 중지되었습니다."
    exit 0
fi

# 로그 보기
if [ "$SHOW_LOGS" = true ]; then
    log_info "실시간 로그 보기 (Ctrl+C로 종료)"
    docker-compose -f $COMPOSE_FILE logs -f
    exit 0
fi

# 재시작 (빌드 없이)
if [ "$RESTART_SERVICES" = true ]; then
    log_info "서비스 재시작 중..."
    docker-compose -f $COMPOSE_FILE restart
    log_success "서비스가 재시작되었습니다."
    exit 0
fi

# 빌드 옵션 설정
BUILD_ARGS=""
if [ "$NO_CACHE" = true ]; then
    BUILD_ARGS="--no-cache"
fi

# 빌드 시작
START_TIME=$(date +%s)

# 프론트엔드만 빌드
if [ "$BUILD_FRONTEND" = true ]; then
    log_info "프론트엔드 빌드 시작..."
    docker-compose -f $COMPOSE_FILE build $BUILD_ARGS frontend
    if [ $? -eq 0 ]; then
        log_success "프론트엔드 빌드 완료"
    else
        log_error "프론트엔드 빌드 실패"
        exit 1
    fi
fi

# 백엔드만 빌드
if [ "$BUILD_BACKEND" = true ]; then
    log_info "백엔드 빌드 시작..."
    docker-compose -f $COMPOSE_FILE build $BUILD_ARGS backend
    if [ $? -eq 0 ]; then
        log_success "백엔드 빌드 완료"
    else
        log_error "백엔드 빌드 실패"
        exit 1
    fi
fi

# 전체 빌드
if [ "$BUILD_ALL" = true ]; then
    log_info "전체 빌드 시작..."
    docker-compose -f $COMPOSE_FILE build $BUILD_ARGS
    if [ $? -eq 0 ]; then
        log_success "전체 빌드 완료"
    else
        log_error "전체 빌드 실패"
        exit 1
    fi
fi

# 빌드 시간 계산
END_TIME=$(date +%s)
BUILD_TIME=$((END_TIME - START_TIME))
log_info "빌드 시간: ${BUILD_TIME}초"

# 서비스 시작
if [ "$START_SERVICES" = true ]; then
    log_info "서비스 시작 중..."
    docker-compose -f $COMPOSE_FILE up -d
    if [ $? -eq 0 ]; then
        log_success "서비스가 시작되었습니다."
        log_info "접속 주소:"
        log_info "  - 프론트엔드: http://localhost:3000"
        log_info "  - 백엔드 API: http://localhost:8000"
        log_info "  - API 문서: http://localhost:8000/docs"
        log_info ""
        log_info "로그 확인: ./deploy-fast.sh -l"
        log_info "서비스 중지: ./deploy-fast.sh -d"
    else
        log_error "서비스 시작 실패"
        exit 1
    fi
fi

log_success "작업이 완료되었습니다!" 