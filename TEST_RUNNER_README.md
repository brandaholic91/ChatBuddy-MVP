# ChatBuddy MVP Test Runner

Ez a dokumentum leírja, hogyan lehet futtatni a ChatBuddy MVP projekt teszteit.

## PowerShell Test Runner Script

A projekt tartalmaz egy `run_tests.ps1` PowerShell script-et, ami egyszerűsíti a teszt futtatást és konzisztens alapértelmezett opciókat biztosít.

### Alapvető használat

```powershell
# Összes teszt futtatása
.\run_tests.ps1 -AllTests

# Specifikus agent tesztek futtatása (ajánlott)
.\run_tests.ps1 -MarketingTests
.\run_tests.ps1 -OrderStatusTests
.\run_tests.ps1 -ProductInfoTests
.\run_tests.ps1 -RecommendationsTests
.\run_tests.ps1 -SecurityTests
.\run_tests.ps1 -RateLimitingTests
.\run_tests.ps1 -CoordinatorTests

# Specifikus teszt fájl futtatása
.\run_tests.ps1 -TestFile "tests/test_marketing_agent.py"

# Specifikus teszt osztály futtatása
.\run_tests.ps1 -TestFile "tests/test_marketing_agent.py" -TestClass "TestMarketingAgent"

# Specifikus teszt függvény futtatása
.\run_tests.ps1 -TestFile "tests/test_marketing_agent.py" -TestClass "TestMarketingAgent" -TestFunction "test_create_marketing_agent"

# Figyelmeztetések elnyomása (csak ha szükséges)
.\run_tests.ps1 -MarketingTests -NoWarnings
```

### Manuális pytest futtatás

Ha nem szeretnéd használni a PowerShell script-et, használhatod a pytest-et közvetlenül:

```powershell
# Alapvető futtatás
python -m pytest tests/test_marketing_agent.py -v

# Figyelmeztetések elnyomásával
python -W ignore -m pytest tests/test_marketing_agent.py -v
```

## Teszt Kategóriák

### Marketing Agent Tesztek (24 teszt)
- **Alapvető funkcionalitás**: Email/SMS küldés, kampány kezelés
- **Tool tesztek**: Minden marketing tool tesztelése
- **Integrációs tesztek**: Üzenet feldolgozás, hibakezelés
- **Biztonsági tesztek**: SQL injection, XSS, adatvédelem
- **Teljesítmény tesztek**: Válaszidő, párhuzamos kérések

### Order Status Agent Tesztek (35 teszt)
- **Alapvető funkcionalitás**: Order lekérdezés, tracking, státusz frissítés
- **Integrációs tesztek**: Üzenet feldolgozás, hibakezelés
- **Biztonsági tesztek**: SQL injection védelem, jogosultság ellenőrzés
- **Teljesítmény tesztek**: Válaszidő, párhuzamos kérések
- **Edge case tesztek**: Üres lekérdezések, hosszú szövegek
- **Async kompatibilitás**: Minden teszt asyncio és trio esetén is fut

### Product Info Agent Tesztek (17 teszt)
- **Alapvető funkcionalitás**: Termék keresés, részletek, értékelések, elérhetőség, árak
- **Tool tesztek**: Minden product info tool tesztelése
- **Query típusok**: Különböző lekérdezés típusok kezelése
- **Dependency injection**: Függőségek megfelelő kezelése

### Recommendations Agent Tesztek (40 teszt)
- **Alapvető funkcionalitás**: Felhasználói preferenciák, hasonló termékek, trend elemzés, személyre szabott ajánlások
- **Integrációs tesztek**: Üzenet feldolgozás, hibakezelés
- **Biztonsági tesztek**: SQL injection védelem, adatvédelem, jogosultság ellenőrzés
- **Teljesítmény tesztek**: Válaszidő, párhuzamos kérések
- **Edge case tesztek**: Üres lekérdezések, hosszú szövegek, nincs preferencia
- **Business logic tesztek**: Kategória alapú ajánlások, ár szűrés, márka preferenciák
- **Async kompatibilitás**: Minden teszt asyncio és trio esetén is fut

