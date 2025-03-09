"""
בדיקות יחידה עבור ממשק ה-WooCommerce API
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock, call
import asyncio
import json
from typing import Dict, Any, List, Optional

from src.tools.store.api.woocommerce import WooCommerceAPI, CachedWooCommerceAPI


@pytest_asyncio.fixture
async def woocommerce_api():
    """פיקסצ'ר ליצירת מופע של WooCommerceAPI עם מוקים"""
    # מוק לספריית woocommerce
    with patch('src.tools.store.api.woocommerce.API') as mock_api_class:
        # יצירת מופע של המוק
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        
        # יצירת מופע של WooCommerceAPI עם הגדרות לדוגמה
        api = WooCommerceAPI(
            url="https://example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
            version="v3"
        )
        
        # החזרת ה-API והמוק
        yield api, mock_api


@pytest_asyncio.fixture
async def cached_woocommerce_api():
    """פיקסצ'ר ליצירת מופע של CachedWooCommerceAPI עם מוקים"""
    # מוק לספריית woocommerce
    with patch('src.tools.store.api.woocommerce.API') as mock_api_class:
        # יצירת מופע של המוק
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        
        # יצירת מופע של CachedWooCommerceAPI עם הגדרות לדוגמה
        api = CachedWooCommerceAPI(
            url="https://example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
            version="v3"
        )
        
        # החזרת ה-API והמוק
        yield api, mock_api


@pytest.mark.asyncio
async def test_woocommerce_api_init(woocommerce_api):
    """בדיקת אתחול WooCommerceAPI"""
    api, mock_api = woocommerce_api
    
    # וידוא שה-API אותחל עם הפרמטרים הנכונים
    from src.tools.store.api.woocommerce import API
    API.assert_called_once_with(
        url="https://example.com",
        consumer_key="ck_test",
        consumer_secret="cs_test",
        version="v3",
        timeout=30
    )


@pytest.mark.asyncio
async def test_woocommerce_api_get(woocommerce_api):
    """בדיקת פעולת GET ב-WooCommerceAPI"""
    api, mock_api = woocommerce_api
    
    # הגדרת התנהגות המוק
    mock_api.get.return_value.json.return_value = {"id": 1, "name": "Test"}
    
    # קריאה לפונקציה
    result = await api.get("products/1")
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once_with("products/1", params=None)
    
    # וידוא שהוחזרה התוצאה הנכונה
    assert result == {"id": 1, "name": "Test"}


@pytest.mark.asyncio
async def test_woocommerce_api_get_with_params(woocommerce_api):
    """בדיקת פעולת GET עם פרמטרים ב-WooCommerceAPI"""
    api, mock_api = woocommerce_api
    
    # הגדרת התנהגות המוק
    mock_api.get.return_value.json.return_value = [{"id": 1, "name": "Test"}]
    
    # קריאה לפונקציה עם פרמטרים
    params = {"per_page": 10, "page": 1}
    result = await api.get("products", params=params)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once_with("products", params=params)
    
    # וידוא שהוחזרה התוצאה הנכונה
    assert result == [{"id": 1, "name": "Test"}]


@pytest.mark.asyncio
async def test_woocommerce_api_post(woocommerce_api):
    """בדיקת פעולת POST ב-WooCommerceAPI"""
    api, mock_api = woocommerce_api
    
    # הגדרת התנהגות המוק
    mock_api.post.return_value.json.return_value = {"id": 1, "name": "New Product"}
    
    # נתונים לשליחה
    data = {"name": "New Product", "regular_price": "100.00"}
    
    # קריאה לפונקציה
    result = await api.post("products", data=data)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.post.assert_called_once_with("products", data=data)
    
    # וידוא שהוחזרה התוצאה הנכונה
    assert result == {"id": 1, "name": "New Product"}


@pytest.mark.asyncio
async def test_woocommerce_api_put(woocommerce_api):
    """בדיקת פעולת PUT ב-WooCommerceAPI"""
    api, mock_api = woocommerce_api
    
    # הגדרת התנהגות המוק
    mock_api.put.return_value.json.return_value = {"id": 1, "name": "Updated Product"}
    
    # נתונים לשליחה
    data = {"name": "Updated Product", "regular_price": "120.00"}
    
    # קריאה לפונקציה
    result = await api.put("products/1", data=data)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.put.assert_called_once_with("products/1", data=data)
    
    # וידוא שהוחזרה התוצאה הנכונה
    assert result == {"id": 1, "name": "Updated Product"}


@pytest.mark.asyncio
async def test_woocommerce_api_delete(woocommerce_api):
    """בדיקת פעולת DELETE ב-WooCommerceAPI"""
    api, mock_api = woocommerce_api
    
    # הגדרת התנהגות המוק
    mock_api.delete.return_value.json.return_value = {"id": 1, "name": "Deleted Product"}
    
    # קריאה לפונקציה
    result = await api.delete("products/1")
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.delete.assert_called_once_with("products/1", params=None)
    
    # וידוא שהוחזרה התוצאה הנכונה
    assert result == {"id": 1, "name": "Deleted Product"}


