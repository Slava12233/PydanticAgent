"""
מודול core - מכיל את רכיבי הליבה של המערכת
"""

from .task_identifier import identify_task, get_task_specific_prompt, TaskIdentification
from .model_manager import ModelManager
from .context_retriever import retrieve_context
from .base_agent import BaseAgent, ChatResponse
from .config import *

__all__ = [
    'identify_task',
    'get_task_specific_prompt',
    'TaskIdentification',
    'ModelManager',
    'retrieve_context',
    'BaseAgent',
    'ChatResponse'
] 