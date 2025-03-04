"""
מנהל תבניות
"""
from typing import Dict, Any, Optional
import yaml
from pathlib import Path
import logfire

class TemplateManager:
    """מחלקה לניהול תבניות"""
    
    def __init__(self, default_language: str = "he"):
        """
        אתחול מנהל התבניות
        
        Args:
            default_language: שפת ברירת המחדל
        """
        self.default_language = default_language
        self.templates_dir = Path(__file__).parent
        self.responses_dir = self.templates_dir / "responses"
        self.locales_dir = self.templates_dir / "locales"
        
        # טעינת תבניות
        self.templates = self._load_templates()
        self.translations = self._load_translations()
    
    def get_template(self, template_key: str, language: Optional[str] = None, **kwargs) -> str:
        """
        קבלת תבנית מעוצבת
        
        Args:
            template_key: מפתח התבנית (למשל "system.welcome")
            language: שפה (אופציונלי)
            **kwargs: פרמטרים להצבה בתבנית
            
        Returns:
            התבנית המעוצבת
        """
        try:
            # בחירת שפה
            lang = language or self.default_language
            
            # קבלת התבנית
            template = self._get_template_by_key(template_key, lang)
            if not template:
                logfire.warning(f"template_not_found", key=template_key, language=lang)
                return f"Template not found: {template_key}"
            
            # עיצוב התבנית
            return template.format(**kwargs).strip()
            
        except KeyError as e:
            logfire.error("template_key_error", key=template_key, error=str(e))
            return f"Missing template parameter: {str(e)}"
        except Exception as e:
            logfire.error("template_error", key=template_key, error=str(e))
            return f"Error formatting template: {str(e)}"
    
    def _load_templates(self) -> Dict[str, Any]:
        """
        טעינת תבניות בסיסיות
        
        Returns:
            מילון של תבניות
        """
        try:
            templates = {}
            
            # טעינת כל קבצי ה-YAML בתיקיית responses
            for yaml_file in self.responses_dir.glob("*.yaml"):
                with open(yaml_file, "r", encoding="utf-8") as f:
                    templates[yaml_file.stem] = yaml.safe_load(f)
            
            return templates
            
        except Exception as e:
            logfire.error("load_templates_error", error=str(e))
            return {}
    
    def _load_translations(self) -> Dict[str, Dict[str, Any]]:
        """
        טעינת תרגומים
        
        Returns:
            מילון של תרגומים לפי שפה
        """
        try:
            translations = {}
            
            # טעינת כל קבצי ה-YAML בתיקיית locales
            for yaml_file in self.locales_dir.glob("*.yaml"):
                language = yaml_file.stem
                with open(yaml_file, "r", encoding="utf-8") as f:
                    translations[language] = yaml.safe_load(f)
            
            return translations
            
        except Exception as e:
            logfire.error("load_translations_error", error=str(e))
            return {}
    
    def _get_template_by_key(self, template_key: str, language: str) -> Optional[str]:
        """
        קבלת תבנית לפי מפתח ושפה
        
        Args:
            template_key: מפתח התבנית
            language: שפה
            
        Returns:
            התבנית או None אם לא נמצאה
        """
        try:
            # פיצול המפתח לחלקים (למשל "system.welcome" -> ["system", "welcome"])
            parts = template_key.split(".")
            
            # ניסיון לקבל את התבנית מהתרגומים
            if language in self.translations:
                template = self.translations[language]
                for part in parts:
                    template = template[part]
                return template
            
            # אם אין תרגום, שימוש בתבנית הבסיסית
            template = self.templates["base_responses"]
            for part in parts:
                template = template[part]
            return template
            
        except (KeyError, TypeError):
            return None
    
    def add_translation(self, language: str, translations: Dict[str, Any]) -> None:
        """
        הוספת תרגום חדש
        
        Args:
            language: קוד השפה
            translations: מילון התרגומים
        """
        try:
            # שמירת התרגומים בזיכרון
            self.translations[language] = translations
            
            # שמירת התרגומים לקובץ
            translation_file = self.locales_dir / f"{language}.yaml"
            with open(translation_file, "w", encoding="utf-8") as f:
                yaml.dump(translations, f, allow_unicode=True, sort_keys=False)
            
            logfire.info("translation_added", language=language)
            
        except Exception as e:
            logfire.error("add_translation_error", language=language, error=str(e))
    
    def get_available_languages(self) -> list[str]:
        """
        קבלת רשימת השפות הזמינות
        
        Returns:
            רשימת קודי שפות
        """
        return list(self.translations.keys())
    
    def get_available_templates(self) -> Dict[str, list[str]]:
        """
        קבלת רשימת התבניות הזמינות
        
        Returns:
            מילון של קטגוריות ותבניות
        """
        templates = {}
        
        # איסוף כל התבניות מהתבניות הבסיסיות
        base_templates = self.templates.get("base_responses", {})
        for category, items in base_templates.items():
            if isinstance(items, dict):
                templates[category] = list(items.keys())
        
        return templates 