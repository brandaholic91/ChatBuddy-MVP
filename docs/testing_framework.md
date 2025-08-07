# ChatBuddy MVP Tesztelési Framework

## Áttekintés

A ChatBuddy MVP projekt teljes tesztelési framework-ot használ, amely magában foglalja a unit teszteket, integrációs teszteket, mock objektumokat és automatizált tesztelési eszközöket.

## Tesztelési Architektúra

### Tesztelési Piramis

```
    ┌─────────────────┐
    │   E2E Tests     │ ← Kevés, kritikus útvonalak
    ├─────────────────┤
    │Integration Tests│ ← Közepes mennyiség
    ├─────────────────┤
    │  Unit Tests     │ ← Sok, minden komponens
    └─────────────────┘
```

### Tesztelési Komponensek

1. **Unit tesztek** - Egyedi komponensek tesztelése
2. **Integrációs tesztek** - Komponensek közötti kapcsolatok
3. **Mock objektumok** - Külső függőségek szimulálása
4. **Test fixtures** - Tesztelési adatok és környezet
5. **Coverage reporting** - Kód lefedettség mérése

## Konfiguráció

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=80
    --strict-markers
    --disable-warnings
    --asyncio-mode=auto
```

### Tesztelési Markerek

- `@pytest.mark.unit` - Unit tesztek
- `@pytest.mark.integration` - Integrációs tesztek
- `@pytest.mark.security` - Biztonsági tesztek
- `@pytest.mark.performance` - Teljesítmény tesztek
- `@pytest.mark.agent` - Agent tesztek
- `@pytest.mark.workflow` - Workflow tesztek
- `@pytest.mark.database` - Adatbázis tesztek
- `@pytest.mark.marketing` - Marketing tesztek
- `@pytest.mark.api` - API tesztek
- `@pytest.mark.ai` - AI model tesztek
- `@pytest.mark.async_test` - Async tesztek
- `@pytest.mark.mock` - Mock tesztek
- `@pytest.mark.e2e` - End-to-end tesztek
- `@pytest.mark.smoke` - Smoke tesztek
- `@pytest.mark.regression` - Regressziós tesztek

## Tesztelési Struktúra

```
tests/
├── conftest.py                    # Globális fixtures
├── test_helpers.py                # Tesztelési segédeszközök
├── test_agents_unit.py            # Agent unit tesztek
├── test_workflows_unit.py         # Workflow unit tesztek
├── test_integrations_unit.py      # Integrációs unit tesztek
├── test_config_unit.py            # Konfigurációs unit tesztek
├── test_integration_comprehensive.py # Teljes integrációs tesztek
├── test_security.py               # Biztonsági tesztek
├── test_rate_limiting.py          # Rate limiting tesztek
├── test_database_integration.py   # Adatbázis integrációs tesztek
├── test_langgraph_workflow.py     # LangGraph workflow tesztek
├── test_models.py                 # Model tesztek
├── test_supabase_connection.py    # Supabase kapcsolat tesztek
├── test_pgvector.py               # Vector database tesztek
├── test_rls_policies.py           # RLS policy tesztek
├── test_rls_comprehensive.py      # RLS átfogó tesztek
├── test_routing_detailed.py       # Routing tesztek
├── test_agents_interactive.py     # Interaktív agent tesztek
├── test_agents_with_consent.py    # Consent-alapú agent tesztek
├── test_imports.py                # Import tesztek
├── simple_test.py                 # Egyszerű tesztek
└── run_tests.ps1                  # PowerShell teszt futtató
```

## Mock Objektumok

### Alapvető Mock Fixtures

```python
@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock_client = Mock()
    mock_client.table = Mock()
    mock_client.rpc = AsyncMock()
    mock_client.auth = Mock()
    mock_client.storage = Mock()
    mock_client.functions = Mock()
    return mock_client

@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    mock_client = Mock()
    mock_client.get = AsyncMock()
    mock_client.set = AsyncMock()
    mock_client.delete = AsyncMock()
    mock_client.exists = AsyncMock()
    mock_client.expire = AsyncMock()
    return mock_client
```

### AI Model Mock

```python
@pytest.fixture
def test_model():
    """Test model for agent testing."""
    return TestModel()
```

### Tesztelési Adatok

```python
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "test_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "preferences": {
            "language": "hu",
            "notifications": True
        }
    }
```

## Tesztelési Segédeszközök

### TestDataGenerator

```python
class TestDataGenerator:
    @staticmethod
    def generate_user_data(user_id: str = None) -> Dict[str, Any]:
        """Generate sample user data."""
        if user_id is None:
            user_id = f"user_{datetime.now().timestamp()}"
        
        return {
            "id": user_id,
            "email": f"test_{user_id}@example.com",
            "name": f"Test User {user_id}",
            "preferences": {
                "language": "hu",
                "notifications": True,
                "theme": "dark"
            }
        }
```

### AsyncTestHelper

```python
class AsyncTestHelper:
    @staticmethod
    async def wait_for_condition(condition_func, timeout: float = 5.0):
        """Wait for a condition to be true."""
        start_time = datetime.now()
        while datetime.now() - start_time < timedelta(seconds=timeout):
            if await condition_func():
                return True
            await asyncio.sleep(0.1)
        return False
```

### ValidationHelper

```python
class ValidationHelper:
    @staticmethod
    def validate_response_structure(response: Dict[str, Any]) -> bool:
        """Validate that a response has the expected structure."""
        required_fields = ["content", "model", "usage"]
        return all(field in response for field in required_fields)
