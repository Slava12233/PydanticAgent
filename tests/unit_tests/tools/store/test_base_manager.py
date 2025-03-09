"""
בדיקות יחידה למודול base_manager.py
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json

from src.tools.store.managers.base_manager import BaseManager
from src.services.store.woocommerce.api.woocommerce_api import WooCommerceAPI


class TestBaseManager(BaseManager):
    """מחלקת בדיקה שיורשת מ-BaseManager לצורך בדיקת הפונקציונליות"""
    
    def _get_resource_name(self) -> str:
        return "test_resource"


@pytest_asyncio.fixture
async def base_manager():
    """יוצר מופע של TestBaseManager עם API מדומה"""
    mock_api = AsyncMock(spec=WooCommerceAPI)
    mock_api.get = AsyncMock()
    mock_api.post = AsyncMock()
    mock_api.put = AsyncMock()
    mock_api.delete = AsyncMock()
    
    manager = TestBaseManager(api=mock_api, use_cache=True)
    return manager


@pytest.mark.asyncio
async def test_init_with_api(base_manager):
    """בודק שהאתחול עם API עובד כראוי"""
    assert base_manager.api is not None
    assert base_manager.use_cache is True
    assert base_manager.cache == {}
    assert base_manager.cache_expiry == {}


@pytest.mark.asyncio
async def test_init_without_api():
    """בודק שהאתחול ללא API יוצר API חדש"""
    with patch('src.tools.store.managers.base_manager.get_cached_woocommerce_api') as mock_get_api:
        mock_api = AsyncMock(spec=WooCommerceAPI)
        mock_get_api.return_value = mock_api
        
        manager = TestBaseManager(use_cache=True)
        
        mock_get_api.assert_called_once()
        assert manager.api is mock_api


@pytest.mark.asyncio
async def test_get_resource_name(base_manager):
    """בודק שהפונקציה _get_resource_name מחזירה את הערך הנכון"""
    assert base_manager._get_resource_name() == "test_resource"


@pytest.mark.asyncio
async def test_get_from_api(base_manager):
    """בודק שהפונקציה _get_from_api קוראת ל-API.get עם הפרמטרים הנכונים"""
    mock_response = {"id": 1, "name": "Test"}
    base_manager.api.get.return_value = mock_response
    
    result = await base_manager._get_from_api("test_resource/1")
    
    base_manager.api.get.assert_called_once_with("test_resource/1", {})
    assert result == mock_response


@pytest.mark.asyncio
async def test_get_from_api_with_params(base_manager):
    """בודק שהפונקציה _get_from_api מעבירה פרמטרים נכון"""
    mock_response = [{"id": 1, "name": "Test"}]
    base_manager.api.get.return_value = mock_response
    params = {"per_page": 10, "page": 1}
    
    result = await base_manager._get_from_api("test_resource", params)
    
    base_manager.api.get.assert_called_once_with("test_resource", params)
    assert result == mock_response


@pytest.mark.asyncio
async def test_get_from_api_error(base_manager):
    """בודק שהפונקציה _get_from_api מטפלת בשגיאות כראוי"""
    base_manager.api.get.side_effect = Exception("API Error")
    
    result = await base_manager._get_from_api("test_resource/1")
    
    base_manager.api.get.assert_called_once()
    assert result is None


@pytest.mark.asyncio
async def test_post_to_api(base_manager):
    """בודק שהפונקציה _post_to_api קוראת ל-API.post עם הפרמטרים הנכונים"""
    mock_response = {"id": 1, "name": "Test"}
    base_manager.api.post.return_value = mock_response
    data = {"name": "Test"}
    
    result = await base_manager._post_to_api("test_resource", data)
    
    base_manager.api.post.assert_called_once_with("test_resource", data)
    assert result == mock_response


@pytest.mark.asyncio
async def test_post_to_api_error(base_manager):
    """בודק שהפונקציה _post_to_api מטפלת בשגיאות כראוי"""
    base_manager.api.post.side_effect = Exception("API Error")
    data = {"name": "Test"}
    
    result = await base_manager._post_to_api("test_resource", data)
    
    base_manager.api.post.assert_called_once()
    assert result is None


@pytest.mark.asyncio
async def test_put_to_api(base_manager):
    """בודק שהפונקציה _put_to_api קוראת ל-API.put עם הפרמטרים הנכונים"""
    mock_response = {"id": 1, "name": "Updated Test"}
    base_manager.api.put.return_value = mock_response
    data = {"name": "Updated Test"}
    
    result = await base_manager._put_to_api("test_resource/1", data)
    
    base_manager.api.put.assert_called_once_with("test_resource/1", data)
    assert result == mock_response


@pytest.mark.asyncio
async def test_put_to_api_error(base_manager):
    """בודק שהפונקציה _put_to_api מטפלת בשגיאות כראוי"""
    base_manager.api.put.side_effect = Exception("API Error")
    data = {"name": "Updated Test"}
    
    result = await base_manager._put_to_api("test_resource/1", data)
    
    base_manager.api.put.assert_called_once()
    assert result is None


@pytest.mark.asyncio
async def test_delete_from_api(base_manager):
    """בודק שהפונקציה _delete_from_api קוראת ל-API.delete עם הפרמטרים הנכונים"""
    mock_response = {"id": 1, "status": "trash"}
    base_manager.api.delete.return_value = mock_response
    
    result = await base_manager._delete_from_api("test_resource/1")
    
    base_manager.api.delete.assert_called_once_with("test_resource/1", {})
    assert result == mock_response


@pytest.mark.asyncio
async def test_delete_from_api_with_params(base_manager):
    """בודק שהפונקציה _delete_from_api מעבירה פרמטרים נכון"""
    mock_response = {"id": 1, "status": "trash"}
    base_manager.api.delete.return_value = mock_response
    params = {"force": True}
    
    result = await base_manager._delete_from_api("test_resource/1", params)
    
    base_manager.api.delete.assert_called_once_with("test_resource/1", params)
    assert result == mock_response


@pytest.mark.asyncio
async def test_delete_from_api_error(base_manager):
    """בודק שהפונקציה _delete_from_api מטפלת בשגיאות כראוי"""
    base_manager.api.delete.side_effect = Exception("API Error")
    
    result = await base_manager._delete_from_api("test_resource/1")
    
    base_manager.api.delete.assert_called_once()
    assert result is None


@pytest.mark.asyncio
async def test_get_from_cache_hit(base_manager):
    """בודק שהפונקציה _get_from_cache מחזירה ערך מהמטמון כאשר הוא קיים ותקף"""
    cache_key = "test_resource/1"
    cache_data = {"id": 1, "name": "Test"}
    base_manager.cache[cache_key] = cache_data
    base_manager.cache_expiry[cache_key] = datetime.now() + timedelta(minutes=10)
    
    result = base_manager._get_from_cache(cache_key)
    
    assert result == cache_data


@pytest.mark.asyncio
async def test_get_from_cache_miss_not_exists(base_manager):
    """בודק שהפונקציה _get_from_cache מחזירה None כאשר המפתח לא קיים במטמון"""
    result = base_manager._get_from_cache("test_resource/1")
    
    assert result is None


@pytest.mark.asyncio
async def test_get_from_cache_miss_expired(base_manager):
    """בודק שהפונקציה _get_from_cache מחזירה None כאשר המטמון פג תוקף"""
    cache_key = "test_resource/1"
    cache_data = {"id": 1, "name": "Test"}
    base_manager.cache[cache_key] = cache_data
    base_manager.cache_expiry[cache_key] = datetime.now() - timedelta(minutes=10)
    
    result = base_manager._get_from_cache(cache_key)
    
    assert result is None


@pytest.mark.asyncio
async def test_set_cache(base_manager):
    """בודק שהפונקציה _set_cache מאחסנת ערך במטמון עם תאריך תפוגה נכון"""
    cache_key = "test_resource/1"
    cache_data = {"id": 1, "name": "Test"}
    
    base_manager._set_cache(cache_key, cache_data)
    
    assert base_manager.cache[cache_key] == cache_data
    assert cache_key in base_manager.cache_expiry
    # בדיקה שתאריך התפוגה הוא בעתיד
    assert base_manager.cache_expiry[cache_key] > datetime.now()


@pytest.mark.asyncio
async def test_invalidate_cache(base_manager):
    """בודק שהפונקציה _invalidate_cache מוחקת ערך מהמטמון"""
    cache_key = "test_resource/1"
    cache_data = {"id": 1, "name": "Test"}
    base_manager.cache[cache_key] = cache_data
    base_manager.cache_expiry[cache_key] = datetime.now() + timedelta(minutes=10)
    
    base_manager._invalidate_cache(cache_key)
    
    assert cache_key not in base_manager.cache
    assert cache_key not in base_manager.cache_expiry


@pytest.mark.asyncio
async def test_invalidate_cache_pattern(base_manager):
    """בודק שהפונקציה _invalidate_cache_pattern מוחקת ערכים מהמטמון לפי תבנית"""
    base_manager.cache = {
        "test_resource/1": {"id": 1, "name": "Test1"},
        "test_resource/2": {"id": 2, "name": "Test2"},
        "other_resource/1": {"id": 1, "name": "Other"}
    }
    base_manager.cache_expiry = {
        "test_resource/1": datetime.now() + timedelta(minutes=10),
        "test_resource/2": datetime.now() + timedelta(minutes=10),
        "other_resource/1": datetime.now() + timedelta(minutes=10)
    }
    
    base_manager._invalidate_cache_pattern("test_resource")
    
    assert "test_resource/1" not in base_manager.cache
    assert "test_resource/2" not in base_manager.cache
    assert "other_resource/1" in base_manager.cache
    
    assert "test_resource/1" not in base_manager.cache_expiry
    assert "test_resource/2" not in base_manager.cache_expiry
    assert "other_resource/1" in base_manager.cache_expiry


@pytest.mark.asyncio
async def test_clear_cache(base_manager):
    """בודק שהפונקציה _clear_cache מוחקת את כל המטמון"""
    base_manager.cache = {
        "test_resource/1": {"id": 1, "name": "Test1"},
        "other_resource/1": {"id": 1, "name": "Other"}
    }
    base_manager.cache_expiry = {
        "test_resource/1": datetime.now() + timedelta(minutes=10),
        "other_resource/1": datetime.now() + timedelta(minutes=10)
    }
    
    base_manager._clear_cache()
    
    assert base_manager.cache == {}
    assert base_manager.cache_expiry == {}


@pytest.mark.asyncio
async def test_get_with_cache_hit(base_manager):
    """בודק שהפונקציה _get_with_cache מחזירה ערך מהמטמון כאשר הוא קיים"""
    cache_key = "test_resource/1"
    cache_data = {"id": 1, "name": "Test"}
    base_manager.cache[cache_key] = cache_data
    base_manager.cache_expiry[cache_key] = datetime.now() + timedelta(minutes=10)
    
    result = await base_manager._get_with_cache(cache_key)
    
    assert result == cache_data
    # וודא שלא הייתה קריאה ל-API
    base_manager.api.get.assert_not_called()


@pytest.mark.asyncio
async def test_get_with_cache_miss(base_manager):
    """בודק שהפונקציה _get_with_cache קוראת ל-API כאשר הערך לא קיים במטמון"""
    cache_key = "test_resource/1"
    api_data = {"id": 1, "name": "Test"}
    base_manager.api.get.return_value = api_data
    
    result = await base_manager._get_with_cache(cache_key)
    
    assert result == api_data
    base_manager.api.get.assert_called_once_with(cache_key, {})
    # וודא שהערך נשמר במטמון
    assert base_manager.cache[cache_key] == api_data
    assert cache_key in base_manager.cache_expiry


@pytest.mark.asyncio
async def test_get_with_cache_disabled(base_manager):
    """בודק שהפונקציה _get_with_cache קוראת ל-API כאשר המטמון מושבת"""
    base_manager.use_cache = False
    cache_key = "test_resource/1"
    cache_data = {"id": 1, "name": "Test"}
    api_data = {"id": 1, "name": "API Test"}
    
    # הוסף נתונים למטמון
    base_manager.cache[cache_key] = cache_data
    base_manager.cache_expiry[cache_key] = datetime.now() + timedelta(minutes=10)
    
    base_manager.api.get.return_value = api_data
    
    result = await base_manager._get_with_cache(cache_key)
    
    assert result == api_data  # צריך להחזיר את הנתונים מה-API, לא מהמטמון
    base_manager.api.get.assert_called_once_with(cache_key, {}) 