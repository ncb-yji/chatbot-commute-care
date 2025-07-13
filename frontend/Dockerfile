# 1단계: React 빌드
FROM node:18-alpine as build

WORKDIR /app

# 의존성 파일 복사
COPY package*.json ./

# 의존성 설치
RUN npm install

# 소스 코드 복사
COPY . .

# React 앱 빌드
RUN npm run build

# 빌드 결과 확인
RUN ls -la build/

# 2단계: Nginx로 서빙
FROM nginx:alpine

# React 빌드 파일 복사
COPY --from=build /app/build /usr/share/nginx/html

# Nginx 설정 복사
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 포트 노출
EXPOSE 80

# Nginx 실행
CMD ["nginx", "-g", "daemon off;"]