# Contributing to Chatbuddy MVP

Köszönjük, hogy hozzájárul a Chatbuddy MVP fejlesztéséhez! Ez a dokumentum útmutatást nyújt a projekthez való hozzájáruláshoz.

## 🚀 Kezdés

### Előfeltételek

- Python 3.11+
- Git
- Docker (opcionális)
- OpenAI API kulcs (fejlesztéshez)

### Projekt Klónozása

```bash
git clone https://github.com/your-org/chatbuddy-mvp.git
cd chatbuddy-mvp
```

### Környezet Beállítása

```bash
# Python környezet létrehozása
python -m venv venv
source venv/bin/activate  # Linux/Mac
# vagy
venv\Scripts\activate     # Windows

# Függőségek telepítése
pip install -r requirements.txt

# Pre-commit hooks telepítése
pre-commit install
```

### Környezeti Változók

```bash
# .env fájl létrehozása
cp .env_example .env

# Szerkeszd a .env fájlt a saját API kulcsaiddal
nano .env
```

## 📝 Fejlesztési Workflow

### 1. Branch Létrehozása

```bash
# Main branch frissítése
git checkout main
git pull origin main

# Új feature branch létrehozása
git checkout -b feature/your-feature-name
```

### 2. Fejlesztés

- Írj tiszta, dokumentált kódot
- Kövesd a Python PEP 8 stílus útmutatót
- Használd a type hints-et
- Írj docstring-eket minden függvényhez

### 3. Tesztek Írása

```bash
# Tesztek futtatása
pytest

# Coverage report
pytest --cov=src --cov-report=html

# Type checking
mypy src/
```

### 4. Kód Minőség

```bash
# Kód formázás
black src/
isort src/

# Linting
flake8 src/

# Pre-commit hooks (automatikusan)
git add .
git commit -m "feat: add new feature"
```

### 5. Pull Request

```bash
# Push a branch-et
git push origin feature/your-feature-name

# Pull Request létrehozása a GitHub-on
```

## 🏗️ Projekt Struktúra

```
src/
├── agents/           # AI ügynökök
├── config/           # Konfiguráció
├── integrations/     # Külső szolgáltatások
├── models/           # Pydantic modellek
├── utils/            # Segédeszközök
└── workflows/        # LangGraph workflow-k

docs/                 # Dokumentáció
tests/                # Tesztek
templates/            # Email/SMS template-ek
```

## 🧪 Tesztelés

### Teszt Struktúra

```python
# tests/test_agents.py
import pytest
from src.agents.coordinator import coordinator_agent

def test_coordinator_agent():
    """Test coordinator agent functionality."""
    # Test implementation
    pass
```

### Teszt Futtatása

```bash
# Összes teszt
pytest

# Specifikus teszt
pytest tests/test_agents.py

# Verbose mód
pytest -v

# Coverage
pytest --cov=src --cov-report=term-missing
```

## 📚 Dokumentáció

### Docstring Formátum

```python
def process_chat_message(message: str, user_id: str) -> dict:
    """
    Process incoming chat message and return response.
    
    Args:
        message: User's message text
        user_id: Unique user identifier
        
    Returns:
        dict: Response with message and metadata
        
    Raises:
        ValueError: If message is empty
        ConnectionError: If AI service is unavailable
    """
    pass
```

### Markdown Dokumentáció

- Használj magyar nyelvet
- Kövesd a Markdown best practice-eket
- Inklúdálj példákat és kódrészleteket
- Frissítsd a dokumentációt a kód változásával

## 🔧 Fejlesztési Eszközök

### Pre-commit Hooks

A projekt automatikusan futtatja a következő ellenőrzéseket:

- **Black**: Kód formázás
- **isort**: Import rendezés
- **Flake8**: Linting
- **MyPy**: Type checking
- **Pre-commit hooks**: Egyéb ellenőrzések

### IDE Beállítások

#### VS Code

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"]
}
```

#### PyCharm

- Enable type checking
- Configure Black formatter
- Set up pytest runner

## 🐛 Bug Reports

### Bug Report Template

```markdown
## Bug Description
Rövid leírás a problémáról.

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
Mit kellett volna történnie.

## Actual Behavior
Mi történt valójában.

## Environment
- OS: [e.g. Ubuntu 20.04]
- Python Version: [e.g. 3.11.0]
- Package Version: [e.g. 0.1.0]

## Additional Context
Egyéb információ.
```

## 💡 Feature Requests

### Feature Request Template

```markdown
## Feature Description
Rövid leírás az új funkcióról.

## Use Case
Mikor és miért lenne hasznos.

## Proposed Solution
Hogyan implementálnád.

## Alternatives Considered
Egyéb megoldások.

## Additional Context
Egyéb információ.
```

## 🚀 Release Process

### Version Management

- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Changelog**: Karbantartás a CHANGELOG.md-ben
- **Release Notes**: Részletes leírás minden release-hez

### Release Checklist

- [ ] Tesztek átmennek
- [ ] Dokumentáció frissítve
- [ ] Changelog frissítve
- [ ] Version bumped
- [ ] Release notes kész

## 🤝 Közösségi Irányelvek

### Kommunikáció

- **Nyelv**: Magyar (dokumentáció, kommentek)
- **Tisztelet**: Mindig tisztelettudóan kommunikálj
- **Konstruktív**: Építő jellegű visszajelzést adj

### Kód Review

- **Konstruktív**: Építő jellegű kommentek
- **Reszpekt**: Tiszteld a másik munkáját
- **Tanulás**: Használd fel a review-t tanulási lehetőségként

### Commit Messages

```bash
# Konvenció: type(scope): description

feat(agents): add coordinator agent implementation
fix(api): resolve CORS issue
docs(readme): update installation instructions
test(workflows): add workflow tests
refactor(models): simplify product model
```

## 📞 Kapcsolat

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: team@chatbuddy.hu

## 📄 Licensz

Ez a projekt a MIT licensz alatt áll. Lásd a [LICENSE](LICENSE) fájlt részletekért.

---

Köszönjük a hozzájárulásod! 🎉 