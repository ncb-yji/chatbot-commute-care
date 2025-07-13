#!/bin/bash

# 카카오 클라우드 배포 스크립트
# 사용법: ./kakao-cloud-deploy.sh [build|deploy|all]

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 설정 변수
REGISTRY="kr.icr.io/kakao-cloud"  # 카카오 클라우드 컨테이너 레지스트리
NAMESPACE="commute-care"
BACKEND_IMAGE="${REGISTRY}/commute-care-backend"
FRONTEND_IMAGE="${REGISTRY}/commute-care-frontend"
VERSION=$(date +%Y%m%d%H%M%S)

ACTION=${1:-all}

echo -e "${GREEN}🚀 카카오 클라우드 배포 시작 - 액션: ${ACTION}${NC}"

# 1. 컨테이너 이미지 빌드 및 푸시
build_and_push() {
    echo -e "${YELLOW}🏗️ 컨테이너 이미지 빌드 및 푸시${NC}"
    
    # 백엔드 이미지 빌드
    echo -e "${YELLOW}🔧 백엔드 이미지 빌드${NC}"
    docker build -t ${BACKEND_IMAGE}:${VERSION} -t ${BACKEND_IMAGE}:latest ../backend
    docker push ${BACKEND_IMAGE}:${VERSION}
    docker push ${BACKEND_IMAGE}:latest
    
    # 프론트엔드 이미지 빌드
    echo -e "${YELLOW}🔧 프론트엔드 이미지 빌드${NC}"
    docker build -t ${FRONTEND_IMAGE}:${VERSION} -t ${FRONTEND_IMAGE}:latest ../frontend
    docker push ${FRONTEND_IMAGE}:${VERSION}
    docker push ${FRONTEND_IMAGE}:latest
    
    echo -e "${GREEN}✅ 이미지 빌드 및 푸시 완료${NC}"
}

# 2. 쿠버네티스 배포
deploy_kubernetes() {
    echo -e "${YELLOW}☸️ 쿠버네티스 배포${NC}"
    
    # 시크릿 생성 (API 키가 설정되어 있는지 확인)
    if [ -z "$SEOUL_API_KEY" ] || [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${RED}❌ 환경변수 SEOUL_API_KEY 또는 OPENAI_API_KEY가 설정되지 않았습니다${NC}"
        echo -e "${YELLOW}다음 명령어로 환경변수를 설정하세요:${NC}"
        echo -e "export SEOUL_API_KEY='your_seoul_api_key'"
        echo -e "export OPENAI_API_KEY='your_openai_api_key'"
        exit 1
    fi
    
    # 네임스페이스 생성
    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    
    # 시크릿 생성
    kubectl create secret generic commute-care-secrets \
        --from-literal=seoul-api-key=${SEOUL_API_KEY} \
        --from-literal=openai-api-key=${OPENAI_API_KEY} \
        -n ${NAMESPACE} \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # 배포 YAML 파일 업데이트
    sed -i "s|image: commute-care-backend:latest|image: ${BACKEND_IMAGE}:${VERSION}|g" kakao-cloud-kubernetes.yml
    sed -i "s|image: commute-care-frontend:latest|image: ${FRONTEND_IMAGE}:${VERSION}|g" kakao-cloud-kubernetes.yml
    
    # 쿠버네티스 리소스 배포
    kubectl apply -f kakao-cloud-kubernetes.yml
    
    echo -e "${GREEN}✅ 쿠버네티스 배포 완료${NC}"
}

# 3. 배포 상태 확인
check_deployment() {
    echo -e "${YELLOW}🔍 배포 상태 확인${NC}"
    
    # 팟 상태 확인
    kubectl get pods -n ${NAMESPACE}
    
    # 서비스 상태 확인
    kubectl get services -n ${NAMESPACE}
    
    # 인그레스 상태 확인
    kubectl get ingress -n ${NAMESPACE}
    
    echo -e "${YELLOW}⏳ 팟이 Ready 상태가 될 때까지 대기 중...${NC}"
    kubectl wait --for=condition=ready pod -l app=commute-care-backend -n ${NAMESPACE} --timeout=300s
    kubectl wait --for=condition=ready pod -l app=commute-care-frontend -n ${NAMESPACE} --timeout=300s
    
    echo -e "${GREEN}✅ 모든 팟이 Ready 상태입니다${NC}"
}

# 4. 헬스 체크
health_check() {
    echo -e "${YELLOW}🏥 헬스 체크${NC}"
    
    # 백엔드 헬스 체크
    BACKEND_SERVICE=$(kubectl get service commute-care-backend-service -n ${NAMESPACE} -o jsonpath='{.spec.clusterIP}')
    if kubectl run curl-test --rm -i --restart=Never --image=curlimages/curl -- curl -f http://${BACKEND_SERVICE}:8000/health; then
        echo -e "${GREEN}✅ 백엔드 헬스 체크 성공${NC}"
    else
        echo -e "${RED}❌ 백엔드 헬스 체크 실패${NC}"
    fi
    
    # 프론트엔드 헬스 체크
    FRONTEND_SERVICE=$(kubectl get service commute-care-frontend-service -n ${NAMESPACE} -o jsonpath='{.spec.clusterIP}')
    if kubectl run curl-test --rm -i --restart=Never --image=curlimages/curl -- curl -f http://${FRONTEND_SERVICE}:80; then
        echo -e "${GREEN}✅ 프론트엔드 헬스 체크 성공${NC}"
    else
        echo -e "${RED}❌ 프론트엔드 헬스 체크 실패${NC}"
    fi
}

# 5. 롤백 함수
rollback() {
    echo -e "${YELLOW}🔄 롤백 실행${NC}"
    
    # 이전 버전으로 롤백
    kubectl rollout undo deployment/commute-care-backend -n ${NAMESPACE}
    kubectl rollout undo deployment/commute-care-frontend -n ${NAMESPACE}
    
    echo -e "${GREEN}✅ 롤백 완료${NC}"
}

# 6. 클린업 함수
cleanup() {
    echo -e "${YELLOW}🧹 리소스 정리${NC}"
    
    kubectl delete namespace ${NAMESPACE} --ignore-not-found=true
    
    echo -e "${GREEN}✅ 리소스 정리 완료${NC}"
}

# 메인 실행 로직
case $ACTION in
    build)
        build_and_push
        ;;
    deploy)
        deploy_kubernetes
        check_deployment
        health_check
        ;;
    all)
        build_and_push
        deploy_kubernetes
        check_deployment
        health_check
        ;;
    rollback)
        rollback
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo -e "${RED}❌ 알 수 없는 액션: ${ACTION}${NC}"
        echo -e "${YELLOW}사용법: $0 [build|deploy|all|rollback|cleanup]${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}🎉 카카오 클라우드 배포 작업 완료!${NC}"
echo ""
echo -e "${YELLOW}💡 유용한 명령어:${NC}"
echo -e "  팟 상태 확인: kubectl get pods -n ${NAMESPACE}"
echo -e "  로그 확인: kubectl logs -f deployment/commute-care-backend -n ${NAMESPACE}"
echo -e "  서비스 확인: kubectl get services -n ${NAMESPACE}"
echo -e "  롤백: $0 rollback"
echo -e "  정리: $0 cleanup" 