# 🌐 도메인 설정 가이드

## 1. 🆓 무료 도메인 서비스

### Freenom (무료 도메인)
- **도메인**: .tk, .ml, .ga, .cf 등
- **가격**: 무료
- **사이트**: https://freenom.com
- **예시**: commutecare.tk

### Duck DNS (무료 서브도메인)
- **도메인**: xxx.duckdns.org
- **가격**: 무료
- **사이트**: https://duckdns.org
- **예시**: commutecare.duckdns.org

## 2. 💰 유료 도메인 서비스

### 한국 도메인 (.kr)
- **가비아**: https://domain.gabia.com
- **후이즈**: https://whois.co.kr
- **가격**: 연간 20,000원~30,000원

### 해외 도메인 (.com, .net)
- **Namecheap**: https://namecheap.com
- **Google Domains**: https://domains.google
- **가격**: 연간 $10~$15

## 3. 🔧 DNS 설정

### A 레코드 설정
```
Type: A
Name: @
Value: YOUR_PUBLIC_IP
TTL: 300
```

### 서브도메인 설정
```
Type: A
Name: api
Value: YOUR_PUBLIC_IP
TTL: 300
```

## 4. 🚀 배포 후 설정

### Docker Compose 업데이트
```bash
# 환경변수 추가
DOMAIN_NAME=commutecare.tk
API_URL=http://commutecare.tk/api
```

### Nginx 설정 업데이트
```nginx
server_name commutecare.tk www.commutecare.tk;
```

## 5. 🔒 SSL/HTTPS 설정

### Let's Encrypt (무료 SSL)
```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d commutecare.tk -d www.commutecare.tk
```

### 자동 갱신 설정
```bash
# 크론탭 설정
sudo crontab -e

# 매달 1일 오전 2시에 갱신
0 2 1 * * /usr/bin/certbot renew --quiet
```

## 6. 📱 최종 결과

### Before
```
❌ http://123.45.67.89:3000
❌ http://123.45.67.89:8000/docs
```

### After
```
✅ https://commutecare.tk
✅ https://commutecare.tk/docs
✅ https://commutecare.tk/health
```

## 7. 🌟 권장 설정

### 도메인 구매 순서
1. **Duck DNS** (무료, 즉시 사용)
2. **Freenom** (무료, 실제 도메인)
3. **Namecheap** (유료, 안정적)

### DNS 설정 예시
```
# Main domain
commutecare.tk → YOUR_PUBLIC_IP

# API subdomain (선택사항)
api.commutecare.tk → YOUR_PUBLIC_IP

# WWW subdomain
www.commutecare.tk → YOUR_PUBLIC_IP
```

## 8. 🔄 적용 방법

### 1단계: 도메인 구매
- Duck DNS 또는 Freenom에서 도메인 획득

### 2단계: DNS 설정
- A 레코드에 서버 IP 추가

### 3단계: Docker 재배포
```bash
# 환경변수 설정
echo "DOMAIN_NAME=commutecare.tk" >> .env

# 서비스 재시작
./deploy-fast.sh -a -s
```

### 4단계: SSL 설정 (선택사항)
```bash
# Let's Encrypt 설정
sudo certbot --nginx -d commutecare.tk
```

---

**💡 추천**: 개발/테스트 단계에서는 **Duck DNS**를 사용하고, 운영 단계에서는 **유료 도메인**을 사용하세요. 