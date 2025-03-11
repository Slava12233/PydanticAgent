"""
פרומפטים לזיהוי משימות
"""
from typing import Dict, Any
import yaml
from pathlib import Path

# טעינת קובץ התצורה של הפרומפטים
PROMPTS_FILE = Path(__file__).parent / "config" / "prompts.yaml"

def load_prompts() -> Dict[str, Any]:
    """טעינת הפרומפטים מקובץ התצורה"""
    if not PROMPTS_FILE.exists():
        return {}
    
    with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# טעינת הפרומפטים בזמן טעינת המודול
TASK_PROMPTS = load_prompts()

def get_task_prompt(task_type: str, params: Dict[str, Any] = None) -> str:
    """
    קבלת פרומפט מותאם למשימה
    
    Args:
        task_type: סוג המשימה
        params: פרמטרים נוספים למשימה
        
    Returns:
        הפרומפט המותאם
    """
    params = params or {}
    
    # קבלת תבנית הפרומפט
    template = TASK_PROMPTS.get(task_type, TASK_PROMPTS.get('general', ''))
    
    # החלפת פרמטרים בתבנית
    return template.format(**params)

def get_intent_prompt(intent_type: str) -> str:
    """
    קבלת פרומפט לזיהוי כוונה ספציפית
    
    Args:
        intent_type: סוג הכוונה
        
    Returns:
        הפרומפט לזיהוי
    """
    return TASK_PROMPTS.get(f"intent_{intent_type}", "") 