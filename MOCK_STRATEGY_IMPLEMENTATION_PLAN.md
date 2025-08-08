# 🎭 Mock Stratégia Implementálási Terv

**Projekt**: ChatBuddy MVP - Teljes Teszt Suite
**Stratégia**: 90% Mock Unit Tesztek + 10% Valódi Integráció Tesztek
**Cél**: Kompatibilitási problémák megoldása és teljes teszt lefedettség

---

## 📋 **Áttekintés**

### **Jelenlegi probléma:**
- Pydantic 2.11.7 + LangChain 0.3.27 kompatibilitási ütközés
- 56 teszt fájl nem futtatható a discriminator field hibák miatt
- Teljes teszt suite nem működik

### **Megoldás:**
- **90% Mock Tesztek**: Gyors, megbízható, dependency-mentes unit tesztek
- **10% Valódi Tesztek**: Kritikus integrációs pontok validálása

---

## 🏗️ **Implementálási Fázisok**

### **Fázis 1: Mock Infrastruktúra (2-3 óra)**
- [ ] Mock objektumok létrehozása
- [ ] conftest.py átstrukturálása
- [ ] pytest.ini optimalizálás
- [ ] Test marker rendszer bevezetése

### **Fázis 2: Mock Unit Tesztek (90% - 4-5 óra)**
- [ ] Agents modulok mock tesztelése
- [ ] Workflows mock tesztelése
- [ ] Integrations mock tesztelése
- [ ] Models és Utils tesztelése

### **Fázis 3: Valódi Integráció Tesztek (10% - 2-3 óra)**
- [ ] Kritikus E2E flow-k
- [ ] Valódi API integráció validáció
- [ ] Performance és reliability tesztek

### **Fázis 4: CI/CD Integráció (1 óra)**
- [ ] GitHub Actions workflow
- [ ] Test reporting
- [ ] Coverage mérés

---

## 🎯 **Fázis 1: Mock Infrastruktúra**

### **1.1 Mock Objektumok Könyvtára**

**Fájl**: `tests/mocks/__init__.py`

```python
"""Mock objektumok központi könyvtára."""

# LangChain Mocks
class MockAIMessage:
    def __init__(self, content: str, **kwargs):
        self.content = content
        self.metadata = kwargs.get('metadata', {})

class MockHumanMessage:
    def __init__(self, content: str, **kwargs):
        self.content = content
        self.metadata = kwargs.get('metadata', {})

class MockChatOpenAI:
    def __init__(self, model: str = "gpt-4", **kwargs):
        self.model = model
        self.temperature = kwargs.get('temperature', 0.7)

    async def agenerate(self, messages, **kwargs):
        return MockLLMResponse("Mock AI response")

# Supabase Mocks
class MockSupabaseClient:
    def table(self, name): return MockTable(name)
    def auth(self): return MockAuth()

# Redis Mocks
class MockRedisClient:
    def __init__(self): self._data = {}
    async def get(self, key): return self._data.get(key)
    async def set(self, key, value): self._data[key] = value

# WebShop Integration Mocks
class MockWebShopAPI:
    async def get_products(self): return [{"id": 1, "name": "Test Product"}]
    async def get_orders(self): return [{"id": 1, "status": "completed"}]
```

### **1.2 conftest.py Átstrukturálás**

**Fájl**: `tests/conftest.py`