@pytest.mark.asyncio
async def test_woocommerce_api_error_handling(woocommerce_api):
    """בדיקת טיפול בשגיאות ב-WooCommerceAPI"""
    api, mock_api = woocommerce_api
    
    # הגדרת התנהגות המוק - זריקת שגיאה
    mock_api.get.side_effect = Exception("API Error")
    
    # קריאה לפונקציה וציפייה לשגיאה
    with pytest.raises(Exception) as excinfo:
        await api.get("products/1")
    
    # וידוא שהשגיאה הנכונה נזרקה
    assert "API Error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_cached_woocommerce_api_init(cached_woocommerce_api):
    """בדיקת אתחול CachedWooCommerceAPI"""
    api, mock_api = cached_woocommerce_api
    
    # וידוא שה-API אותחל עם הפרמטרים הנכונים
    from src.tools.store.api.woocommerce import API
    API.assert_called_once_with(
        url="https://example.com",
        consumer_key="ck_test",
        consumer_secret="cs_test",
        version="v3",
        timeout=30
    )
    
    # וידוא שהמטמון אותחל כראוי
    assert api._cache == {}
    assert api._cache_ttl == 300  # ברירת מחדל


@pytest.mark.asyncio
async def test_cached_woocommerce_api_get_no_cache(cached_woocommerce_api):
    """בדיקת פעולת GET ללא מטמון ב-CachedWooCommerceAPI"""
    api, mock_api = cached_woocommerce_api
    
    # הגדרת התנהגות המוק
    mock_api.get.return_value.json.return_value = {"id": 1, "name": "Test"}
    
    # קריאה לפונקציה
    result = await api.get("products/1")
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once_with("products/1", params=None)
    
    # וידוא שהוחזרה התוצאה הנכונה
    assert result == {"id": 1, "name": "Test"}
    
    # וידוא שהתוצאה נשמרה במטמון
    cache_key = "GET:products/1:None"
    assert cache_key in api._cache
    assert api._cache[cache_key]["data"] == {"id": 1, "name": "Test"}


@pytest.mark.asyncio
async def test_cached_woocommerce_api_get_from_cache(cached_woocommerce_api):
    """בדיקת פעולת GET מהמטמון ב-CachedWooCommerceAPI"""
    api, mock_api = cached_woocommerce_api
    
    # הגדרת מטמון עם נתונים
    cache_key = "GET:products/1:None"
    api._cache[cache_key] = {
        "data": {"id": 1, "name": "Cached Test"},
        "timestamp": asyncio.get_event_loop().time() + 3600  # שעה מעכשיו
    }
    
    # קריאה לפונקציה
    result = await api.get("products/1")
    
    # וידוא שהפונקציה לא נקראה (כי השתמשנו במטמון)
    mock_api.get.assert_not_called()
    
    # וידוא שהוחזרה התוצאה מהמטמון
    assert result == {"id": 1, "name": "Cached Test"}


@pytest.mark.asyncio
async def test_cached_woocommerce_api_get_expired_cache(cached_woocommerce_api):
    """בדיקת פעולת GET עם מטמון שפג תוקפו ב-CachedWooCommerceAPI"""
    api, mock_api = cached_woocommerce_api
    
    # הגדרת מטמון עם נתונים שפג תוקפם
    cache_key = "GET:products/1:None"
    api._cache[cache_key] = {
        "data": {"id": 1, "name": "Expired Cached Test"},
        "timestamp": asyncio.get_event_loop().time() - 3600  # שעה לפני
    }
    
    # הגדרת התנהגות המוק לנתונים חדשים
    mock_api.get.return_value.json.return_value = {"id": 1, "name": "Fresh Test"}
    
    # קריאה לפונקציה
    result = await api.get("products/1")
    
    # וידוא שהפונקציה נקראה (כי המטמון פג תוקף)
    mock_api.get.assert_called_once_with("products/1", params=None)
    
    # וידוא שהוחזרה התוצאה החדשה
    assert result == {"id": 1, "name": "Fresh Test"}
    
    # וידוא שהמטמון עודכן
    assert api._cache[cache_key]["data"] == {"id": 1, "name": "Fresh Test"}


