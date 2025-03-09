"""
מודול הפרומפטים של המערכת
"""
from .prompt_manager import prompt_manager

# ייצוא פונקציות נפוצות
get_prompt = prompt_manager.get_prompt
get_template = prompt_manager.get_template
get_task_prompt = prompt_manager.get_task_prompt
get_error_prompt = prompt_manager.get_error_prompt
reload_prompts = prompt_manager.reload_prompts

__all__ = [
    'prompt_manager',
    'get_prompt',
    'get_template',
    'get_task_prompt',
    'get_error_prompt',
    'reload_prompts'
] 