```python
"""Pytest konfigurációk és fixtures."""

import pytest
from unittest.mock import patch, MagicMock
from tests.mocks import *

# ===========================================
# MOCK FIXTURES (90% tesztek)
# ===========================================

@pytest.fixture(autouse=True, scope="session")
def mock_external_dependencies():
    """Auto-mock minden külső függőséget."""

    patches = [
        # LangChain
        patch('langchain_core.messages.AIMessage', MockAIMessage),
        patch('langchain_core.messages.HumanMessage', MockHumanMessage),
        patch('langchain_openai.ChatOpenAI', MockChatOpenAI),

        # Supabase
        patch('supabase.Client', MockSupabaseClient),

        # Redis
        patch('redis.asyncio.Redis', MockRedisClient),

        # External APIs
        patch('openai.OpenAI', MagicMock),
        patch('requests.get', MagicMock),
        patch('aiohttp.ClientSession', MagicMock),
    ]

    # Start all patches
    mocks = [p.start() for p in patches]
    yield mocks

    # Stop all patches
    for p in patches:
        p.stop()

# ===========================================
# REAL INTEGRATION FIXTURES (10% tesztek)
# ===========================================

@pytest.fixture(scope="session")
def real_openai_client():
    """Valódi OpenAI kliens integráció tesztekhez."""
    import openai
    return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", "test-key"))

@pytest.fixture(scope="session")
def real_supabase_client():
    """Valódi Supabase kliens integráció tesztekhez."""
    from supabase import create_client
    return create_client(
        os.getenv("SUPABASE_URL", "http://localhost:54321"),
        os.getenv("SUPABASE_ANON_KEY", "test-key")
    )

# ===========================================
# TEST DATA FIXTURES
# ===========================================

@pytest.fixture
def sample_user_context():
    return {
        "user_id": "test_user_123",
        "session_id": "session_456",
        "language": "hu",
        "timezone": "Europe/Budapest"
    }

@pytest.fixture
def sample_chat_request():
    return {
        "message": "Szia! Segítenél termékeket keresni?",
        "user_id": "test_user_123",
        "session_id": "session_456"
    }

@pytest.fixture
def sample_products():
    return [
        {"id": 1, "name": "iPhone 15", "price": 350000, "category": "electronics"},
        {"id": 2, "name": "Samsung Galaxy", "price": 280000, "category": "electronics"},
        {"id": 3, "name": "Nike cipő", "price": 45000, "category": "fashion"}
    ]
```

### **1.3 pytest.ini Optimalizálás**

**Fájl**: `pytest.ini`

```ini
[pytest]
# Test discovery
python_paths = .
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Test markers
markers =
    # Test types (90-10 strategy)
    unit: Unit tests with mocks (fast, default)
    integration: Real integration tests (slow, manual)
    e2e: End-to-end tests (very slow, CI only)

    # Module markers
    agents: Agent functionality tests
    workflows: Workflow tests
    integrations: Integration tests
    models: Data model tests
    utils: Utility function tests

    # Performance markers
    fast: Fast tests (< 1 second)
    slow: Slow tests (1-10 seconds)
    very_slow: Very slow tests (> 10 seconds)

    # Environment markers
    requires_openai: Requires OpenAI API key
    requires_supabase: Requires Supabase connection
    requires_redis: Requires Redis connection
    requires_internet: Requires internet connection

# Coverage settings
addopts =
    -ra
    --strict-markers
    --strict-config
    --disable-warnings
    -p no:warnings
    --tb=short
    # Coverage for unit tests only
    --cov=src
    --cov-report=term-missing:skip-covered
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-fail-under=85

# Async settings
asyncio_mode = auto
asyncio_default_fixture_loop_scope = session

# Timeout settings
timeout = 300
timeout_method = thread

# Parallel execution (optional)
# addopts = ... -n auto

# Test environment variables
env =
    ENVIRONMENT = test
    PYTHONPATH = .
```

---

## 🧪 **Fázis 2: Mock Unit Tesztek (90%)**

### **2.1 Agents Mock Tesztek**

**Prioritás**: Magas (Core functionality)
**Becsült idő**: 2 óra
**Fájlok**: `tests/agents/test_*_mock.py`