@pytest.mark.asyncio
async def test_cached_woocommerce_api_post_bypasses_cache(cached_woocommerce_api):
    """בדיקה שפעולת POST עוקפת את המטמון ב-CachedWooCommerceAPI"""
    api, mock_api = cached_woocommerce_api
    
    # הגדרת התנהגות המוק
    mock_api.post.return_value.json.return_value = {"id": 1, "name": "New Product"}
    
    # נתונים לשליחה
    data = {"name": "New Product", "regular_price": "100.00"}
    
    # קריאה לפונקציה
    result = await api.post("products", data=data)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.post.assert_called_once_with("products", data=data)
    
    # וידוא שהוחזרה התוצאה הנכונה
    assert result == {"id": 1, "name": "New Product"}
    
    # וידוא שאין מטמון לפעולת POST
    cache_key = "POST:products:{\"name\": \"New Product\", \"regular_price\": \"100.00\"}"
    assert cache_key not in api._cache


@pytest.mark.asyncio
async def test_cached_woocommerce_api_put_invalidates_cache(cached_woocommerce_api):
    """בדיקה שפעולת PUT מבטלת את המטמון הרלוונטי ב-CachedWooCommerceAPI"""
    api, mock_api = cached_woocommerce_api
    
    # הגדרת מטמון עם נתונים
    get_cache_key = "GET:products/1:None"
    api._cache[get_cache_key] = {
        "data": {"id": 1, "name": "Old Product"},
        "timestamp": asyncio.get_event_loop().time() + 3600  # שעה מעכשיו
    }
    
    # הגדרת התנהגות המוק
    mock_api.put.return_value.json.return_value = {"id": 1, "name": "Updated Product"}
    
    # נתונים לשליחה
    data = {"name": "Updated Product", "regular_price": "120.00"}
    
    # קריאה לפונקציה
    result = await api.put("products/1", data=data)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.put.assert_called_once_with("products/1", data=data)
    
    # וידוא שהוחזרה התוצאה הנכונה
    assert result == {"id": 1, "name": "Updated Product"}
    
    # וידוא שהמטמון הרלוונטי בוטל
    assert get_cache_key not in api._cache


@pytest.mark.asyncio
async def test_cached_woocommerce_api_delete_invalidates_cache(cached_woocommerce_api):
    """בדיקה שפעולת DELETE מבטלת את המטמון הרלוונטי ב-CachedWooCommerceAPI"""
    api, mock_api = cached_woocommerce_api
    
    # הגדרת מטמון עם נתונים
    get_cache_key = "GET:products/1:None"
    api._cache[get_cache_key] = {
        "data": {"id": 1, "name": "Product To Delete"},
        "timestamp": asyncio.get_event_loop().time() + 3600  # שעה מעכשיו
    }
    
    # הגדרת התנהגות המוק
    mock_api.delete.return_value.json.return_value = {"id": 1, "name": "Deleted Product"}
    
    # קריאה לפונקציה
    result = await api.delete("products/1")
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.delete.assert_called_once_with("products/1", params=None)
    
    # וידוא שהוחזרה התוצאה הנכונה
    assert result == {"id": 1, "name": "Deleted Product"}
    
    # וידוא שהמטמון הרלוונטי בוטל
    assert get_cache_key not in api._cache


@pytest.mark.asyncio
async def test_cached_woocommerce_api_clear_cache(cached_woocommerce_api):
    """בדיקת ניקוי המטמון ב-CachedWooCommerceAPI"""
    api, mock_api = cached_woocommerce_api
    
    # הגדרת מטמון עם מספר נתונים
    api._cache = {
        "GET:products/1:None": {
            "data": {"id": 1, "name": "Product 1"},
            "timestamp": asyncio.get_event_loop().time() + 3600
        },
        "GET:products/2:None": {
            "data": {"id": 2, "name": "Product 2"},
            "timestamp": asyncio.get_event_loop().time() + 3600
        }
    }
    
    # קריאה לפונקציה
    api.clear_cache()
    
    # וידוא שהמטמון נוקה
    assert api._cache == {}


@pytest.mark.asyncio
async def test_cached_woocommerce_api_clear_cache_pattern(cached_woocommerce_api):
    """בדיקת ניקוי המטמון לפי תבנית ב-CachedWooCommerceAPI"""
    api, mock_api = cached_woocommerce_api
    
    # הגדרת מטמון עם מספר נתונים
    api._cache = {
        "GET:products/1:None": {
            "data": {"id": 1, "name": "Product 1"},
            "timestamp": asyncio.get_event_loop().time() + 3600
        },
        "GET:products/2:None": {
            "data": {"id": 2, "name": "Product 2"},
            "timestamp": asyncio.get_event_loop().time() + 3600
        },
        "GET:orders/1:None": {
            "data": {"id": 1, "order_number": "1001"},
            "timestamp": asyncio.get_event_loop().time() + 3600
        }
    }
    
    # קריאה לפונקציה עם תבנית
    api.clear_cache("products")
    
    # וידוא שרק המטמון הרלוונטי נוקה
    assert "GET:products/1:None" not in api._cache
    assert "GET:products/2:None" not in api._cache
    assert "GET:orders/1:None" in api._cache 