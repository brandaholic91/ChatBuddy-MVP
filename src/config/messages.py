# src/config/messages.py

ERROR_MESSAGES = {
    "HU": {
        "GENERIC_ERROR": {
            "code": "E001",
            "message": "Ismeretlen hiba történt. Kérjük, próbálja újra később.",
            "action": "Ellenőrizze az internetkapcsolatot, és próbálja meg ismét. Ha a probléma továbbra is fennáll, lépjen kapcsolatba az ügyfélszolgálattal.",
            "category": "System"
        },
        "INVALID_INPUT": {
            "code": "E002",
            "message": "Érvénytelen bemenet. Kérjük, ellenőrizze a megadott adatokat.",
            "action": "Győződjön meg róla, hogy minden kötelező mező ki van töltve, és a formátum helyes.",
            "category": "Validation"
        },
        "AGENT_NOT_FOUND": {
            "code": "E003",
            "message": "Az ágens nem található. Lehet, hogy nem létezik, vagy jelenleg nem elérhető.",
            "action": "Ellenőrizze az ágens nevét, vagy próbálja meg később. Ha a probléma továbbra is fennáll, lépjen kapcsolatba az ügyfélszolgálattal.",
            "category": "Agent"
        },
        "DATABASE_ERROR": {
            "code": "E004",
            "message": "Adatbázis hiba történt. Kérjük, próbálja újra később.",
            "action": "Ez egy belső hiba. Kérjük, értesítse az ügyfélszolgálatot a hibakóddal: {error_code}.",
            "category": "Database"
        },
        "UNAUTHORIZED_ACCESS": {
            "code": "E005",
            "message": "Nincs jogosultsága ehhez a művelethez.",
            "action": "Győződjön meg róla, hogy be van jelentkezve, és rendelkezik a megfelelő engedélyekkel.",
            "category": "Security"
        },
        "RATE_LIMIT_EXCEEDED": {
            "code": "E006",
            "message": "Túl sok kérés. Kérjük, várjon egy kicsit, mielőtt újra próbálkozik.",
            "action": "Várjon néhány percet, majd próbálja újra. Ha gyakran találkozik ezzel a hibával, lépjen kapcsolatba az ügyfélszolgálattal.",
            "category": "Rate Limiting"
        },
        "NETWORK_ERROR": {
            "code": "E007",
            "message": "Hálózati hiba történt. Kérjük, ellenőrizze az internetkapcsolatát.",
            "action": "Ellenőrizze az internetkapcsolatot, és próbálja meg ismét.",
            "category": "Network"
        }
    }
}