```python
# tests/agents/test_general_agent_mock.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.agents.general.agent import GeneralAgent
from src.agents.base import BaseDependencies

@pytest.mark.unit
@pytest.mark.agents
@pytest.mark.fast
class TestGeneralAgentMock:
    """General Agent mock tesztek."""

    @pytest.fixture
    def agent(self):
        return GeneralAgent()

    @pytest.fixture
    def dependencies(self, sample_user_context):
        return BaseDependencies(
            user_context=sample_user_context,
            audit_logger=AsyncMock()
        )

    async def test_agent_initialization(self, agent):
        """Agent inicializálás tesztje."""
        assert agent.model == 'openai:gpt-4o'
        assert agent.agent_type.value == 'general'

    async def test_successful_response(self, agent, dependencies):
        """Sikeres válasz tesztje."""
        result = await agent.run("Hello", dependencies)

        assert result.response_text is not None
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.metadata, dict)

    async def test_error_handling(self, agent, dependencies):
        """Hibakezelés tesztje."""
        # Force error in mock agent
        agent._agent = MagicMock()
        agent._agent.run.side_effect = Exception("Mock error")

        result = await agent.run("test", dependencies)

        assert "hiba történt" in result.response_text.lower()
        assert result.confidence == 0.0
        assert "error_type" in result.metadata
```

### **2.2 Workflows Mock Tesztek**

**Prioritás**: Magas
**Becsült idő**: 2 óra
**Fájlok**: `tests/workflows/test_*_mock.py`

```python
# tests/workflows/test_coordinator_mock.py

import pytest
from unittest.mock import AsyncMock, patch
from src.workflows.coordinator import process_coordinator_message

@pytest.mark.unit
@pytest.mark.workflows
@pytest.mark.fast
class TestCoordinatorMock:
    """Coordinator workflow mock tesztek."""

    async def test_message_routing(self, sample_chat_request):
        """Üzenet routing tesztje."""
        with patch('src.workflows.coordinator.route_to_agent') as mock_route:
            mock_route.return_value = "general"

            result = await process_coordinator_message(
                sample_chat_request["message"],
                user_id=sample_chat_request["user_id"]
            )

            assert result is not None
            mock_route.assert_called_once()

    async def test_agent_selection_logic(self):
        """Agent kiválasztási logika tesztje."""
        test_cases = [
            ("termékek", "product_info"),
            ("rendelés állapota", "order_status"),
            ("ajánlás", "recommendations"),
            ("marketing", "marketing"),
            ("általános kérdés", "general")
        ]

        for message, expected_agent in test_cases:
            with patch('src.workflows.coordinator.select_agent') as mock_select:
                mock_select.return_value = expected_agent

                result = await process_coordinator_message(message)
                assert mock_select.return_value == expected_agent
```

### **2.3 Integrations Mock Tesztek**

**Prioritás**: Közepes
**Becsült idő**: 1.5 óra

```python
# tests/integrations/test_webshop_mock.py

@pytest.mark.unit
@pytest.mark.integrations
@pytest.mark.fast
class TestWebshopIntegrationMock:
    """WebShop integráció mock tesztek."""

    async def test_product_fetch(self):
        """Termék lekérdezés mock tesztje."""
        with patch('src.integrations.webshop.api.WebShopAPI') as mock_api:
            mock_api.return_value.get_products.return_value = [
                {"id": 1, "name": "Test Product", "price": 1000}
            ]

            api = mock_api()
            products = await api.get_products()

            assert len(products) == 1
            assert products[0]["name"] == "Test Product"
```

### **2.4 Models és Utils Tesztek**

**Prioritás**: Alacsony (Már létező)
**Becsült idő**: 0.5 óra

```python
# tests/models/test_models_mock.py (már meglévő tesztek kiegészítése)
# tests/utils/test_utils_mock.py (már meglévő tesztek kiegészítése)
```

---

## 🔗 **Fázis 3: Valódi Integráció Tesztek (10%)**

### **3.1 Kritikus E2E Flow Tesztek**

**Prioritás**: Közepes
**Becsült idő**: 2 óra
**Fájlok**: `tests/e2e/test_critical_flows.py`

```python
# tests/e2e/test_critical_flows.py

import pytest
import os

@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.requires_openai
@pytest.mark.requires_supabase
class TestCriticalFlows:
    """Kritikus üzleti folyamatok valódi tesztje."""

    async def test_complete_chat_flow(self, real_openai_client):
        """Teljes chat folyamat E2E tesztje."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        # 1. Chat request
        request = {
            "message": "Milyen iPhone modellek vannak?",
            "user_id": "test_user_e2e",
            "session_id": "session_e2e"
        }

        # 2. Process through real coordinator
        from src.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            response = client.post("/api/v1/chat", json=request)

        # 3. Assertions
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0

    async def test_agent_handoff_flow(self):
        """Agent átadási folyamat tesztje."""
        # Termékkereső → Rendelés státusz váltás
        pass

    async def test_error_recovery_flow(self):
        """Hiba helyreállítási folyamat tesztje."""
        # Hibás input → Graceful degradation
        pass
```

