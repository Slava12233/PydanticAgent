"""
מודול לניהול הקשר שיחה
"""
from typing import List, Dict, Any, Optional
import logfire

from src.services.rag_service import search_documents
from src.tools.managers import (
    ConversationContext,
    understand_context,
    resolve_pronouns,
    extract_context_from_history
)

class ContextManager:
    """מחלקה לניהול הקשר שיחה"""
    
    def __init__(self):
        """אתחול מנהל ההקשר"""
        self.context = ConversationContext()
    
    async def retrieve_context(self, query: str) -> str:
        """
        חיפוש מידע רלוונטי במאגר הידע לפי שאילתה
        
        Args:
            query: שאילתת החיפוש
            
        Returns:
            מחרוזת עם המידע הרלוונטי או הודעה שלא נמצא מידע
        """
        try:
            # בדיקה אם השאילתה קצרה מדי
            if len(query.strip()) <= 3:
                logfire.info('query_too_short', query=query)
                return "לא נמצא מידע רלוונטי. השאילתה קצרה מדי."
            
            logfire.info('searching_knowledge_base', query=query[:100])
            
            # חיפוש מסמכים רלוונטיים
            try:
                chunks = await search_documents(query, limit=5, min_similarity=0.1)
                
                if not chunks:
                    logfire.info('no_relevant_chunks_found', query=query[:100])
                    return "לא נמצא מידע רלוונטי במאגר הידע."
                
                # בניית הקשר מהקטעים שנמצאו
                context_parts = []
                for chunk in chunks:
                    title = chunk.get('title', 'ללא כותרת')
                    source = chunk.get('source', 'לא ידוע')
                    similarity = chunk.get('similarity_percentage', 0)
                    content = chunk.get('content', '')
                    
                    chunk_text = f"### {title}\n"
                    chunk_text += f"מקור: {source}\n"
                    chunk_text += f"רלוונטיות: {similarity:.2f}%\n\n"
                    chunk_text += f"{content}"
                    
                    context_parts.append(chunk_text)
                
                context = "\n\n".join(context_parts)
                
                logfire.info('rag_context_found', chunks_count=len(chunks))
                return f"מידע רלוונטי שנמצא:\n\n{context}"
            except Exception as inner_e:
                logfire.error('search_documents_error', error=str(inner_e))
                return "לא ניתן לחפש במאגר הידע כרגע. אנא נסה שוב מאוחר יותר."
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logfire.error('retrieve_context_error', error=str(e), traceback=error_trace)
            return "לא ניתן לחפש במאגר הידע כרגע. אנא נסה שוב מאוחר יותר."
    
    async def get_relevant_documents(self, query: str) -> str:
        """
        חיפוש מסמכים רלוונטיים לשאילתה
        
        Args:
            query: שאילתת החיפוש
            
        Returns:
            מחרוזת עם המסמכים הרלוונטיים
        """
        try:
            # חיפוש מסמכים רלוונטיים
            chunks = await search_documents(query, limit=3, min_similarity=0.2)
            
            if not chunks:
                return None
            
            # בניית תשובה מהמסמכים שנמצאו
            documents = []
            for chunk in chunks:
                title = chunk.get('title', 'ללא כותרת')
                content = chunk.get('content', '')
                similarity = chunk.get('similarity_percentage', 0)
                
                if similarity < 20:  # סינון תוצאות לא רלוונטיות
                    continue
                    
                documents.append(f"מסמך: {title}\n{content}\n")
            
            if not documents:
                return None
                
            return "\n---\n".join(documents)
            
        except Exception as e:
            logfire.error('get_relevant_documents_error', error=str(e))
            return None
    
    def update_context(self, user_message: str, bot_response: str):
        """
        עדכון הקשר השיחה
        
        Args:
            user_message: הודעת המשתמש
            bot_response: תשובת הבוט
        """
        self.context.add_message("user", user_message)
        self.context.add_message("bot", bot_response)
    
    def get_conversation_history(self, max_messages: int = 5) -> str:
        """
        קבלת היסטוריית השיחה
        
        Args:
            max_messages: מספר ההודעות המקסימלי להחזרה
            
        Returns:
            מחרוזת עם היסטוריית השיחה
        """
        history = []
        messages = self.context.get_last_messages(max_messages)
        
        for msg in messages:
            role = "משתמש" if msg.role == "user" else "בוט"
            history.append(f"{role}: {msg.content}")
        
        return "\n".join(history) if history else "" 