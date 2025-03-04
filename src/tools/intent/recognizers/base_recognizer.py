"""
מזהה כוונות בסיסי
"""
from typing import Dict, List, Tuple, Optional
import re
import logfire

from ..config.intent_config import (
    GENERAL_SETTINGS,
    INTENT_PATTERNS,
    get_all_keywords
)

class BaseIntentRecognizer:
    """מחלקה בסיסית לזיהוי כוונות"""
    
    def __init__(self):
        """אתחול המזהה"""
        self.keywords = get_all_keywords()
        self.patterns = INTENT_PATTERNS
        self.settings = GENERAL_SETTINGS
    
    def identify_intent(self, text: str) -> Tuple[str, str, float]:
        """
        זיהוי כוונה מתוך טקסט
        
        Args:
            text: הטקסט לזיהוי
            
        Returns:
            סוג הכוונה, הפעולה הספציפית, וציון הביטחון
        """
        text = text.lower().strip()
        
        # ניסיון לזהות לפי תבניות
        pattern_match = self._match_patterns(text)
        if pattern_match:
            return pattern_match
        
        # ניסיון לזהות לפי מילות מפתח
        keyword_match = self._match_keywords(text)
        if keyword_match:
            return keyword_match
        
        # אם לא נמצאה התאמה
        return "general", "unknown", 0.0
    
    def _match_patterns(self, text: str) -> Optional[Tuple[str, str, float]]:
        """
        זיהוי כוונה לפי תבניות
        
        Args:
            text: הטקסט לזיהוי
            
        Returns:
            סוג הכוונה, הפעולה הספציפית, וציון הביטחון או None אם לא נמצאה התאמה
        """
        for intent_type, actions in self.patterns.items():
            for action, pattern in actions.items():
                if re.search(pattern, text):
                    return intent_type, action, 1.0
        return None
    
    def _match_keywords(self, text: str) -> Optional[Tuple[str, str, float]]:
        """
        זיהוי כוונה לפי מילות מפתח
        
        Args:
            text: הטקסט לזיהוי
            
        Returns:
            סוג הכוונה, הפעולה הספציפית, וציון הביטחון או None אם לא נמצאה התאמה
        """
        best_match = (None, None, 0.0)  # (intent_type, action, score)
        
        for intent_type, actions in self.keywords.items():
            for action, keywords in actions.items():
                score = self._calculate_keyword_score(text, keywords)
                if score > best_match[2]:
                    best_match = (intent_type, action, score)
        
        if best_match[2] >= self.settings["min_confidence_score"]:
            return best_match
        return None
    
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """
        חישוב ציון התאמה לפי מילות מפתח
        
        Args:
            text: הטקסט לבדיקה
            keywords: רשימת מילות מפתח
            
        Returns:
            ציון בין 0 ל-1
        """
        words = set(text.split())
        matches = sum(1 for keyword in keywords if keyword in words)
        return matches / len(keywords) if keywords else 0.0
    
    def learn_from_feedback(self, text: str, correct_intent: str, correct_action: str) -> None:
        """
        למידה מפידבק משתמש
        
        Args:
            text: הטקסט המקורי
            correct_intent: הכוונה הנכונה
            correct_action: הפעולה הנכונה
        """
        try:
            # חילוץ מילות מפתח חדשות מהטקסט
            words = set(text.lower().split())
            current_keywords = set(self.keywords.get(correct_intent, {}).get(correct_action, []))
            
            # הוספת מילים חדשות שעומדות בקריטריונים
            new_keywords = {
                word for word in words
                if (
                    self.settings["min_keyword_length"] <= len(word) <= self.settings["max_keyword_length"]
                    and word not in current_keywords
                )
            }
            
            if new_keywords:
                # עדכון מילות המפתח
                if correct_intent not in self.keywords:
                    self.keywords[correct_intent] = {}
                if correct_action not in self.keywords[correct_intent]:
                    self.keywords[correct_intent][correct_action] = []
                
                self.keywords[correct_intent][correct_action].extend(list(new_keywords))
                
                # שמירת השינויים
                from ..config.intent_config import save_custom_keywords
                save_custom_keywords(self.keywords)
                
                logfire.info(
                    "learned_new_keywords",
                    intent=correct_intent,
                    action=correct_action,
                    new_keywords=list(new_keywords)
                )
                
        except Exception as e:
            logfire.error("learning_error", error=str(e)) 