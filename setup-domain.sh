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
    echo "사용법: ./setup-domain.sh [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help          도움말 표시"
    echo "  -d, --domain DOMAIN 도메인 이름 설정"
    echo "  -p, --port-only     포트만 숨김 (80포트 사용)"
    echo "  -r, --reverse-proxy 리버스 프록시 설정"
    echo "  -s, --ssl           SSL 인증서 설정"
    echo "  --duck-dns          Duck DNS 설정"
    echo ""
    echo "예시:"
    echo "  ./setup-domain.sh -p              # 포트만 숨김"
    echo "  ./setup-domain.sh -d example.com  # 도메인 설정"
    echo "  ./setup-domain.sh -d example.com -s  # 도메인 + SSL"
    echo "  ./setup-domain.sh --duck-dns       # Duck DNS 설정"
}

# 기본값 설정
DOMAIN_NAME=""
PORT_ONLY=false
REVERSE_PROXY=false
SSL_ENABLED=false
DUCK_DNS=false

# 인자 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--domain)
            DOMAIN_NAME="$2"
            shift 2
            ;;
        -p|--port-only)
            PORT_ONLY=true
            shift
            ;;
        -r|--reverse-proxy)
            REVERSE_PROXY=true
            shift
            ;;
        -s|--ssl)
            SSL_ENABLED=true
            shift
            ;;
        --duck-dns)
            DUCK_DNS=true
            shift
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            show_help
            exit 1
            ;;
    esac
done

# 1. 포트만 숨김 설정
if [ "$PORT_ONLY" = true ]; then
    log_info "포트 숨김 설정 시작..."
    
    # docker-compose.prod.yml 포트 변경
    sed -i 's/- "3000:80"/- "80:80"/' docker-compose.prod.yml
    
    log_success "포트 숨김 설정 완료!"
    log_info "이제 http://YOUR-IP 로 접속 가능합니다."
    
    # 서비스 재시작
    ./deploy-fast.sh -f -s
    exit 0
fi

# 2. Duck DNS 설정
if [ "$DUCK_DNS" = true ]; then
    log_info "Duck DNS 설정 시작..."
    
    echo "Duck DNS 설정을 위해 다음 단계를 수행하세요:"
    echo "1. https://duckdns.org 접속"
    echo "2. 로그인 후 원하는 서브도메인 등록"
    echo "3. 아래에 도메인 이름을 입력하세요 (예: commutecare.duckdns.org)"
    
    read -p "Duck DNS 도메인 이름: " DOMAIN_NAME
    
    if [ -z "$DOMAIN_NAME" ]; then
        log_error "도메인 이름을 입력해주세요."
        exit 1
    fi
    
    log_info "Duck DNS 설정: $DOMAIN_NAME"
fi

# 3. 도메인 설정
if [ ! -z "$DOMAIN_NAME" ]; then
    log_info "도메인 설정 시작: $DOMAIN_NAME"
    
    # .env 파일에 도메인 추가
    if grep -q "DOMAIN_NAME=" .env; then
        sed -i "s/DOMAIN_NAME=.*/DOMAIN_NAME=$DOMAIN_NAME/" .env
    else
        echo "DOMAIN_NAME=$DOMAIN_NAME" >> .env
    fi
    
    # 리버스 프록시 또는 SSL 설정
    if [ "$SSL_ENABLED" = true ]; then
        log_info "SSL 설정 시작..."
        
        # SSL 디렉토리 생성
        mkdir -p ssl/certs ssl/www
        
        # SSL 인증서 발급
        log_info "SSL 인증서 발급 중..."
        docker run --rm -v "$(pwd)/ssl/certs:/etc/letsencrypt" -v "$(pwd)/ssl/www:/var/www/certbot" certbot/certbot certonly --webroot --webroot-path=/var/www/certbot --email admin@$DOMAIN_NAME --agree-tos --non-interactive -d $DOMAIN_NAME
        
        if [ $? -eq 0 ]; then
            log_success "SSL 인증서 발급 완료!"
            
            # SSL 환경 설정
            echo "SSL_ENABLED=true" >> .env
            
            # SSL Docker Compose 실행
            log_info "SSL 환경으로 서비스 시작..."
            docker-compose -f docker-compose.ssl.yml up -d --build
            
            log_success "SSL 설정 완료!"
            log_info "접속 주소: https://$DOMAIN_NAME"
            
        else
            log_error "SSL 인증서 발급 실패"
            exit 1
        fi
        
    elif [ "$REVERSE_PROXY" = true ]; then
        log_info "리버스 프록시 설정 시작..."
        
        # 리버스 프록시 환경 설정
        echo "REVERSE_PROXY=true" >> .env
        
        # 프론트엔드 Nginx 설정 복사
        cp nginx.conf frontend/nginx.conf
        
        # 서비스 재시작
        ./deploy-fast.sh -a -s
        
        log_success "리버스 프록시 설정 완료!"
        log_info "접속 주소: http://$DOMAIN_NAME"
        log_info "API 문서: http://$DOMAIN_NAME/docs"
        
    else
        log_info "기본 도메인 설정 시작..."
        
        # 포트 80으로 변경
        sed -i 's/- "3000:80"/- "80:80"/' docker-compose.prod.yml
        
        # 서비스 재시작
        ./deploy-fast.sh -a -s
        
        log_success "도메인 설정 완료!"
        log_info "접속 주소: http://$DOMAIN_NAME"
    fi
    
    log_success "모든 설정이 완료되었습니다!"
    
    # 최종 확인
    log_info "설정 확인 중..."
    sleep 5
    
    if [ "$SSL_ENABLED" = true ]; then
        curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN_NAME
    else
        curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN_NAME
    fi
    
    if [ $? -eq 0 ]; then
        log_success "서비스가 정상적으로 실행 중입니다!"
    else
        log_warning "서비스 확인에 실패했습니다. 수동으로 확인해주세요."
    fi
    
else
    log_warning "도메인 이름이 설정되지 않았습니다."
    log_info "사용법: ./setup-domain.sh -d your-domain.com"
fi

# 설정 요약 출력
log_info "=== 설정 요약 ==="
if [ "$PORT_ONLY" = true ]; then
    echo "✅ 포트 숨김: http://YOUR-IP"
elif [ ! -z "$DOMAIN_NAME" ]; then
    echo "✅ 도메인: $DOMAIN_NAME"
    if [ "$SSL_ENABLED" = true ]; then
        echo "✅ SSL: https://$DOMAIN_NAME"
    else
        echo "✅ HTTP: http://$DOMAIN_NAME"
    fi
    if [ "$REVERSE_PROXY" = true ]; then
        echo "✅ 리버스 프록시: $DOMAIN_NAME/api"
    fi
fi

log_info "설정이 완료되었습니다! 🎉" 