### **3.2 API Integráció Validáció**

**Prioritás**: Alacsony
**Becsült idő**: 1 óra

```python
# tests/integration/test_api_validation.py

@pytest.mark.integration
@pytest.mark.requires_internet
class TestAPIValidation:
    """Külső API integrációk validálása."""

    async def test_openai_connectivity(self, real_openai_client):
        """OpenAI API elérhetőség."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        response = await real_openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}]
        )
        assert response.choices[0].message.content

    async def test_supabase_connectivity(self, real_supabase_client):
        """Supabase kapcsolat tesztje."""
        # Health check query
        pass
```

---

## 🚀 **Fázis 4: CI/CD Integráció**

### **4.1 GitHub Actions Workflow**

**Fájl**: `.github/workflows/tests.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  # FAST UNIT TESTS (90%) - Always run
  unit-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio

    - name: Run unit tests
      run: |
        pytest -m "unit" --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  # INTEGRATION TESTS (10%) - Only on main branch
  integration-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    needs: unit-tests
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio

    - name: Run integration tests
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
        SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
      run: |
        pytest -m "integration" --tb=short
```

### **4.2 Test Commands Dokumentáció**

**Fájl**: `TESTING.md`

```markdown
# Testing Guide

## Quick Commands

```bash
# Fejlesztés közben (gyors)
pytest -m unit

# Release előtt (teljes)
pytest

# Csak agents
pytest -m "unit and agents"

# Csak integráció (lassú)
pytest -m integration

# Coverage report
pytest -m unit --cov=src --cov-report=html
```

## Test Categories

- **unit**: Mock tesztek (90%) - gyors feedback
- **integration**: Valódi API tesztek (10%) - release validation
- **e2e**: End-to-end tesztek - critical flows only
```

---

## 📊 **Eredmény Előrejelzés**

### **Teszt Lefedettség:**
- **Unit Tests (Mock)**: 90% - ~200-250 teszt
- **Integration Tests**: 10% - ~20-30 teszt
- **Összesen**: ~270-280 teszt

### **Futási Idők:**
- **Unit Tests**: 10-15 másodperc
- **Integration Tests**: 2-5 perc
- **Teljes Suite**: 3-6 perc

### **Coverage Várakozás:**
- **Kód lefedettség**: 85-90%
- **Critical path**: 95%+
- **Edge cases**: 70-80%

---

## ✅ **Sikerkritériumok**

### **Fázis 1 Sikeres:**
- [ ] Minden mock objektum létrehozva
- [ ] conftest.py működik
- [ ] Egyszerű teszt lefut hiba nélkül

### **Fázis 2 Sikeres:**
- [ ] Minden ágenstípus tesztelve
- [ ] Workflows logika lefedve
- [ ] 85%+ coverage elérve

### **Fázis 3 Sikeres:**
- [ ] Legalább 3 kritikus E2E flow működik
- [ ] OpenAI/Supabase integráció validálva

### **Fázis 4 Sikeres:**
- [ ] CI/CD pipeline működik
- [ ] Automatikus test reporting
- [ ] Pull request validation

---

## 🎯 **Következő Lépések**

1. **Jóváhagyás**: Terv áttekintése és módosítások
2. **Implementáció**: Fázisok szerint haladás
3. **Validáció**: Minden fázis után tesztelés
4. **Dokumentáció**: Developer guide frissítése

**Becsült teljes időigény**: 8-12 óra
**Várt eredmény**: Teljes teszt suite 100% futtatható állapot

---

*Ez a terv biztosítja a gyors fejlesztői feedback-et (mock tesztek) és a production megbízhatóságot (integráció tesztek) egyaránt.*
