# AegisScan — Production Deployment Guide

This guide details how to deploy AegisScan in production environments safely and securely.

---

## 1. Prerequisites

- **Docker Engine** (v24.0+) and **Docker Compose** (v2.20+)
- **Domain Name** pointing to your server's public IP (e.g., `aegisscan.example.com`)
- **TLS Certificate** (e.g., Let's Encrypt / Certbot or reverse proxy termination)
- Minimum System Specifications:
  - 2 vCPU cores
  - 4 GB RAM
  - 20 GB Disk Space (for reports and scanner evidence)

---

## 2. Environment Configuration

1. Clone repository to your production host:
   ```bash
   git clone https://github.com/Garvittt-API/Aegis-Scan.git
   cd Aegis-Scan
   ```

2. Copy the sample environment file and generate a production secret key:
   ```bash
   cp .env.example .env
   ```

3. Update `.env` with strong production credentials:
   ```ini
   APP_ENV=production
   ENVIRONMENT=production
   DEBUG=false

   # Generate strong random key: openssl rand -hex 32
   SECRET_KEY=e8c459b71891d4e02a90184b2efc829104bce9204821a89c8392019482019482
   
   # PostgreSQL Connection
   DATABASE_URL=postgresql://aegis:CHANGE_TO_STRONG_PASSWORD@db:5432/aegisscan
   DB_PASSWORD=CHANGE_TO_STRONG_PASSWORD

   # CORS Domain Configuration
   CORS_ORIGINS=["https://aegisscan.example.com"]
   FRONTEND_URL=https://aegisscan.example.com

   # Disable scanning private IPs in public SaaS deployments
   ALLOW_PRIVATE_TARGETS=false

   # Concurrency bounds
   MAX_CONCURRENT_SCANS=5
   MAX_SCAN_TIMEOUT_SECONDS=300
   ```

---

## 3. Docker Deployment (Recommended)

Run the multi-container stack (Backend + Database + Persistence):

```bash
# Build and start containers in the background
docker-compose up -d --build

# Verify container health status
docker-compose ps
```

Verify backend logs:
```bash
docker-compose logs -f aegisscan
```

---

## 4. HTTPS & Reverse Proxy Setup (Nginx)

For TLS termination and HTTP->HTTPS redirection, you can use the provided `nginx.conf`:

```bash
# Install Certbot and obtain Let's Encrypt certificates
sudo apt update && sudo apt install -y certbot python3-certbot-nginx
sudo certbot certonly --standalone -d aegisscan.example.com
```

Link certificate files to `/etc/nginx/certs/`:
- `fullchain.pem` -> `/etc/letsencrypt/live/aegisscan.example.com/fullchain.pem`
- `privkey.pem` -> `/etc/letsencrypt/live/aegisscan.example.com/privkey.pem`

Start Nginx:
```bash
sudo nginx -t && sudo systemctl restart nginx
```

---

## 5. Health & Verification

Verify the live deployment:

```bash
# 1. Liveness probe
curl -i https://aegisscan.example.com/health

# 2. Readiness probe (checks DB and storage writeability)
curl -i https://aegisscan.example.com/health/ready
```

Expected output:
```json
{
  "status": "ready",
  "database": "ready",
  "storage": "ready",
  "environment": "production"
}
```

---

## 6. Initial Administrator Setup

Upon initial deployment, the first account registered via `/api/auth/register` is automatically granted Administrator privileges:

```bash
curl -X POST https://aegisscan.example.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "StrongAdminPassword123!",
    "full_name": "Lead Security Officer"
  }'
```
