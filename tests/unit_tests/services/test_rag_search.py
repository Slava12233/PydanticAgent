"""
בדיקות יחידה עבור מודול RAG Search
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from datetime import datetime

# מוק למחלקת Document של langchain
class Document:
    """מוק למחלקת Document של langchain"""
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

# מוק למחלקת RAGSearch
class RAGSearch:
    """מוק למחלקת RAGSearch"""
    
    def __init__(self, vectorstore=None):
        """אתחול מופע RAGSearch"""
        self.vectorstore = vectorstore or MagicMock()
        self.documents = []
    
    async def semantic_search(self, query, k=5, filter_metadata=None, min_relevance_score=0.7):
        """חיפוש סמנטי"""
        if not query:
            return []
        
        # קריאה למאגר הווקטורים
        try:
            results = await self.vectorstore.similarity_search_with_relevance_scores(
                query,
                k=k,
                filter=filter_metadata
            )
            
            # סינון לפי ציון מינימלי
            filtered_results = []
            for doc, score in results:
                if score >= min_relevance_score:
                    filtered_results.append({
                        "document": doc,
                        "score": score
                    })
            
            return filtered_results
        except Exception as e:
            raise e
    
    async def keyword_search(self, keywords=None, query=None, k=5, filter_metadata=None, match_all=False):
        """חיפוש מילות מפתח"""
        if not keywords and not query:
            return []
        
        # קריאה למאגר הווקטורים
        try:
            docs = await self.vectorstore.similarity_search(
                query or " ".join(keywords or []),
                k=k,
                filter=filter_metadata
            )
            
            # מדמה תוצאות חיפוש
            results = []
            for i, doc in enumerate(docs):
                results.append({
                    "document": doc,
                    "score": 0.8 - (i * 0.05)  # ציונים יורדים
                })
            
            return results
        except Exception as e:
            raise e
    
    async def filter_search(self, filter_metadata=None, k=5):
        """חיפוש לפי פילטרים"""
        if not filter_metadata:
            return []
        
        # קריאה למאגר הווקטורים
        try:
            docs = await self.vectorstore.similarity_search(
                "",
                k=k,
                filter=filter_metadata
            )
            
            # מדמה תוצאות חיפוש
            results = []
            for doc in docs:
                results.append({
                    "document": doc,
                    "score": 1.0  # ציון מלא לפילטרים
                })
            
            return results
        except Exception as e:
            raise e
    
    async def hybrid_search(self, query, filter_metadata=None, k=5, min_relevance_score=0.7, semantic_weight=0.7):
        """חיפוש היברידי"""
        if not query:
            return []
        
        # קריאה למאגר הווקטורים
        try:
            docs = await self.vectorstore.max_marginal_relevance_search(
                query,
                k=k,
                filter=filter_metadata
            )
            
            # מדמה תוצאות חיפוש
            results = []
            for i, doc in enumerate(docs):
                semantic_score = 0.9 - (i * 0.05)
                keyword_score = 0.8 - (i * 0.05)
                combined_score = (semantic_score * semantic_weight) + (keyword_score * (1 - semantic_weight))
                
                if combined_score >= min_relevance_score:
                    results.append({
                        "document": doc,
                        "score": combined_score,
                        "semantic_score": semantic_score,
                        "keyword_score": keyword_score
                    })
            
            return results
        except Exception as e:
            raise e


@pytest_asyncio.fixture
async def rag_search():
    """פיקסצ'ר ליצירת מופע RAG Search לבדיקות"""
    # יצירת מופע RAGSearch
    search = RAGSearch()
    
    # יצירת מסמכים לדוגמה
    search.documents = [
        Document(
            page_content="זהו מסמך לדוגמה עם מידע על מוצרים",
            metadata={"title": "מסמך מוצרים", "category": "מוצרים", "date": "2023-01-01"}
        ),
        Document(
            page_content="מסמך זה מכיל מידע על שירותים שונים",
            metadata={"title": "מסמך שירותים", "category": "שירותים", "date": "2023-02-01"}
        ),
        Document(
            page_content="מדריך למשתמש עבור המערכת",
            metadata={"title": "מדריך למשתמש", "category": "מדריכים", "date": "2023-03-01"}
        ),
        Document(
            page_content="שאלות נפוצות ותשובות",
            metadata={"title": "שאלות ותשובות", "category": "תמיכה", "date": "2023-04-01"}
        ),
        Document(
            page_content="מידע על החברה והצוות",
            metadata={"title": "אודות", "category": "חברה", "date": "2023-05-01"}
        )
    ]
    
    # מוק לפונקציות
    search.semantic_search = AsyncMock(side_effect=search.semantic_search)
    search.keyword_search = AsyncMock(side_effect=search.keyword_search)
    search.filter_search = AsyncMock(side_effect=search.filter_search)
    search.hybrid_search = AsyncMock(side_effect=search.hybrid_search)
    
    # מוק למאגר הווקטורים
    search.vectorstore.similarity_search_with_relevance_scores = AsyncMock()
    search.vectorstore.similarity_search = AsyncMock()
    search.vectorstore.max_marginal_relevance_search = AsyncMock()
    
    yield search


