"""
מנהל הפרומפטים של המערכת
"""
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import yaml
from functools import lru_cache, wraps

from src.models.responses import ServiceResponse

logger = logging.getLogger(__name__)

# מנגנון קאשינג עם תמיכה בפקיעת תוקף
def timed_lru_cache(seconds: int, maxsize: int = 128):
    """
    מנגנון קאשינג עם תמיכה בפקיעת תוקף
    
    Args:
        seconds: זמן פקיעת תוקף בשניות
        maxsize: גודל מקסימלי של הקאש
        
    Returns:
        פונקציית עטיפה
    """
    def wrapper_cache(func):
        # שימוש ב-LRU cache רגיל
        func = lru_cache(maxsize=maxsize)(func)
        
        # שמירת זמן הפקיעה
        func.expiration = seconds
        # שמירת זמן הטעינה האחרונה
        func.last_clear_time = time.time()
        
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            # בדיקה אם הקאש פג תוקף
            if time.time() - func.last_clear_time > func.expiration:
                func.cache_clear()
                func.last_clear_time = time.time()
                
            return func(*args, **kwargs)
        
        # העברת פונקציות ניקוי הקאש
        wrapped_func.cache_clear = func.cache_clear
        wrapped_func.cache_info = func.cache_info
        
        return wrapped_func
    
    return wrapper_cache

