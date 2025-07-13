#!/bin/bash

# Ubuntu 서버에 Docker 애플리케이션 배포 스크립트
# 사용법: ./ubuntu-deploy.sh [production|staging]

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 환경 변수 설정
ENVIRONMENT=${1:-production}
APP_NAME="commute-care"
DEPLOY_DIR="/opt/${APP_NAME}"
BACKUP_DIR="/opt/${APP_NAME}_backup_$(date +%Y%m%d_%H%M%S)"

echo -e "${GREEN}🚀 Commute Care 애플리케이션 배포 시작 - 환경: ${ENVIRONMENT}${NC}"

# 1. 시스템 업데이트 및 Docker 설치 확인
echo -e "${YELLOW}📦 시스템 업데이트 및 Docker 설치 확인${NC}"
sudo apt-get update

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}🐳 Docker 설치 중...${NC}"
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
fi

# Docker Compose 설치 확인
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}🐳 Docker Compose 설치 중...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 2. 기존 서비스 중지 및 백업
if [ -d "${DEPLOY_DIR}" ]; then
    echo -e "${YELLOW}🔄 기존 서비스 중지 및 백업${NC}"
    cd ${DEPLOY_DIR}
    docker-compose down || true
    sudo cp -r ${DEPLOY_DIR} ${BACKUP_DIR}
    echo -e "${GREEN}✅ 백업 완료: ${BACKUP_DIR}${NC}"
fi

# 3. 배포 디렉토리 생성
echo -e "${YELLOW}📁 배포 디렉토리 설정${NC}"
sudo mkdir -p ${DEPLOY_DIR}
sudo chown -R $USER:$USER ${DEPLOY_DIR}

# 4. 소스 코드 배포 (Git 또는 파일 복사)
echo -e "${YELLOW}📥 소스 코드 배포${NC}"
cd ${DEPLOY_DIR}

# Git에서 클론 (여기서는 현재 디렉토리에서 복사)
cp -r $(dirname $0)/../* .

# 5. 환경 파일 설정
echo -e "${YELLOW}⚙️ 환경 설정${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${RED}❗ .env 파일을 확인하고 실제 API 키를 입력하세요${NC}"
    read -p "계속하려면 Enter를 누르세요..."
fi

# 6. 방화벽 설정
echo -e "${YELLOW}🔥 방화벽 설정${NC}"
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable

# 7. Docker 빌드 및 실행
echo -e "${YELLOW}🏗️ Docker 이미지 빌드 및 컨테이너 실행${NC}"
docker-compose down || true
docker-compose build --no-cache
docker-compose up -d

# 8. 서비스 상태 확인
echo -e "${YELLOW}🔍 서비스 상태 확인${NC}"
sleep 30

# 백엔드 헬스 체크
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 백엔드 서비스 정상 작동${NC}"
else
    echo -e "${RED}❌ 백엔드 서비스 오류${NC}"
    docker-compose logs backend
fi

# 프론트엔드 확인
if curl -f http://localhost:80 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 프론트엔드 서비스 정상 작동${NC}"
else
    echo -e "${RED}❌ 프론트엔드 서비스 오류${NC}"
    docker-compose logs frontend
fi

# 9. 자동 시작 설정
echo -e "${YELLOW}🔄 부팅시 자동 시작 설정${NC}"
sudo tee /etc/systemd/system/commute-care.service > /dev/null <<EOF
[Unit]
Description=Commute Care Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${DEPLOY_DIR}
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable commute-care.service

# 10. 로그 로테이션 설정
echo -e "${YELLOW}📄 로그 로테이션 설정${NC}"
sudo tee /etc/logrotate.d/commute-care > /dev/null <<EOF
${DEPLOY_DIR}/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF

# 11. 모니터링 스크립트 설정
echo -e "${YELLOW}📊 모니터링 스크립트 설정${NC}"
sudo tee /usr/local/bin/commute-care-monitor.sh > /dev/null <<EOF
#!/bin/bash
cd ${DEPLOY_DIR}
if ! docker-compose ps | grep -q "Up"; then
    echo "Service is down, restarting..."
    docker-compose up -d
fi
EOF

sudo chmod +x /usr/local/bin/commute-care-monitor.sh

# 크론탭에 모니터링 추가 (5분마다 확인)
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/commute-care-monitor.sh") | crontab -

echo -e "${GREEN}🎉 배포 완료!${NC}"
echo -e "${GREEN}📱 프론트엔드: http://$(hostname -I | awk '{print $1}')${NC}"
echo -e "${GREEN}🔗 백엔드 API: http://$(hostname -I | awk '{print $1}'):8000${NC}"
echo -e "${GREEN}📚 API 문서: http://$(hostname -I | awk '{print $1}'):8000/docs${NC}"
echo ""
echo -e "${YELLOW}💡 유용한 명령어:${NC}"
echo -e "  서비스 상태 확인: docker-compose ps"
echo -e "  로그 확인: docker-compose logs -f"
echo -e "  서비스 재시작: docker-compose restart"
echo -e "  서비스 중지: docker-compose down"
echo -e "  시스템 서비스 상태: sudo systemctl status commute-care" 