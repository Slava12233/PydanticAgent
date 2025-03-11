"""
מודול RAG Search - מכיל את פונקציות החיפוש במערכת ה-RAG
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

from langchain.docstore.document import Document
from langchain_community.vectorstores.pgvector import PGVector

from src.utils.logger import setup_logger
from .rag_core import RAGCore

logger = setup_logger(__name__)

class RAGSearch(RAGCore):
    """מחלקה לביצוע חיפושים במערכת ה-RAG"""
    
    async def semantic_search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_relevance_score: float = 0.7
    ) -> List[Tuple[Document, float]]:
        """חיפוש סמנטי במאגר המסמכים
        
        Args:
            query: שאילתת החיפוש
            k: מספר התוצאות המקסימלי
            filter_metadata: פילטר לפי מטא-דאטה
            min_relevance_score: ציון רלוונטיות מינימלי
            
        Returns:
            רשימה של זוגות (מסמך, ציון) מסודרת לפי רלוונטיות
        """
        try:
            # ביצוע החיפוש
            results = self.vectorstore.similarity_search_with_relevance_scores(
                query,
                k=k,
                filter=filter_metadata
            )
            
            # פילטור לפי ציון מינימלי
            filtered_results = [
                (doc, score) for doc, score in results
                if score >= min_relevance_score
            ]
            
            logger.info(f"Found {len(filtered_results)} relevant results for query: {query}")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Failed to perform semantic search: {str(e)}")
            raise
            
    async def keyword_search(
        self,
        keywords: List[str],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        match_all: bool = False
    ) -> List[Document]:
        """חיפוש לפי מילות מפתח
        
        Args:
            keywords: רשימת מילות מפתח
            k: מספר התוצאות המקסימלי
            filter_metadata: פילטר לפי מטא-דאטה
            match_all: האם נדרשת התאמה לכל מילות המפתח
            
        Returns:
            רשימת המסמכים הרלוונטיים
        """
        try:
            # בניית שאילתת החיפוש
            query = " AND " if match_all else " OR "
            query = query.join(keywords)
            
            # ביצוע החיפוש
            results = self.vectorstore.similarity_search(
                query,
                k=k,
                filter=filter_metadata
            )
            
            logger.info(f"Found {len(results)} results for keywords: {keywords}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform keyword search: {str(e)}")
            raise
            
    async def filter_search(
        self,
        filter_metadata: Dict[str, Any],
        k: Optional[int] = None
    ) -> List[Document]:
        """חיפוש לפי פילטרים של מטא-דאטה
        
        Args:
            filter_metadata: פילטר המטא-דאטה
            k: מספר התוצאות המקסימלי (אופציונלי)
            
        Returns:
            רשימת המסמכים המתאימים
        """
        try:
            results = self.vectorstore.get(
                filter=filter_metadata,
                limit=k
            )
            
            logger.info(f"Found {len(results)} results for filter: {filter_metadata}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform filter search: {str(e)}")
            raise
            
    async def hybrid_search(
        self,
        query: str,
        filter_metadata: Optional[Dict[str, Any]] = None,
        k: int = 5,
        min_relevance_score: float = 0.7
    ) -> List[Tuple[Document, float]]:
        """חיפוש היברידי המשלב חיפוש סמנטי עם פילטרים
        
        Args:
            query: שאילתת החיפוש
            filter_metadata: פילטר לפי מטא-דאטה
            k: מספר התוצאות המקסימלי
            min_relevance_score: ציון רלוונטיות מינימלי
            
        Returns:
            רשימה של זוגות (מסמך, ציון) מסודרת לפי רלוונטיות
        """
        try:
            # ביצוע חיפוש סמנטי עם פילטרים
            results = await self.semantic_search(
                query,
                k=k,
                filter_metadata=filter_metadata,
                min_relevance_score=min_relevance_score
            )
            
            logger.info(f"Performed hybrid search with query: {query} and filters: {filter_metadata}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform hybrid search: {str(e)}")
            raise 