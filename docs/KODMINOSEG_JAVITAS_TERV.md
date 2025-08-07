# Kódminőség Javítási Terv - ChatBuddy MVP

Ez a dokumentum a ChatBuddy MVP projekt kódminőségének javítására vonatkozó tervet részletezi. A cél a kód olvashatóságának, karbantarthatóságának, megbízhatóságának és tesztelhetőségének növelése.

---

### 1. Duplikáció csökkentése

**Jelenlegi helyzet:**
Az `agents` könyvtárban (pl. `general`, `marketing`, `order_status`, `product_info`, `recommendations`, `social_media`) valószínűsíthetően ismétlődő kódminták találhatók, mivel mindegyik ágens hasonló struktúrával és alapvető funkciókkal rendelkezik (pl. üzenetfeldolgozás, válaszgenerálás, függőségek kezelése). Hasonlóképpen, az `integrations` könyvtárban (pl. `cache`, `database`, `marketing`, `social_media`, `webshop`) is előfordulhatnak ismétlődő inicializálási, hiba kezelési vagy adatfeldolgozási logikák.

**Cél:**
Azonosítani és refaktorálni az ismétlődő kódrészleteket, közös absztrakciókat (alaposztályok, segédfüggvények, mixinek) létrehozásával. Ez csökkenti a kódméretet, javítja a karbantarthatóságot és csökkenti a hibalehetőségeket.

**Lépések:**
1.  **Közös ágens alaposztály létrehozása:**
    *   Hozzon létre egy `src/agents/base/base_agent.py` fájlt.
    *   Definiáljon egy `BaseAgent` osztályt, amely tartalmazza az összes ágens által megosztott alapvető funkcionalitást (pl. `__init__` metódus a függőségek kezelésére, `process_message` vagy `run` metódus alapvető üzenetfeldolgozási logikával).
    *   Minden meglévő ágens (pl. `general/agent.py`, `marketing/agent.py`) örököljön a `BaseAgent` osztályból, és csak a specifikus logikát implementálja.
2.  **Közös integrációs segédfüggvények/osztályok:**
    *   Vizsgálja meg az `integrations` könyvtár alatti modulokat. Keresse az ismétlődő mintákat (pl. API hívások, válaszok feldolgozása, hiba kezelés).
    *   Hozzon létre `src/utils/integration_utils.py` vagy hasonló fájlokat a közös segédfüggvények számára.
    *   Például, ha több integráció is hasonló módon kezel API kulcsokat vagy konfigurációt, vonja ki ezt a logikát egy közös helyre.
3.  **Konfiguráció és konstansok centralizálása:**
    *   Győződjön meg róla, hogy minden konfigurációs érték és konstans a `src/config` könyvtárban van definiálva, és onnan importálódik. Kerülje a hardkódolt értékeket a logikai fájlokban.

---

### 2. Típusbiztonság javítása

**Jelenlegi helyzet:**
A projektben valószínűleg hiányoznak vagy inkonzisztensek a típusjelölések, ami megnehezíti a kód megértését, a hibák azonosítását fordítási időben, és a refaktorálást. A `mypy` konfiguráció valószínűleg nem elég szigorú.

**Cél:**
A típusjelölések kiterjesztése a teljes kódbázisra, különös tekintettel a függvényparaméterekre, visszatérési értékekre és osztályattribútumokra. A `mypy` konfiguráció szigorítása a statikus analízis hatékonyságának növelése érdekében.

**Lépések:**
1.  **`mypy` konfiguráció szigorítása:**
    *   Ellenőrizze vagy hozza létre a `mypy.ini` fájlt a projekt gyökerében.
    *   Adja hozzá a következő szigorú szabályokat (vagy győződjön meg róla, hogy már benne vannak):
        ```ini
        [mypy]
        disallow_untyped_defs = True
        no_implicit_optional = True
        warn_return_any = True
        warn_unused_ignores = True
        check_untyped_defs = True
        disallow_untyped_calls = True
        ```
    *   Futtassa a `mypy`-t a kódbázison (`mypy src/`) és javítsa a felmerülő hibákat.
2.  **Típusjelölések hozzáadása:**
    *   **Függvények és metódusok:** Adjon hozzá típusjelöléseket minden függvény és metódus paraméteréhez és visszatérési értékéhez. Kezdje a leggyakrabban használt segédprogramokkal (`src/utils`) és a fő belépési pontokkal (`src/main.py`, `src/workflows`).
    *   **Osztályattribútumok:** Használjon típusjelöléseket az osztályattribútumok deklarálásakor.
    *   **Pydantic modellek kiterjesztése:** Győződjön meg róla, hogy a `src/models` alatti összes Pydantic modell teljes mértékben típusjelölt, és használja ki a Pydantic validációs képességeit.
3.  **Fokozatos bevezetés:**
    *   Ha a kódbázis nagy, fontolja meg a típusjelölések fokozatos bevezetését, modulonként vagy funkciónként haladva.

---

### 3. Teszt coverage javítása

**Jelenlegi helyzet:**
A tesztlefedettség alacsony (kb. 25%), ami azt jelenti, hogy a kód nagy része nincs automatizált tesztekkel ellenőrizve. Ez növeli a hibák kockázatát és megnehezíti a refaktorálást.

**Cél:**
A tesztlefedettség növelése 95% fölé. Ez magában foglalja az egységtesztek, integrációs tesztek és edge case-ek lefedését.

**Lépések:**
1.  **Tesztelési stratégia felülvizsgálata:**
    *   Tekintse át a `tests` könyvtárat, és győződjön meg róla, hogy a tesztek jól strukturáltak és könnyen futtathatók.
    *   Határozza meg a legkritikusabb modulokat és funkciókat, amelyeknek magas tesztlefedettségre van szükségük (pl. `src/main.py`, `src/workflows`, `src/integrations/database`, `src/config/security`).
2.  **Egységtesztek kiterjesztése:**
    *   Minden függvényhez és metódushoz írjon egységtesztet, amely lefedi a normál működést, a hibakezelést és az edge case-eket.
    *   Használjon mock objektumokat a külső függőségek (pl. adatbázis, API hívások) izolálására.
3.  **Integrációs tesztek hozzáadása:**
    *   Írjon integrációs teszteket, amelyek ellenőrzik a modulok közötti interakciókat (pl. ágensek és integrációk közötti kommunikáció, adatbázis műveletek).
    *   Használjon tesztadatbázist vagy in-memory adatbázist az integrációs tesztekhez.
4.  **Edge case-ek és hibakezelés tesztelése:**
    *   Különös figyelmet fordítson a hibakezelési logikára és az edge case-ekre. Tesztelje, hogy a rendszer hogyan reagál érvénytelen bemenetekre, hálózati hibákra, adatbázis hibákra stb.
5.  **Folyamatos tesztelés és jelentéskészítés:**
    *   Integrálja a tesztfuttatást a CI/CD pipeline-ba (ha van ilyen), hogy minden kódmódosítás után automatikusan fusson.
    *   Használjon lefedettségi jelentéskészítő eszközöket (pl. `pytest-cov`), és kövesse nyomon a lefedettségi százalékot.

---

**Implementációs megjegyzések:**
*   A fenti lépéseket iteratívan kell végrehajtani, prioritásokat felállítva a legkritikusabb területekkel kezdve.
*   Minden változtatást kis, kezelhető commitokban kell végrehajtani, és minden commit után futtatni kell a teszteket.
*   A kódminőség javítása folyamatos folyamat, nem egyszeri feladat.
