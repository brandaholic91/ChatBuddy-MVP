# Chatbuddy MVP Deployment Útmutató

## Áttekintés

Ez a dokumentum részletes útmutatót nyújt a Chatbuddy MVP telepítéséhez különböző környezetekben.

## Előfeltételek

### Rendszer Követelmények

- **Python**: 3.11+
- **RAM**: Minimum 2GB, ajánlott 4GB+
- **Tárhely**: Minimum 10GB szabad hely
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows 10+

### Szükséges Szolgáltatások

- **Supabase**: PostgreSQL adatbázis + pgvector
- **Redis**: Cache és session storage
- **OpenAI API**: GPT-4o modell hozzáférés
- **Anthropic API**: Claude-3-5-sonnet hozzáférés (opcionális)

## Lokális Fejlesztési Környezet

### 1. Klónozás és Beállítás

```bash
# Repository klónozása
git clone https://github.com/your-org/chatbuddy-mvp.git
cd chatbuddy-mvp

# Python környezet létrehozása
python -m venv venv
source venv/bin/activate  # Linux/Mac
# vagy
venv\Scripts\activate     # Windows

# Függőségek telepítése
pip install -r requirements.txt
```

### 2. Környezeti Változók Beállítása

```bash
# Környezeti változók másolása
cp .env_example .env

# .env fájl szerkesztése
nano .env
```

**Kötelező beállítások:**
```bash
# AI Provider Settings
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key

# Application Settings
SECRET_KEY=your_secret_key_here
```

### 3. Adatbázis Beállítása

#### Supabase Setup