### Security Tesztek (38 teszt)
- **Konfiguráció tesztek**: Biztonsági beállítások, titkos kulcsok validálása
- **Input validáció**: String tisztítás, email/telefon validáció, jelszó erősség
- **JWT kezelés**: Token létrehozás, ellenőrzés, lejárat kezelés
- **Fenyegetés detektálás**: SQL injection, XSS, veszélyes kulcsszavak
- **Jelszó biztonság**: Hasholás, ellenőrzés, biztonságos token generálás
- **GDPR compliance**: Hozzájárulás kezelés, adat törlés/export
- **Audit logging**: Agent interakciók, biztonsági események, adat hozzáférés
- **Integrációs tesztek**: Biztonságos chat feldolgozás, rosszindulatú input kezelés
- **Middleware tesztek**: Biztonsági fejlécek, IP blokkolás

### Rate Limiting Tesztek (12 teszt)
- **Redis rate limiter**: Rate limit parsing, ellenőrzés, túllépés kezelés
- **Middleware tesztek**: Kliens azonosítás, endpoint rate limit beállítások
- **Integrációs tesztek**: Rate limit fejlécek, túllépés válaszok
- **Teljesítmény tesztek**: Párhuzamos rate limit ellenőrzések, memória használat
- **Konfiguráció és hibakezelés**: Rate limit beállítások, hiba kezelés

### Coordinator Agent Tesztek (14 teszt)
- **Üzenet kategorizálás**: Product info, order status, recommendation, marketing, general kategóriák
- **Állapot kezelés**: State lekérdezés és reset
- **Async funkcionalitás**: Üzenet feldolgozás, hibakezelés
- **Singleton pattern**: Agent példányok kezelése
- **Integrációs tesztek**: Teljes üzenet folyam (OpenAI API szükséges)

## Teszt Eredmények

### Sikeres Tesztek (2025.08.04.)
- ✅ **Marketing Agent**: 24/24 teszt sikeres
- ✅ **Order Status Agent**: 35/35 teszt sikeres
- ✅ **Product Info Agent**: 17/17 teszt sikeres
- ✅ **Recommendations Agent**: 40/40 teszt sikeres
- ✅ **Security**: 38/38 teszt sikeres
- ✅ **Rate Limiting**: 12/12 teszt sikeres
- ✅ **Coordinator Agent**: 13/14 teszt sikeres (1 skipped - OpenAI API szükséges)
- ✅ **Models**: 15/15 teszt sikeres
- ✅ **Imports**: 8/8 teszt sikeres

### Teszt Idők
- **Marketing Agent**: ~1.5 másodperc
- **Order Status Agent**: ~1.5 másodperc
- **Product Info Agent**: ~23 másodperc
- **Recommendations Agent**: ~3 másodperc
- **Security**: ~6 másodperc
- **Rate Limiting**: ~3 másodperc
- **Coordinator Agent**: ~2.5 másodperc
- **Teljes teszt suite**: ~73 másodperc (207 teszt)

## Hibaelhárítás

### Pytest Mark Figyelmeztetések
A projektben használt pytest markok (`@pytest.mark.unit`, `@pytest.mark.integration`, stb.) már megfelelően regisztrálva vannak a `pytest.ini` fájlban. Ha mégis figyelmeztetéseket látsz, használd a `-NoWarnings` kapcsolót: `.\run_tests.ps1 -MarketingTests -NoWarnings`

### Async Tesztek
A tesztek mind asyncio, mind trio async library-kel kompatibilisek. Ha problémák merülnek fel, ellenőrizd a Python verziót és az async library verziókat.

### Coverage Report
A tesztek coverage report-ot is generálnak:
- HTML formátum: `htmlcov/index.html`
- Konzol formátum: A teszt futtatás során

## Fejlesztői Tippek

1. **Gyors tesztelés**: Használd a specifikus teszt függvény futtatást fejlesztés közben
2. **Konzisztens opciók**: A PowerShell script mindig `-v --tb=short` opciókat használ
3. **Coverage**: A coverage report automatikusan generálódik és segít azonosítani a nem tesztelt kód részeket
4. **CI/CD**: A PowerShell script könnyen integrálható CI/CD pipeline-okba
5. **Debugging**: Ha figyelmeztetéseket látsz, használd a `-NoWarnings` kapcsolót 