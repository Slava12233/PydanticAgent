"""
מודול לחיפוש והחזרת הקשר רלוונטי
"""

import logfire
from typing import Optional
from src.services.ai import search_documents

async def retrieve_context(query: str) -> str:
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