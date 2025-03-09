"""
חבילת זיהוי משימות
"""
from .models import TaskIdentification, IntentRecognitionResult, TaskContext
from .identifier import identify_task, get_task_specific_prompt
from .prompts import get_task_prompt, get_intent_prompt

__all__ = [
    'TaskIdentification',
    'IntentRecognitionResult',
    'TaskContext',
    'identify_task',
    'get_task_specific_prompt',
    'get_task_prompt',
    'get_intent_prompt'
] 