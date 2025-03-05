"""
בדיקות יחידה למערכת הפרומפטים
"""
import pytest
import yaml
from pathlib import Path
from src.agents.prompts.prompt_manager import PromptManager
from src.agents.prompts.task_prompts import get_task_prompt
from src.agents.prompts.error_prompts import get_error_prompt
from src.agents.prompts.base_prompts import get_base_prompt

def test_load_yaml_files():
    """בדיקת טעינת קבצי YAML"""
    yaml_files = [
        "conversations.yaml",
        "commands.yaml",
        "responses.yaml",
        "base_prompts.yaml"
    ]
    
    prompts_dir = Path("src/agents/prompts")
    
    for file_name in yaml_files:
        file_path = prompts_dir / file_name
        assert file_path.exists(), f"קובץ {file_name} לא נמצא"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            assert data is not None
            assert isinstance(data, dict)
            assert len(data) > 0

def test_prompt_manager():
    """בדיקת מנהל הפרומפטים"""
    manager = PromptManager()
    
    # בדיקת טעינת פרומפטים
    assert manager.prompts is not None
    assert len(manager.prompts) > 0
    
    # בדיקת קבלת פרומפט
    prompt = manager.get_prompt("general_conversation")
    assert prompt is not None
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    
    # בדיקת החלפת משתנים בפרומפט
    prompt_with_vars = manager.get_prompt(
        "user_greeting",
        variables={
            "user_name": "משה",
            "time_of_day": "בוקר"
        }
    )
    assert "משה" in prompt_with_vars
    assert "בוקר" in prompt_with_vars

def test_task_prompts():
    """בדיקת פרומפטים למשימות"""
    test_cases = [
        ("weather", "מזג אוויר"),
        ("add_product", "מוצר"),
        ("help", "עזרה"),
        ("general", "שיחה")
    ]
    
    for task_type, expected_content in test_cases:
        prompt = get_task_prompt(task_type)
        assert prompt is not None
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert expected_content in prompt.lower()

def test_error_prompts():
    """בדיקת פרומפטים לשגיאות"""
    test_cases = [
        ("general_error", "שגיאה"),
        ("not_found", "לא נמצא"),
        ("permission_denied", "הרשאה"),
        ("timeout", "זמן"),
        ("validation_error", "תקין")
    ]
    
    for error_type, expected_content in test_cases:
        prompt = get_error_prompt(error_type)
        assert prompt is not None
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert expected_content in prompt.lower()

def test_base_prompts():
    """בדיקת פרומפטים בסיסיים"""
    test_cases = [
        ("system_introduction", "עוזר"),
        ("user_greeting", "שלום"),
        ("help_message", "עזרה"),
        ("farewell", "להתראות")
    ]
    
    for prompt_type, expected_content in test_cases:
        prompt = get_base_prompt(prompt_type)
        assert prompt is not None
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert expected_content in prompt.lower()

def test_prompt_variables():
    """בדיקת החלפת משתנים בפרומפטים"""
    manager = PromptManager()
    
    test_cases = [
        (
            "user_greeting",
            {"user_name": "משה", "time_of_day": "בוקר"},
            ["משה", "בוקר"]
        ),
        (
            "task_completion",
            {"task_name": "הוספת מוצר", "status": "הושלם"},
            ["הוספת מוצר", "הושלם"]
        ),
        (
            "error_message",
            {"error_type": "שגיאת רשת", "details": "אין חיבור"},
            ["שגיאת רשת", "אין חיבור"]
        )
    ]
    
    for prompt_type, variables, expected_contents in test_cases:
        prompt = manager.get_prompt(prompt_type, variables=variables)
        assert prompt is not None
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        for content in expected_contents:
            assert content in prompt

def test_prompt_validation():
    """בדיקת תקינות פרומפטים"""
    manager = PromptManager()
    
    # בדיקת פרומפט לא קיים
    with pytest.raises(KeyError):
        manager.get_prompt("non_existent_prompt")
    
    # בדיקת משתנים חסרים
    with pytest.raises(KeyError):
        manager.get_prompt(
            "user_greeting",
            variables={"user_name": "משה"}  # חסר time_of_day
        )
    
    # בדיקת משתנים לא תקינים
    with pytest.raises(TypeError):
        manager.get_prompt(
            "user_greeting",
            variables={"user_name": None, "time_of_day": 123}
        )

def test_prompt_formatting():
    """בדיקת פורמט פרומפטים"""
    manager = PromptManager()
    
    test_cases = [
        # פרומפט רגיל
        ("general_conversation", None, 1000),
        
        # פרומפט עם משתנים
        (
            "user_greeting",
            {"user_name": "משה", "time_of_day": "בוקר"},
            1000
        ),
        
        # פרומפט ארוך
        ("system_introduction", None, 2000)
    ]
    
    for prompt_type, variables, max_length in test_cases:
        prompt = manager.get_prompt(prompt_type, variables=variables)
        assert prompt is not None
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert len(prompt) <= max_length
        assert prompt.strip() == prompt  # אין רווחים מיותרים
        assert prompt.count("{") == prompt.count("}")  # כל המשתנים הוחלפו 