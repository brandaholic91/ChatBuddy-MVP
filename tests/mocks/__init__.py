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

class MockLLMResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)

class MockMessage:
    def __init__(self, content):
        self.content = content

# Supabase Mocks
class MockSupabaseClient:
    def table(self, name): return MockTable(name)
    def auth(self): return MockAuth()
    def execute_query(self, query): return True # Simplified for now
    def check_rls_enabled(self, table_name): return True # Simplified for now
    def get_table_info(self, table_name): return [] # Simplified for now
    def enable_pgvector_extension(self): return True # Simplified for now
    def check_pgvector_extension(self): return True # Simplified for now
    def check_vector_functions(self): return True # Simplified for now
    def check_vector_indexes(self): return True # Simplified for now
    def table_exists(self, table_name): return True # Simplified for now

class MockTable:
    def __init__(self, name):
        self.name = name
    def select(self, columns): return self
    def eq(self, column, value): return self
    def order(self, column, desc): return self
    def limit(self, count): return self
    def execute(self): return MockResponse()
    def update(self, data): return self
    def or_(self, *args): return self

class MockAuth:
    pass

class MockResponse:
    def __init__(self, data=None):
        self.data = data if data is not None else []

# Redis Mocks
class MockRedisClient:
    def __init__(self): self._data = {}
    async def get(self, key): return self._data.get(key)
    async def set(self, key, value): self._data[key] = value
    async def close(self): pass
    async def ping(self): return True

# WebShop Integration Mocks
from unittest.mock import AsyncMock

class MockWebShopAPI:
    def __init__(self):
        # Define AsyncMock methods so that tests can override `.return_value` safely
        self.get_products = AsyncMock(return_value=[{"id": 1, "name": "Test Product"}])
        self.get_orders = AsyncMock(return_value=[{"id": 1, "status": "completed"}])
        self.search_products = AsyncMock(return_value=[{"id": 2, "name": "Searched Product", "price": 100.0}])
        self.get_product = AsyncMock(return_value={"id": "prod_1", "name": "Single Product", "price": 50.0})
        self.update_order_status = AsyncMock(return_value=True)