class PromptManager:
    """מנהל הפרומפטים של המערכת"""
    
    def __init__(self, base_dir: Optional[str] = None, cache_ttl: int = 3600):
        """
        אתחול מנהל הפרומפטים
        
        Args:
            base_dir: תיקיית הבסיס (אופציונלי)
            cache_ttl: זמן פקיעת תוקף הקאש בשניות (ברירת מחדל: שעה)
        """
        if base_dir is None:
            base_dir = Path(__file__).parent
        
        self.base_dir = Path(base_dir)
        self.config_dir = self.base_dir / "config"
        self.templates_dir = self.base_dir / "templates"
        self.locales_dir = self.base_dir / "locales"
        self.cache_ttl = cache_ttl
        
        # טעינת כל הפרומפטים
        self.prompts = self._load_all_prompts()
        
        # מטמון לתבניות מעובדות
        self._template_cache = {}
        self._template_cache_timestamps = {}
        
        logger.info("prompt_manager_initialized")
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """
        טעינת קובץ YAML
        
        Args:
            file_path: נתיב הקובץ
            
        Returns:
            תוכן הקובץ
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"שגיאה בטעינת {file_path}: {str(e)}")
            return {}
    
    def _load_all_prompts(self) -> Dict[str, Any]:
        """
        טעינת כל הפרומפטים
        
        Returns:
            מילון עם כל הפרומפטים
        """
        prompts = {}
        
        # טעינת קבצי תצורה
        for yaml_file in self.config_dir.glob("*.yaml"):
            prompts[yaml_file.stem] = self._load_yaml_file(yaml_file)
        
        # טעינת תבניות
        prompts['templates'] = {}
        for yaml_file in self.templates_dir.glob("*.yaml"):
            prompts['templates'][yaml_file.stem] = self._load_yaml_file(yaml_file)
        
        # טעינת תרגומים
        prompts['locales'] = {}
        for yaml_file in self.locales_dir.glob("*.yaml"):
            prompts['locales'][yaml_file.stem] = self._load_yaml_file(yaml_file)
        
        return prompts
    
    @timed_lru_cache(seconds=3600, maxsize=100)
    def get_prompt(
        self,
        prompt_type: str,
        prompt_name: str,
        language: str = 'he'
    ) -> str:
        """
        קבלת פרומפט לפי סוג ושם
        
        Args:
            prompt_type: סוג הפרומפט
            prompt_name: שם הפרומפט
            language: שפה (ברירת מחדל: עברית)
            
        Returns:
            הפרומפט המבוקש
        """
        # ניסיון לקבל את הפרומפט מהתרגומים
        if language != 'he':
            locale_prompts = self.prompts.get('locales', {}).get(language, {})
            if prompt_type in locale_prompts and prompt_name in locale_prompts[prompt_type]:
                return locale_prompts[prompt_type][prompt_name]
        
        # חיפוש בקבצי התצורה
        if prompt_type in self.prompts:
            return self.prompts[prompt_type].get(prompt_name, '')
        
        # חיפוש בתבניות
        if prompt_type in self.prompts.get('templates', {}):
            return self.prompts['templates'][prompt_type].get(prompt_name, '')
        
        return ''
    
    def get_template(
        self,
        template_type: str,
        template_name: str,
        **kwargs
    ) -> str:
        """
        קבלת תבנית ומילוי הפרמטרים שלה
        
        Args:
            template_type: סוג התבנית
            template_name: שם התבנית
            **kwargs: פרמטרים למילוי בתבנית
            
        Returns:
            התבנית לאחר מילוי הפרמטרים
        """
        # בדיקה אם התבנית נמצאת במטמון
        cache_key = f"{template_type}:{template_name}:{str(kwargs)}"
        
        # בדיקה אם התבנית במטמון ולא פג תוקפה
        current_time = time.time()
        if (cache_key in self._template_cache and 
            current_time - self._template_cache_timestamps.get(cache_key, 0) < self.cache_ttl):
            return self._template_cache[cache_key]
        
        # אם לא במטמון, מקבלים את התבנית ומעבדים אותה
        template = self.get_prompt('templates', template_type, template_name)
        if not template:
            return ''
        
        try:
            filled_template = template.format(**kwargs)
            
            # שמירה במטמון
            self._template_cache[cache_key] = filled_template
            self._template_cache_timestamps[cache_key] = current_time
            
            return filled_template
        except KeyError as e:
            logger.error(f"חסר פרמטר {e} בתבנית {template_type}/{template_name}")
            return template
        except Exception as e:
            logger.error(f"שגיאה במילוי תבנית {template_type}/{template_name}: {str(e)}")
            return template
    
    @timed_lru_cache(seconds=3600, maxsize=100)
    def get_task_prompt(
        self,
        task_type: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        קבלת פרומפט למשימה
        
        Args:
            task_type: סוג המשימה
            params: פרמטרים למשימה
            
        Returns:
            הפרומפט למשימה
        """
        # אם אין פרמטרים, אפשר להשתמש בקאשינג פשוט
        if not params:
            prompt = self.get_prompt('task_prompts', task_type)
            if not prompt:
                prompt = self.get_prompt('base_prompts', 'default')
            return prompt
        
        # אם יש פרמטרים, צריך לעבד את התבנית
        prompt = self.get_prompt('task_prompts', task_type)
        if not prompt:
            prompt = self.get_prompt('base_prompts', 'default')
        
        try:
            return prompt.format(**params)
        except Exception as e:
            logger.error(f"שגיאה במילוי פרומפט משימה: {str(e)}")
            return prompt
    
    @timed_lru_cache(seconds=3600, maxsize=100)
    def get_error_prompt(
        self,
        error_type: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        קבלת פרומפט לשגיאה
        
        Args:
            error_type: סוג השגיאה
            error_details: פרטי השגיאה
            
        Returns:
            הפרומפט לשגיאה
        """
        # אם אין פרטי שגיאה, אפשר להשתמש בקאשינג פשוט
        if not error_details:
            prompt = self.get_prompt('error_prompts', error_type)
            if not prompt:
                prompt = self.get_prompt('error_prompts', 'general')
            return prompt
        
        # אם יש פרטי שגיאה, צריך לעבד את התבנית
        prompt = self.get_prompt('error_prompts', error_type)
        if not prompt:
            prompt = self.get_prompt('error_prompts', 'general')
        
        try:
            return prompt.format(**error_details)
        except Exception as e:
            logger.error(f"שגיאה במילוי פרומפט שגיאה: {str(e)}")
            return prompt
    
    def clear_cache(self) -> ServiceResponse:
        """
        ניקוי כל המטמונים
        
        Returns:
            תוצאת הפעולה
        """
        try:
            # ניקוי מטמון הפרומפטים
            self.get_prompt.cache_clear()
            
            # ניקוי מטמון התבניות
            self._template_cache.clear()
            self._template_cache_timestamps.clear()
            
            # ניקוי מטמון פרומפטי המשימות
            self.get_task_prompt.cache_clear()
            
            # ניקוי מטמון פרומפטי השגיאות
            self.get_error_prompt.cache_clear()
            
            logger.info("prompt_cache_cleared")
            
            return ServiceResponse(
                success=True,
                message="המטמון נוקה בהצלחה"
            )
        except Exception as e:
            logger.error(f"שגיאה בניקוי המטמון: {str(e)}")
            return ServiceResponse(
                success=False,
                message="שגיאה בניקוי המטמון",
                error_details=str(e)
            )
    
    def reload_prompts(self) -> ServiceResponse:
        """
        טעינה מחדש של כל הפרומפטים
        
        Returns:
            תוצאת הפעולה
        """
        try:
            self.prompts = self._load_all_prompts()
            
            # ניקוי כל המטמונים
            self.clear_cache()
            
            return ServiceResponse(
                success=True,
                message="הפרומפטים נטענו מחדש בהצלחה"
            )
        except Exception as e:
            logger.error(f"שגיאה בטעינת הפרומפטים: {str(e)}")
            return ServiceResponse(
                success=False,
                message="שגיאה בטעינת הפרומפטים",
                error_details=str(e)
            )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        קבלת סטטיסטיקות על המטמון
        
        Returns:
            מילון עם סטטיסטיקות המטמון
        """
        try:
            stats = {
                "prompt_cache": self.get_prompt.cache_info()._asdict(),
                "task_prompt_cache": self.get_task_prompt.cache_info()._asdict(),
                "error_prompt_cache": self.get_error_prompt.cache_info()._asdict(),
                "template_cache_size": len(self._template_cache),
                "cache_ttl": self.cache_ttl
            }
            
            return stats
        except Exception as e:
            logger.error(f"שגיאה בקבלת סטטיסטיקות המטמון: {str(e)}")
            return {
                "error": str(e)
            }
            
    @timed_lru_cache(seconds=3600, maxsize=10)
    def get_system_prompt(self) -> str:
        """
        קבלת הפרומפט הראשי של המערכת
        
        Returns:
            פרומפט המערכת
        """
        try:
            # ניסיון לקבל את פרומפט המערכת מקובץ התצורה
            system_prompts = self.get_prompt('base_prompts', 'system')
            
            # בדיקה אם קיבלנו מילון של פרומפטים
            if isinstance(system_prompts, dict) and 'base_bot' in system_prompts:
                # שימוש בפרומפט הבסיסי
                system_prompt = system_prompts['base_bot']
            else:
                # אם לא נמצא, החזרת פרומפט ברירת מחדל
                system_prompt = """אתה עוזר אישי חכם ויעיל שמסייע למשתמשים בעברית.
אתה עונה בצורה מדויקת, ברורה ומועילה לכל שאלה.
אתה מתמקד במתן מידע מדויק ורלוונטי, ומשתדל לספק תשובות מקיפות ומועילות.
אם אינך יודע את התשובה, אתה מודה בכך ולא ממציא מידע.
חשוב מאוד: אתה חייב לענות בעברית בלבד!
"""
            
            # וידוא שהפרומפט מדגיש את הצורך לענות בעברית
            if "בעברית" not in system_prompt:
                system_prompt += "\nחשוב מאוד: אתה חייב לענות בעברית בלבד!"
                
            return system_prompt
        except Exception as e:
            logger.error(f"שגיאה בקבלת פרומפט המערכת: {str(e)}")
            # החזרת פרומפט ברירת מחדל במקרה של שגיאה
            return """אתה עוזר אישי חכם ויעיל שמסייע למשתמשים בעברית.
אתה עונה בצורה מדויקת, ברורה ומועילה לכל שאלה.
חשוב מאוד: אתה חייב לענות בעברית בלבד!"""

            
    def get_error_message(self, error_type: str = "general") -> str:
        """
        קבלת הודעת שגיאה למשתמש
        
        Args:
            error_type: סוג השגיאה
            
        Returns:
            הודעת השגיאה
        """
        try:
            # ניסיון לקבל את הודעת השגיאה מקובץ התצורה
            error_message = self.get_prompt('error_messages', error_type)
            
            # אם לא נמצא, החזרת הודעת שגיאה כללית
            if not error_message:
                error_message = "אירעה שגיאה בעיבוד הבקשה שלך. אנא נסה שוב מאוחר יותר."
                
            return error_message
        except Exception as e:
            logger.error(f"שגיאה בקבלת הודעת שגיאה: {str(e)}")
            return "אירעה שגיאה בעיבוד הבקשה שלך. אנא נסה שוב מאוחר יותר."

# יצירת מופע יחיד של מנהל הפרומפטים
prompt_manager = PromptManager()