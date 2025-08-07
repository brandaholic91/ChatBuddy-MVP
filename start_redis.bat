@echo off
REM Redis lokális indítás script ChatBuddy MVP projekthez
REM Használat: start_redis.bat

echo 🚀 Redis indítása ChatBuddy MVP projekthez...

REM Ellenőrizzük, hogy Docker fut-e
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker nem fut vagy nincs telepítve!
    echo Telepítsd a Docker Desktop-ot: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo ✅ Docker elérhető

REM Ellenőrizzük, hogy a .env fájl létezik-e
if not exist ".env" (
    echo ⚠️  .env fájl nem található!
    echo Másold át az env.example fájlt .env néven és töltsd ki a Redis beállításokat:
    echo REDIS_URL=redis://localhost:6379
    echo REDIS_PASSWORD=defaultpassword
    pause
    exit /b 1
)

REM Redis konténer indítása
echo 📦 Redis konténer indítása...
docker-compose up -d redis

REM Várunk, hogy a Redis elinduljon
echo ⏳ Várakozás a Redis elindulására...
timeout /t 5 /nobreak >nul

REM Ellenőrizzük a Redis kapcsolatot
docker exec chatbuddy-mvp_redis_1 redis-cli --raw incr ping >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Redis sikeresen elindult és működik!
    echo 📍 Redis URL: redis://localhost:6379
    echo 🔑 Jelszó: defaultpassword
) else (
    echo ❌ Redis nem válaszol megfelelően!
    echo Ellenőrizd a Docker konténereket: docker ps
)

echo.
echo 📋 Hasznos parancsok:
echo   Redis CLI: docker exec -it chatbuddy-mvp_redis_1 redis-cli
echo   Redis logok: docker logs chatbuddy-mvp_redis_1
echo   Redis leállítás: docker-compose stop redis
echo   Minden leállítása: docker-compose down

pause 