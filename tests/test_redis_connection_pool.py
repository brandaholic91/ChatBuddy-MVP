
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.integrations.cache.redis_connection_pool import (
    OptimizedRedisConnectionPool,
    OptimizedCacheConfig,
    CacheMetrics
)

@pytest.fixture
async def mock_redis_client():
    """Fixture for a mock redis.Redis client"""
    client = MagicMock()
    client.ping = AsyncMock(return_value=True)
    client.info = AsyncMock(return_value={})
    client.setex = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=None)
    client.delete = AsyncMock(return_value=1)
    client.exists = AsyncMock(return_value=0)
    client.expire = AsyncMock(return_value=True)
    client.incr = AsyncMock(return_value=1)
    client.keys = AsyncMock(return_value=[])
    pipe = MagicMock()
    pipe.execute = AsyncMock(return_value=[b'"test_value"', b'{"type": "json", "compressed": false}'])
    client.pipeline.return_value = pipe
    return client

@pytest.fixture
async def connection_pool(mock_redis_client):
    """Fixture for OptimizedRedisConnectionPool"""
    with patch('redis.asyncio.Redis', return_value=mock_redis_client):
        pool = OptimizedRedisConnectionPool()
        pool._redis_client = mock_redis_client
        pool._connected = True
        yield pool

def test_cache_metrics():
    """Test CacheMetrics calculations"""
    metrics = CacheMetrics(hits=10, misses=10, sets=20, compression_saves=5)
    assert metrics.hit_rate == 50.0
    assert metrics.compression_rate == 25.0

@pytest.mark.asyncio
async def test_pool_set_get(connection_pool, mock_redis_client):
    """Test set and get operations"""
    mock_redis_client.get.return_value = b'"test_value"'
    await connection_pool.set("key1", "test_value")
    value = await connection_pool.get("key1")
    assert value == "test_value"

@pytest.mark.asyncio
async def test_pool_delete(connection_pool):
    """Test delete operation"""
    result = await connection_pool.delete("key1")
    assert result is True

@pytest.mark.asyncio
async def test_pool_health_check(connection_pool):
    """Test health check"""
    connection_pool._pool = MagicMock()
    connection_pool._pool.created_connections = 1
    connection_pool._pool._available_connections = [1]
    connection_pool._pool._in_use_connections = []
    health = await connection_pool.health_check()
    assert health['status'] == 'healthy'

@pytest.mark.asyncio
async def test_pool_compression(connection_pool):
    """Test data compression"""
    large_data = b'a' * 2048
    compressed_data, is_compressed = connection_pool._compress_data(large_data)
    assert is_compressed is True
    assert len(compressed_data) < len(large_data)

@pytest.mark.asyncio
async def test_pool_serialization(connection_pool):
    """Test data serialization"""
    data = {'key': 'value'}
    serialized_data = connection_pool._serialize_value(data)
    assert isinstance(serialized_data, bytes)
