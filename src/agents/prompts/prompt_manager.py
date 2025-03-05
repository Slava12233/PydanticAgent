"""
מנהל פרומפטים
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional

class PromptManager:
    """מנהל פרומפטים"""

    def __init__(self):
        """אתחול מנהל הפרומפטים"""
        self.prompts = {}
        self._load_prompts()
        logging.info("prompts_loaded")

    def _load_prompts(self) -> None:
        """טעינת פרומפטים מקבצי YAML"""
        prompts_dir = os.path.dirname(os.path.abspath(__file__))
        yaml_files = [
            f for f in os.listdir(prompts_dir)
            if f.endswith('.yaml')
        ]

        for yaml_file in yaml_files:
            with open(os.path.join(prompts_dir, yaml_file), 'r', encoding='utf-8') as f:
                try:
                    prompts = yaml.safe_load(f)
                    if prompts and isinstance(prompts, dict):
                        self.prompts.update(prompts)
                except yaml.YAMLError as e:
                    logging.error(f"שגיאה בטעינת קובץ {yaml_file}: {str(e)}")

    def get_prompt(self, prompt_type: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """
        קבלת פרומפט לפי סוג
        
        Args:
            prompt_type: סוג הפרומפט
            variables: משתנים להחלפה בפרומפט
            
        Returns:
            הפרומפט המבוקש
            
        Raises:
            KeyError: אם הפרומפט לא נמצא
            ValueError: אם יש שגיאה בהחלפת משתנים
        """
        if prompt_type not in self.prompts:
            raise KeyError(f"פרומפט מסוג {prompt_type} לא נמצא")

        prompt = self.prompts[prompt_type]

        if variables:
            try:
                prompt = prompt.format(**variables)
            except KeyError as e:
                raise KeyError(f"חסר משתנה {e} בפרומפט")
            except Exception as e:
                raise ValueError(f"שגיאה בהחלפת משתנים בפרומפט: {str(e)}")

        return prompt.strip()

    def get_task_prompt(self, task_type: str) -> str:
        """
        קבלת פרומפט למשימה
        
        Args:
            task_type: סוג המשימה
            
        Returns:
            פרומפט למשימה
        """
        prompt_key = f"task_{task_type}"
        return self.get_prompt(prompt_key)

    def get_error_prompt(self, error_type: str) -> str:
        """
        קבלת פרומפט לשגיאה
        
        Args:
            error_type: סוג השגיאה
            
        Returns:
            פרומפט לשגיאה
        """
        prompt_key = f"error_{error_type}"
        return self.get_prompt(prompt_key)

    def get_base_prompt(self, prompt_type: str) -> str:
        """
        קבלת פרומפט בסיסי
        
        Args:
            prompt_type: סוג הפרומפט
            
        Returns:
            פרומפט בסיסי
        """
        prompt_key = f"base_{prompt_type}"
        return self.get_prompt(prompt_key)

# יצירת מופע גלובלי של מנהל הפרומפטים
prompt_manager = PromptManager() 