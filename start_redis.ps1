#!/usr/bin/env pwsh
# Redis lokális indítás script ChatBuddy MVP projekthez
# Használat: .\start_redis.ps1

Write-Host "🚀 Redis indítása ChatBuddy MVP projekthez..." -ForegroundColor Green

# Ellenőrizzük, hogy Docker fut-e
try {
    docker version | Out-Null
    Write-Host "✅ Docker elérhető" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker nem fut vagy nincs telepítve!" -ForegroundColor Red
    Write-Host "Telepítsd a Docker Desktop-ot: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

# Ellenőrizzük, hogy a .env fájl létezik-e
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env fájl nem található!" -ForegroundColor Yellow
    Write-Host "Másold át az env.example fájlt .env néven és töltsd ki a Redis beállításokat:" -ForegroundColor Yellow
    Write-Host "REDIS_URL=redis://localhost:6379" -ForegroundColor Cyan
    Write-Host "REDIS_PASSWORD=defaultpassword" -ForegroundColor Cyan
    exit 1
}

# Redis konténer indítása
Write-Host "📦 Redis konténer indítása..." -ForegroundColor Blue
docker-compose up -d redis

# Várunk, hogy a Redis elinduljon
Write-Host "⏳ Várakozás a Redis elindulására..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Ellenőrizzük a Redis kapcsolatot
try {
    $redisTest = docker exec chatbuddy-mvp_redis_1 redis-cli --raw incr ping
    if ($redisTest -eq "1") {
        Write-Host "✅ Redis sikeresen elindult és működik!" -ForegroundColor Green
        Write-Host "📍 Redis URL: redis://localhost:6379" -ForegroundColor Cyan
        Write-Host "🔑 Jelszó: defaultpassword" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Redis nem válaszol megfelelően!" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Redis kapcsolat tesztelése sikertelen!" -ForegroundColor Red
    Write-Host "Ellenőrizd a Docker konténereket: docker ps" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 Hasznos parancsok:" -ForegroundColor Magenta
Write-Host "  Redis CLI: docker exec -it chatbuddy-mvp_redis_1 redis-cli" -ForegroundColor Cyan
Write-Host "  Redis logok: docker logs chatbuddy-mvp_redis_1" -ForegroundColor Cyan
Write-Host "  Redis leállítás: docker-compose stop redis" -ForegroundColor Cyan
Write-Host "  Minden leállítása: docker-compose down" -ForegroundColor Cyan 