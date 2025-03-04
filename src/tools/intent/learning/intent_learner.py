"""
מנהל למידת כוונות
"""
from typing import Dict, List, Set, Tuple, Any
import json
from datetime import datetime, timedelta
import logfire

from ..config.intent_config import (
    GENERAL_SETTINGS,
    get_all_keywords,
    save_custom_keywords
)

class IntentLearner:
    """מחלקה ללמידת כוונות"""
    
    def __init__(self):
        """אתחול מנהל הלמידה"""
        self.settings = GENERAL_SETTINGS
        self.keywords = get_all_keywords()
        self.learning_history = []
    
    def learn_from_examples(self, examples: List[Tuple[str, str, str]]) -> None:
        """
        למידה מדוגמאות מתויגות
        
        Args:
            examples: רשימה של טאפלים (טקסט, כוונה, פעולה)
        """
        try:
            for text, intent, action in examples:
                # חילוץ מילות מפתח פוטנציאליות
                words = self._extract_potential_keywords(text)
                
                # הוספת מילות מפתח חדשות
                self._add_new_keywords(words, intent, action)
            
            # שמירת השינויים
            save_custom_keywords(self.keywords)
            
            logfire.info(
                "learned_from_examples",
                examples_count=len(examples)
            )
            
        except Exception as e:
            logfire.error("learning_from_examples_error", error=str(e))
    
    def learn_from_feedback(self, text: str, predicted: Tuple[str, str], correct: Tuple[str, str]) -> None:
        """
        למידה מפידבק משתמש
        
        Args:
            text: הטקסט המקורי
            predicted: הכוונה והפעולה שזוהו (כוונה, פעולה)
            correct: הכוונה והפעולה הנכונות (כוונה, פעולה)
        """
        try:
            # תיעוד הפידבק
            self.learning_history.append({
                "text": text,
                "predicted": predicted,
                "correct": correct,
                "timestamp": datetime.now().isoformat()
            })
            
            # חילוץ מילות מפתח פוטנציאליות
            words = self._extract_potential_keywords(text)
            
            # הוספת מילות מפתח חדשות לכוונה הנכונה
            self._add_new_keywords(words, correct[0], correct[1])
            
            # הסרת מילות מפתח שגויות
            self._remove_wrong_keywords(words, predicted[0], predicted[1])
            
            # שמירת השינויים
            save_custom_keywords(self.keywords)
            
            logfire.info(
                "learned_from_feedback",
                text=text[:100],
                predicted=predicted,
                correct=correct
            )
            
        except Exception as e:
            logfire.error("learning_from_feedback_error", error=str(e))
    
    def analyze_learning_history(self, days: int = 7) -> Dict[str, Any]:
        """
        ניתוח היסטוריית הלמידה
        
        Args:
            days: מספר הימים לניתוח
            
        Returns:
            סטטיסטיקות על הלמידה
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_history = [
                entry for entry in self.learning_history
                if datetime.fromisoformat(entry["timestamp"]) >= cutoff_date
            ]
            
            total_feedback = len(recent_history)
            correct_predictions = sum(
                1 for entry in recent_history
                if entry["predicted"] == entry["correct"]
            )
            
            return {
                "total_feedback": total_feedback,
                "correct_predictions": correct_predictions,
                "accuracy": correct_predictions / total_feedback if total_feedback > 0 else 0,
                "days_analyzed": days
            }
            
        except Exception as e:
            logfire.error("analyze_history_error", error=str(e))
            return {}
    
    def _extract_potential_keywords(self, text: str) -> Set[str]:
        """
        חילוץ מילות מפתח פוטנציאליות מטקסט
        
        Args:
            text: הטקסט לניתוח
            
        Returns:
            סט של מילות מפתח פוטנציאליות
        """
        words = set(text.lower().split())
        return {
            word for word in words
            if self.settings["min_keyword_length"] <= len(word) <= self.settings["max_keyword_length"]
        }
    
    def _add_new_keywords(self, words: Set[str], intent: str, action: str) -> None:
        """
        הוספת מילות מפתח חדשות
        
        Args:
            words: סט של מילים
            intent: סוג הכוונה
            action: סוג הפעולה
        """
        if intent not in self.keywords:
            self.keywords[intent] = {}
        if action not in self.keywords[intent]:
            self.keywords[intent][action] = []
        
        current_keywords = set(self.keywords[intent][action])
        new_keywords = words - current_keywords
        
        if new_keywords:
            # הגבלת מספר מילות המפתח
            available_slots = self.settings["max_keywords_per_intent"] - len(current_keywords)
            if available_slots > 0:
                self.keywords[intent][action].extend(list(new_keywords)[:available_slots])
    
    def _remove_wrong_keywords(self, words: Set[str], wrong_intent: str, wrong_action: str) -> None:
        """
        הסרת מילות מפתח שגויות
        
        Args:
            words: סט של מילים
            wrong_intent: סוג הכוונה השגוי
            wrong_action: סוג הפעולה השגוי
        """
        if wrong_intent in self.keywords and wrong_action in self.keywords[wrong_intent]:
            current_keywords = set(self.keywords[wrong_intent][wrong_action])
            wrong_keywords = words & current_keywords
            
            if wrong_keywords:
                self.keywords[wrong_intent][wrong_action] = [
                    kw for kw in self.keywords[wrong_intent][wrong_action]
                    if kw not in wrong_keywords
                ] 