1. **Projekt létrehozása**: [supabase.com](https://supabase.com)
2. **pgvector extension engedélyezése**:
```sql
-- Supabase SQL Editor-ben
CREATE EXTENSION IF NOT EXISTS vector;
```

3. **Táblák létrehozása**:
```sql
-- Users tábla
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Products tábla
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    category VARCHAR,
    embedding vector(1536),
    available BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Orders tábla
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    status VARCHAR DEFAULT 'pending',
    total DECIMAL(10,2),
    items JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat sessions tábla
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR UNIQUE NOT NULL,
    messages JSONB DEFAULT '[]',
    agent_state JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 4. Redis Beállítása

#### Lokális Redis

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Windows
# Töltsd le a Redis Windows verzióját
```

#### Docker Redis

```bash
# Redis container indítása
docker run -d --name redis-chatbuddy \
  -p 6379:6379 \
  redis:7-alpine redis-server --requirepass your_password
```

### 5. Alkalmazás Indítása

```bash
# Fejlesztői mód
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production mód
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Docker Deployment

### 1. Docker Image Build

```bash
# Image buildelése
docker build -t chatbuddy-mvp:latest .

# Image tesztelése
docker run -p 8000:8000 --env-file .env chatbuddy-mvp:latest
```

### 2. Docker Compose Deployment

```bash
# Környezeti változók beállítása
cp .env_example .env
# Szerkeszd a .env fájlt

# Szolgáltatások indítása
docker-compose up -d

# Logok megtekintése
docker-compose logs -f chatbuddy-api
```

### 3. Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  chatbuddy-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    restart: unless-stopped
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## Cloud Deployment

### Heroku

#### 1. Heroku CLI Setup

```bash
# Heroku CLI telepítése
curl https://cli-assets.heroku.com/install.sh | sh

# Bejelentkezés
heroku login

# App létrehozása
heroku create chatbuddy-mvp
```

#### 2. Heroku Config

```bash
# Környezeti változók beállítása
heroku config:set OPENAI_API_KEY=your_key
heroku config:set SUPABASE_URL=your_url
heroku config:set SUPABASE_ANON_KEY=your_key
heroku config:set SECRET_KEY=your_secret

# Redis addon hozzáadása
heroku addons:create heroku-redis:hobby-dev
```

#### 3. Deployment

```bash
# Git repository beállítása
heroku git:remote -a chatbuddy-mvp

# Deploy
git push heroku main
```

### Railway

#### 1. Railway Setup

```bash
# Railway CLI telepítése
npm install -g @railway/cli

# Bejelentkezés
railway login

# Projekt inicializálása
railway init
```

#### 2. Railway Config

```bash
# Környezeti változók beállítása
railway variables set OPENAI_API_KEY=your_key
railway variables set SUPABASE_URL=your_url
railway variables set SECRET_KEY=your_secret
```

#### 3. Deployment

```bash
# Deploy
railway up
```

### DigitalOcean App Platform

#### 1. App Spec YAML

```yaml
# .do/app.yaml
name: chatbuddy-mvp
services:
- name: web
  source_dir: /
  github:
    repo: your-org/chatbuddy-mvp
    branch: main
  run_command: uvicorn src.main:app --host 0.0.0.0 --port $PORT
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: OPENAI_API_KEY
    value: ${OPENAI_API_KEY}
  - key: SUPABASE_URL
    value: ${SUPABASE_URL}
  - key: SECRET_KEY
    value: ${SECRET_KEY}
```

#### 2. Deployment

```bash
# DigitalOcean CLI telepítése
doctl apps create --spec .do/app.yaml
```

## Production Környezet

### 1. Nginx Konfiguráció

```nginx
# /etc/nginx/sites-available/chatbuddy
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2. Systemd Service

```ini
# /etc/systemd/system/chatbuddy.service
[Unit]
Description=Chatbuddy MVP API
After=network.target

[Service]
Type=exec
User=chatbuddy
WorkingDirectory=/opt/chatbuddy
Environment=PATH=/opt/chatbuddy/venv/bin
ExecStart=/opt/chatbuddy/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. SSL/TLS Beállítás

```bash
# Certbot telepítése
sudo apt-get install certbot python3-certbot-nginx

# SSL tanúsítvány kérése
sudo certbot --nginx -d your-domain.com

# Automatikus megújítás
sudo crontab -e
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring és Logging

### 1. Health Check Endpoint

```python
# src/main.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "services": {
            "database": "connected",
            "redis": "connected",
            "ai_models": "available"
        }
    }
```

### 2. Logging Beállítás

```python
# src/config/logging.py
def setup_production_logging():
    setup_logging(
        log_level="INFO",
        logfire_token=os.getenv("LOGFIRE_TOKEN"),
        enable_file=True,
        log_file="/var/log/chatbuddy/app.log"
    )
```

### 3. Monitoring

```bash
# Prometheus konfiguráció
# /etc/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'chatbuddy'
    static_configs:
      - targets: ['localhost:8000']
```

## Backup és Recovery

### 1. Adatbázis Backup

```bash
# Supabase backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL > backup_$DATE.sql
gzip backup_$DATE.sql
```

### 2. Redis Backup

```bash
# Redis backup
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb backup_redis_$(date +%Y%m%d).rdb
```

## Troubleshooting

### Gyakori Hibák

#### 1. Adatbázis Kapcsolat

```bash
# Kapcsolat tesztelése
python -c "
import os
from supabase import create_client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')
client = create_client(url, key)
print('Connection successful')
"
```

#### 2. Redis Kapcsolat

```bash
# Redis tesztelése
redis-cli ping
# Válasz: PONG
```

#### 3. AI Model Kapcsolat

```bash
# OpenAI API tesztelése
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

### Log Fájlok

```bash
# Alkalmazás logok
tail -f /var/log/chatbuddy/app.log

# Nginx logok
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Systemd logok
journalctl -u chatbuddy.service -f
```

## Performance Optimalizálás

### 1. Caching

```python
# Redis cache beállítás
from functools import lru_cache
import redis

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))

@lru_cache(maxsize=1000)
def get_cached_product(product_id: str):
    # Cache implementation
    pass
```

### 2. Database Indexing

```sql
-- Performance indexek
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_embedding ON products USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
```

### 3. Load Balancing

```nginx
# Nginx load balancer
upstream chatbuddy_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    location / {
        proxy_pass http://chatbuddy_backend;
    }
}
```

## Security Checklist

- [ ] HTTPS/SSL beállítása
- [ ] Firewall konfiguráció
- [ ] Rate limiting implementálása
- [ ] Input validation
- [ ] SQL injection védelem
- [ ] XSS védelem
- [ ] CORS beállítás
- [ ] Security headers
- [ ] API key rotation
- [ ] Log monitoring
- [ ] Backup strategy
- [ ] Incident response plan 