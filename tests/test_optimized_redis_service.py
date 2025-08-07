
import pytest
from unittest.mock import MagicMock, AsyncMock

from src.integrations.cache.optimized_redis_service import (
    OptimizedRedisCacheService, 
    OptimizedSessionCache, 
    OptimizedPerformanceCache, 
    OptimizedRateLimitCache,
    OptimizedSessionData
)

@pytest.fixture
async def mock_pool():
    """Fixture for a mock OptimizedRedisConnectionPool"""
    pool = MagicMock()
    pool.get = AsyncMock(return_value=None)
    pool.set = AsyncMock(return_value=True)
    pool.delete = AsyncMock(return_value=True)
    pool.incr = AsyncMock(return_value=1)
    pool.expire = AsyncMock(return_value=True)
    pool.get_performance_stats = AsyncMock(return_value={})
    pool.health_check = AsyncMock(return_value={"status": "healthy"})
    pool.config.session_ttl = 3600
    return pool

@pytest.fixture
async def session_cache(mock_pool):
    """Fixture for OptimizedSessionCache"""
    return OptimizedSessionCache(mock_pool)

@pytest.fixture
async def performance_cache(mock_pool):
    """Fixture for OptimizedPerformanceCache"""
    return OptimizedPerformanceCache(mock_pool)

@pytest.fixture
async def rate_limit_cache(mock_pool):
    """Fixture for OptimizedRateLimitCache"""
    return OptimizedRateLimitCache(mock_pool)

@pytest.mark.asyncio
async def test_create_session(session_cache, mock_pool):
    """Test session creation"""
    session_id = await session_cache.create_session("user1")
    assert session_id is not None
    mock_pool.set.assert_called()

@pytest.mark.asyncio
async def test_get_session(session_cache, mock_pool):
    """Test getting a session"""
    mock_pool.get.return_value = OptimizedSessionData(session_id="sid", user_id="uid").to_dict()
    session = await session_cache.get_session("session1")
    assert session is not None
    assert session.session_id == "sid"

@pytest.mark.asyncio
async def test_cache_agent_response(performance_cache, mock_pool):
    """Test caching agent response"""
    await performance_cache.cache_agent_response("hash1", {"data": "response"})
    mock_pool.set.assert_called_with(key="hash1", value={"data": "response"}, cache_type='agent_response')

@pytest.mark.asyncio
async def test_check_rate_limit_allowed(rate_limit_cache, mock_pool):
    """Test rate limit check when allowed"""
    result = await rate_limit_cache.check_rate_limit("id1", "type1", 10, 60)
    assert result["allowed"] is True

@pytest.mark.asyncio
async def test_check_rate_limit_denied(rate_limit_cache, mock_pool):
    """Test rate limit check when denied"""
    mock_pool.get.return_value = 10
    result = await rate_limit_cache.check_rate_limit("id1", "type1", 10, 60)
    assert result["allowed"] is False

@pytest.mark.asyncio
async def test_service_get_instance():
    """Test singleton instance retrieval"""
    service1 = await OptimizedRedisCacheService.get_instance()
    service2 = await OptimizedRedisCacheService.get_instance()
    assert service1 is service2

@pytest.mark.asyncio
async def test_service_health_check(mock_pool):
    """Test service health check"""
    service = OptimizedRedisCacheService()
    service.pool = mock_pool
    health = await service.health_check()
    assert health["status"] == "healthy"
