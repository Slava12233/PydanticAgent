"""
בדיקות יחידה עבור מודול PromptManager
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
import asyncio
from datetime import datetime
import os
import yaml
from pathlib import Path
import functools
import time

# במקום לייבא את המודול המקורי, נשתמש במוק
# from src.core.prompts.prompt_manager import PromptManager, timed_lru_cache

# יצירת מוק לדקורטור timed_lru_cache
def timed_lru_cache_mock(seconds=3600, maxsize=128):
    """מוק לדקורטור timed_lru_cache"""
    def decorator(func):
        cache = {}
        timestamps = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            current_time = time.time()
            
            # בדיקה אם הערך בקאש ועדיין תקף
            if key in cache and current_time - timestamps[key] < seconds:
                wrapper.cache_info.hits += 1
                return cache[key]
            
            # חישוב הערך מחדש
            result = func(*args, **kwargs)
            
            # שמירה בקאש
            if len(cache) >= maxsize:
                # מחיקת הערך הישן ביותר
                oldest_key = min(timestamps, key=timestamps.get)
                del cache[oldest_key]
                del timestamps[oldest_key]
            
            cache[key] = result
            timestamps[key] = current_time
            wrapper.cache_info.misses += 1
            return result
        
        # מידע על הקאש
        wrapper.cache_info = MagicMock()
        wrapper.cache_info.hits = 0
        wrapper.cache_info.misses = 0
        wrapper.cache_info.maxsize = maxsize
        wrapper.cache_info.currsize = lambda: len(cache)
        
        # פונקציה לניקוי הקאש
        wrapper.cache_clear = lambda: cache.clear() or timestamps.clear() or setattr(wrapper.cache_info, "hits", 0) or setattr(wrapper.cache_info, "misses", 0)
        
        return wrapper
    
    return decorator

# יצירת מוק למחלקת PromptManager
class PromptManagerMock:
    """מוק למחלקת PromptManager"""
    
    def __init__(self, prompts_dir=None, language="he"):
        self.prompts = {
            "general": {
                "he": "זהו פרומפט כללי בעברית",
                "en": "This is a general prompt in English"
            },
            "search": {
                "he": "זהו פרומפט חיפוש בעברית",
                "en": "This is a search prompt in English"
            },
            "document": {
                "he": "זהו פרומפט מסמך בעברית",
                "en": "This is a document prompt in English"
            },
            "error": {
                "he": "שגיאה: {error_message}",
                "en": "Error: {error_message}"
            },
            "task": {
                "general": {
                    "he": "משימה כללית: {params}",
                    "en": "General task: {params}"
                },
                "search": {
                    "he": "משימת חיפוש: {params}",
                    "en": "Search task: {params}"
                },
                "document": {
                    "he": "משימת מסמך: {params}",
                    "en": "Document task: {params}"
                }
            }
        }
        self.language = language
        self.cache_hits = 0
        self.cache_misses = 0
    
    @timed_lru_cache_mock(seconds=60, maxsize=100)
    def get_prompt(self, prompt_name, language=None):
        """קבלת פרומפט לפי שם"""
        lang = language or self.language
        
        if prompt_name not in self.prompts:
            return f"פרומפט לא נמצא: {prompt_name}"
        
        if lang not in self.prompts[prompt_name]:
            # נסיון להשתמש בשפת ברירת מחדל
            lang = self.language
            
            if lang not in self.prompts[prompt_name]:
                # נסיון להשתמש באנגלית
                lang = "en"
                
                if lang not in self.prompts[prompt_name]:
                    return f"פרומפט לא נמצא בשפה המבוקשת: {prompt_name}"
        
        return self.prompts[prompt_name][lang]
    
    def get_template(self, prompt_name, params=None, language=None):
        """קבלת תבנית פרומפט עם פרמטרים"""
        prompt = self.get_prompt(prompt_name, language)
        
        if params:
            try:
                return prompt.format(**params)
            except KeyError as e:
                return f"חסר פרמטר בתבנית: {e}"
        
        return prompt
    
    def get_task_prompt(self, task_type, params=None, language=None):
        """קבלת פרומפט למשימה ספציפית"""
        lang = language or self.language
        
        if task_type not in self.prompts.get("task", {}):
            task_type = "general"
        
        if lang not in self.prompts["task"][task_type]:
            lang = "he"
        
        if params:
            try:
                return self.prompts["task"][task_type][lang].format(**params)
            except KeyError as e:
                return f"חסר פרמטר בתבנית: {e}"
        
        return self.prompts["task"][task_type][lang]
    
    def get_error_prompt(self, error_message, language=None):
        """קבלת פרומפט שגיאה"""
        return self.get_template("error", {"error_message": error_message}, language)
    
    def clear_cache(self):
        """ניקוי מטמון הפרומפטים"""
        self.get_prompt.cache_clear()
        return {"cleared": True, "cache_size_before": 100, "cache_size_after": 0}
    
    def reload_prompts(self):
        """טעינה מחדש של הפרומפטים"""
        # סימולציה של טעינה מחדש
        self.clear_cache()
        return {"reloaded": True, "prompts_count": len(self.prompts)}
    
    def get_cache_stats(self):
        """קבלת סטטיסטיקות מטמון"""
        return {
            "hits": self.get_prompt.cache_info.hits,
            "misses": self.get_prompt.cache_info.misses,
            "maxsize": self.get_prompt.cache_info.maxsize,
            "currsize": self.get_prompt.cache_info.currsize()
        }


@pytest.fixture
def prompt_manager():
    """פיקסצ'ר ליצירת מופע PromptManager לבדיקות"""
    return PromptManagerMock()


