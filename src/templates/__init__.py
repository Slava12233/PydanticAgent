"""
חבילת תבניות
"""

from .template_manager import TemplateManager

# יצירת מופע יחיד של מנהל התבניות
template_manager = TemplateManager()

def get_template(template_key: str, language: str = None, **kwargs) -> str:
    """
    קבלת תבנית מעוצבת
    
    Args:
        template_key: מפתח התבנית (למשל "system.welcome")
        language: שפה (אופציונלי)
        **kwargs: פרמטרים להצבה בתבנית
        
    Returns:
        התבנית המעוצבת
    """
    return template_manager.get_template(template_key, language, **kwargs)

def add_translation(language: str, translations: dict) -> None:
    """
    הוספת תרגום חדש
    
    Args:
        language: קוד השפה
        translations: מילון התרגומים
    """
    template_manager.add_translation(language, translations)

def get_available_languages() -> list[str]:
    """
    קבלת רשימת השפות הזמינות
    
    Returns:
        רשימת קודי שפות
    """
    return template_manager.get_available_languages()

def get_available_templates() -> dict[str, list[str]]:
    """
    קבלת רשימת התבניות הזמינות
    
    Returns:
        מילון של קטגוריות ותבניות
    """
    return template_manager.get_available_templates()

__all__ = [
    'TemplateManager',
    'get_template',
    'add_translation',
    'get_available_languages',
    'get_available_templates'
] 