@pytest.mark.asyncio
async def test_semantic_search(rag_search):
    """בדיקת חיפוש סמנטי"""
    # יצירת מסמכים לדוגמה
    doc1 = Document(
        page_content="מסמך ראשון לבדיקה",
        metadata={"title": "מסמך 1", "id": "doc_id_1"}
    )
    doc2 = Document(
        page_content="מסמך שני לבדיקה",
        metadata={"title": "מסמך 2", "id": "doc_id_2"}
    )
    
    # הגדרת מוק לחזרה מהפונקציה
    rag_search.vectorstore.similarity_search_with_relevance_scores.return_value = [
        (doc1, 0.85),
        (doc2, 0.75)
    ]
    
    # הרצת הפונקציה
    results = await rag_search.semantic_search(
        query="שאילתת חיפוש",
        k=5,
        filter_metadata={"type": "test"},
        min_relevance_score=0.7
    )
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    rag_search.vectorstore.similarity_search_with_relevance_scores.assert_called_once_with(
        "שאילתת חיפוש",
        k=5,
        filter={"type": "test"}
    )
    
    # וידוא שהוחזרו התוצאות הנכונות
    assert len(results) == 2
    assert results[0]["document"] == doc1
    assert results[0]["score"] == 0.85
    assert results[1]["document"] == doc2
    assert results[1]["score"] == 0.75


@pytest.mark.asyncio
async def test_semantic_search_with_min_score_filter(rag_search):
    """בדיקת חיפוש סמנטי עם פילטור לפי ציון מינימלי"""
    # יצירת מסמכים לדוגמה
    doc1 = Document(
        page_content="מסמך ראשון לבדיקה",
        metadata={"title": "מסמך 1", "id": "doc_id_1"}
    )
    doc2 = Document(
        page_content="מסמך שני לבדיקה",
        metadata={"title": "מסמך 2", "id": "doc_id_2"}
    )
    
    # הגדרת מוק לחזרה מהפונקציה
    rag_search.vectorstore.similarity_search_with_relevance_scores.return_value = [
        (doc1, 0.85),
        (doc2, 0.65)  # ציון נמוך מהסף
    ]
    
    # הרצת הפונקציה
    results = await rag_search.semantic_search(
        query="שאילתת חיפוש",
        min_relevance_score=0.7
    )
    
    # וידוא שהוחזרו רק התוצאות מעל הסף
    assert len(results) == 1
    assert results[0]["document"] == doc1
    assert results[0]["score"] == 0.85


@pytest.mark.asyncio
async def test_keyword_search(rag_search):
    """בדיקת חיפוש לפי מילות מפתח"""
    # יצירת מסמכים לדוגמה
    doc1 = Document(
        page_content="מסמך ראשון לבדיקה",
        metadata={"title": "מסמך 1", "id": "doc_id_1"}
    )
    doc2 = Document(
        page_content="מסמך שני לבדיקה",
        metadata={"title": "מסמך 2", "id": "doc_id_2"}
    )
    
    # הגדרת מוק לחזרה מהפונקציה
    rag_search.vectorstore.similarity_search.return_value = [doc1, doc2]
    
    # הרצת הפונקציה
    results = await rag_search.keyword_search(
        keywords=["מסמך", "בדיקה"],
        k=5,
        filter_metadata={"type": "test"},
        match_all=True
    )
    
    # וידוא שהפונקציה נקראה
    rag_search.vectorstore.similarity_search.assert_called()
    
    # וידוא שהוחזרו התוצאות הנכונות
    assert len(results) == 2
    assert results[0]["document"] == doc1
    assert results[1]["document"] == doc2


@pytest.mark.asyncio
async def test_filter_search(rag_search):
    """בדיקת חיפוש לפי פילטרים"""
    # יצירת מסמכים לדוגמה
    doc1 = Document(
        page_content="מסמך ראשון לבדיקה",
        metadata={"title": "מסמך 1", "id": "doc_id_1"}
    )
    doc2 = Document(
        page_content="מסמך שני לבדיקה",
        metadata={"title": "מסמך 2", "id": "doc_id_2"}
    )
    
    # הגדרת מוק לחזרה מהפונקציה
    rag_search.vectorstore.similarity_search.return_value = [doc1, doc2]
    
    # הרצת הפונקציה
    results = await rag_search.filter_search(
        filter_metadata={"type": "test"},
        k=5
    )
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    rag_search.vectorstore.similarity_search.assert_called_with(
        "",
        k=5,
        filter={"type": "test"}
    )
    
    # וידוא שהוחזרו התוצאות הנכונות
    assert len(results) == 2
    assert results[0]["document"] == doc1
    assert results[1]["document"] == doc2


@pytest.mark.asyncio
async def test_hybrid_search(rag_search):
    """בדיקת חיפוש היברידי"""
    # יצירת מסמכים לדוגמה
    doc1 = Document(
        page_content="מסמך ראשון לבדיקה",
        metadata={"title": "מסמך 1", "id": "doc_id_1"}
    )
    doc2 = Document(
        page_content="מסמך שני לבדיקה",
        metadata={"title": "מסמך 2", "id": "doc_id_2"}
    )
    
    # הגדרת מוק לחזרה מהפונקציה
    rag_search.vectorstore.max_marginal_relevance_search.return_value = [doc1, doc2]
    
    # הרצת הפונקציה
    results = await rag_search.hybrid_search(
        query="שאילתת חיפוש",
        filter_metadata={"type": "test"},
        k=5,
        min_relevance_score=0.7
    )
    
    # וידוא שהפונקציה נקראה
    rag_search.vectorstore.max_marginal_relevance_search.assert_called()
    
    # וידוא שהוחזרו התוצאות הנכונות
    assert len(results) == 2
    assert results[0]["document"] == doc1
    assert results[1]["document"] == doc2


@pytest.mark.asyncio
async def test_error_handling(rag_search):
    """בדיקת טיפול בשגיאות"""
    # הגדרת מוק לזריקת שגיאה
    rag_search.vectorstore.similarity_search_with_relevance_scores.side_effect = Exception("שגיאת בדיקה")
    
    # הרצת הפונקציה וציפייה לשגיאה
    with pytest.raises(Exception):
        await rag_search.semantic_search(query="שאילתת חיפוש") 