```

## Tesztelési Példák

### Unit Teszt Példa

```python
class TestGeneralAgent:
    @pytest.mark.unit
    @pytest.mark.agent
    def test_general_agent_initialization(self, test_model):
        """Test GeneralAgent initialization."""
        agent = GeneralAgent(model=test_model)
        assert agent is not None
        assert agent.model == test_model
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_general_agent_process_message(self, test_model, mock_chat_message):
        """Test GeneralAgent message processing."""
        agent = GeneralAgent(model=test_model)
        response = await agent.process_message(mock_chat_message)
        assert response is not None
        assert "content" in response
```

### Integrációs Teszt Példa

```python
class TestFullWorkflowIntegration:
    @pytest.mark.integration
    @pytest.mark.workflow
    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self, 
                                            mock_workflow_config, 
                                            mock_agent_state, 
                                            mock_chat_message,
                                            test_model):
        """Test complete conversation flow from message to response."""
        # Initialize components
        coordinator = Coordinator(config=mock_workflow_config)
        workflow = LangGraphWorkflow(config=mock_workflow_config)
        general_agent = GeneralAgent(model=test_model)
        
        # Process conversation
        route = await coordinator.route_message(mock_chat_message)
        assert route is not None
        
        # Execute workflow
        result = await workflow.execute(mock_agent_state)
        assert result is not None
        assert "output" in result
```

## Tesztelési Futtatás

### PowerShell Script

```powershell
# Alapvető tesztelés
.\tests\run_tests.ps1

# Unit tesztek coverage-val
.\tests\run_tests.ps1 -Unit -Coverage

# Integrációs tesztek verbose módban
.\tests\run_tests.ps1 -Integration -Verbose

# Biztonsági tesztek párhuzamosan
.\tests\run_tests.ps1 -TestType security -Parallel

# Egyedi markerek
.\tests\run_tests.ps1 -Markers "agent and not slow"
```

### Közvetlen pytest

```bash
# Minden teszt
python -m pytest tests/

# Unit tesztek
python -m pytest tests/ -m unit

# Integrációs tesztek
python -m pytest tests/ -m integration

# Coverage report
python -m pytest tests/ --cov=src --cov-report=html

# Párhuzamos futtatás
python -m pytest tests/ -n auto

# Verbose mód
python -m pytest tests/ -v -s
```

## Coverage Célok

- **Minimum coverage**: 80%
- **Unit tesztek**: 90%+
- **Integrációs tesztek**: 70%+
- **Kritikus útvonalak**: 100%

## Tesztelési Stratégia

### 1. Unit Tesztek
- Minden agent és komponens unit teszt-tel
- Mock objektumok használata külső függőségekhez
- Gyors futtatás (< 1 másodperc)

### 2. Integrációs Tesztek
- Komponensek közötti kapcsolatok
- API és adatbázis integrációk
- Workflow tesztelés

### 3. Biztonsági Tesztek
- Input validáció
- Rate limiting
- GDPR compliance
- RLS policy tesztelés

### 4. Teljesítmény Tesztek
- Response time mérés
- Memory usage
- Concurrent request handling

## Best Practices

### 1. Tesztelési Naming
```python
def test_[modul]_[funkció]_[scenario]():
    """Test description."""
    pass
```

### 2. Fixture Használat
```python
@pytest.fixture
def sample_data():
    """Reusable test data."""
    return {"key": "value"}

def test_function(sample_data):
    """Use fixture in test."""
    assert sample_data["key"] == "value"
```

### 3. Async Tesztelés
```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async functions."""
    result = await async_function()
    assert result is not None
```

### 4. Mock Objektumok
```python
@patch('module.external_service')
def test_with_mock(mock_service):
    """Test with mocked external service."""
    mock_service.return_value = "mocked_result"
    result = function_under_test()
    assert result == "mocked_result"
```

## Hibaelhárítás

### Gyakori Problémák

1. **Import hibák**
   ```bash
   export PYTHONPATH=.
   python -m pytest tests/test_imports.py
   ```

2. **Async teszt hibák**
   ```python
   @pytest.mark.asyncio
   async def test_async():
       # Használj @pytest.mark.asyncio dekorátort
       pass
   ```

3. **Mock objektum problémák**
   ```python
   # Használj AsyncMock async függvényekhez
   mock_function = AsyncMock(return_value="result")
   ```

### Debug Mód

```bash
# Debug módban futtatás
python -m pytest tests/ -s --pdb

# Egy teszt debug módban
python -m pytest tests/test_specific.py::test_function -s --pdb
```

## CI/CD Integráció

### GitHub Actions

```yaml
- name: Run Tests
  run: |
    python -m pytest tests/ --cov=src --cov-report=xml
    coverage report --fail-under=80
```

### Pre-commit Hooks

```yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: python -m pytest tests/ -m "not slow"
      language: system
      pass_filenames: false
```

## Monitoring és Reporting

### Coverage Report

```bash
# HTML report generálása
python -m pytest tests/ --cov=src --cov-report=html

# XML report CI-hez
python -m pytest tests/ --cov=src --cov-report=xml
```

### Tesztelési Metrikák

- Teszt futási idő
- Coverage százalék
- Sikeres/sikertelen tesztek
- Teszt kategóriák eloszlása

## Következő Lépések

1. **E2E tesztek hozzáadása**
2. **Performance benchmarking**
3. **Load testing**
4. **Security penetration testing**
5. **Automated visual testing** 