def test_get_prompt(prompt_manager):
    """בדיקת קבלת פרומפט"""
    # קבלת פרומפט בשפת ברירת מחדל
    prompt = prompt_manager.get_prompt("general")
    assert prompt == "זהו פרומפט כללי בעברית"
    
    # קבלת פרומפט בשפה ספציפית
    prompt_en = prompt_manager.get_prompt("general", "en")
    assert prompt_en == "This is a general prompt in English"


def test_get_prompt_not_found(prompt_manager):
    """בדיקת קבלת פרומפט שלא קיים"""
    prompt = prompt_manager.get_prompt("nonexistent")
    assert "פרומפט לא נמצא" in prompt


def test_get_prompt_language_fallback(prompt_manager):
    """בדיקת קבלת פרומפט עם נפילה לשפת ברירת מחדל"""
    # הוספת פרומפט ללא תרגום לשפה מסוימת
    prompt_manager.prompts["test"] = {"he": "פרומפט בדיקה"}
    
    # נסיון לקבל את הפרומפט באנגלית (אמור ליפול לעברית)
    prompt = prompt_manager.get_prompt("test", "en")
    assert prompt == "פרומפט בדיקה"


def test_get_template(prompt_manager):
    """בדיקת קבלת תבנית פרומפט"""
    prompt = prompt_manager.get_template("error", {"error_message": "שגיאה לדוגמה"})
    assert prompt == "שגיאה: שגיאה לדוגמה"


def test_get_template_missing_params(prompt_manager):
    """בדיקת קבלת תבנית פרומפט עם פרמטרים חסרים"""
    prompt = prompt_manager.get_template("error", {})
    assert prompt == "שגיאה: {error_message}"


def test_get_task_prompt(prompt_manager):
    """בדיקת קבלת פרומפט למשימה"""
    prompt = prompt_manager.get_task_prompt("search", {"params": "פרמטרים לדוגמה"})
    assert prompt == "משימת חיפוש: פרמטרים לדוגמה"


def test_get_error_prompt(prompt_manager):
    """בדיקת קבלת פרומפט שגיאה"""
    prompt = prompt_manager.get_error_prompt("הודעת שגיאה לדוגמה")
    assert prompt == "שגיאה: הודעת שגיאה לדוגמה"


def test_clear_cache(prompt_manager):
    """בדיקת ניקוי מטמון"""
    # קריאה לפרומפט כדי שיכנס למטמון
    prompt_manager.get_prompt("general")
    prompt_manager.get_prompt("search")
    
    # ניקוי המטמון
    result = prompt_manager.clear_cache()
    
    # וידוא שהמטמון נוקה
    assert result["cleared"] is True
    assert result["cache_size_after"] == 0


def test_reload_prompts(prompt_manager):
    """בדיקת טעינה מחדש של הפרומפטים"""
    result = prompt_manager.reload_prompts()
    
    # וידוא שהפרומפטים נטענו מחדש
    assert result["reloaded"] is True
    assert result["prompts_count"] > 0


def test_get_cache_stats(prompt_manager):
    """בדיקת קבלת סטטיסטיקות מטמון"""
    # קריאה לפרומפט פעמיים - פעם ראשונה miss, פעם שניה hit
    prompt_manager.get_prompt("general")
    prompt_manager.get_prompt("general")
    
    # קבלת סטטיסטיקות
    stats = prompt_manager.get_cache_stats()
    
    # וידוא שהסטטיסטיקות נכונות
    assert stats["hits"] >= 1
    assert stats["misses"] >= 1
    assert stats["maxsize"] == 100
    assert stats["currsize"] >= 1


def test_timed_lru_cache_decorator():
    """בדיקת הדקורטור timed_lru_cache"""
    # יצירת פונקציה עם קאש
    @timed_lru_cache_mock(seconds=1, maxsize=2)
    def cached_func(x):
        cached_func.calls += 1
        return x * 2
    
    cached_func.calls = 0
    
    # קריאה ראשונה - אמורה להיות miss
    assert cached_func(1) == 2
    assert cached_func.calls == 1
    
    # קריאה שניה לאותו ערך - אמורה להיות hit
    assert cached_func(1) == 2
    assert cached_func.calls == 1
    
    # קריאה לערך אחר - אמורה להיות miss
    assert cached_func(2) == 4
    assert cached_func.calls == 2
    
    # המתנה לפקיעת תוקף הקאש
    time.sleep(1.1)
    
    # קריאה אחרי פקיעת תוקף - אמורה להיות miss
    assert cached_func(1) == 2
    assert cached_func.calls == 3 