# src/database/database.py
import os
import asyncio
from datetime import datetime
import json
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import create_engine, desc, asc, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
import asyncpg
import openai
from pgvector.sqlalchemy import Vector
import logfire

from src.core.config import DATABASE_URL
from src.database.models import Base, User, Conversation, Message, Document, DocumentChunk

class Database:
    """מחלקה לניהול מסד הנתונים והאינטראקציות איתו"""
    
    def __init__(self, db_url=None):
        """אתחול מסד הנתונים"""
        if db_url is None:
            # שימוש במשתני סביבה לחיבור למסד הנתונים
            db_host = os.getenv("POSTGRES_HOST", "localhost")
            db_port = os.getenv("POSTGRES_PORT", "5432")
            db_name = os.getenv("POSTGRES_DB", "postgres")
            db_user = os.getenv("POSTGRES_USER", "postgres")
            db_password = os.getenv("POSTGRES_PASSWORD", "SSll456456!!")
            
            db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            async_db_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            async_db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
        
        self.db_url = db_url
        self.async_db_url = async_db_url
        self.engine = None
        self.async_engine = None
        self.Session = None
        self.AsyncSession = None
    
    def init_db(self, recreate_tables=False):
        """אתחול מסד הנתונים - יצירת חיבור וטבלאות"""
        with logfire.span('database_init'):
            # יצירת מנוע SQLAlchemy סינכרוני
            self.engine = create_engine(self.db_url)
            
            # יצירת מנוע SQLAlchemy אסינכרוני
            self.async_engine = create_async_engine(self.async_db_url)
            
            # מחיקת טבלאות קיימות אם נדרש
            if recreate_tables:
                logfire.info('dropping_existing_tables')
                Base.metadata.drop_all(self.engine)
            
            # יצירת הטבלאות אם הן לא קיימות
            Base.metadata.create_all(self.engine)
            
            # יצירת session factory סינכרוני
            self.Session = sessionmaker(bind=self.engine)
            
            # יצירת session factory אסינכרוני
            self.AsyncSession = sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logfire.info('database_connected', engine=str(self.engine.url).split('@')[0])
    
    #
    # שיטות לניהול משתמשים
    #
    
    def get_or_create_user(self, user_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None) -> User:
        """קבלת משתמש קיים או יצירת חדש"""
        with self.Session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                user = User(
                    id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
                logfire.info("created_new_user", user_id=user_id)
            else:
                # עדכון זמן פעילות אחרון
                user.last_active = datetime.utcnow()
                
            session.commit()
            return user
    
    #
    # שיטות לניהול שיחות
    #
    
    def create_conversation(self, user_id: int, title: str = None) -> int:
        """יצירת שיחה חדשה"""
        with self.Session() as session:
            # ודא שהמשתמש קיים
            self.get_or_create_user(user_id)
            
            # סמן שיחות קודמות כלא פעילות
            old_convs = session.query(Conversation)\
                .filter(Conversation.user_id == user_id, Conversation.is_active == True)\
                .all()
                
            for conv in old_convs:
                conv.is_active = False
            
            # יצירת שיחה חדשה
            new_conv = Conversation(
                user_id=user_id,
                title=title or f"שיחה מתאריך {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            )
            session.add(new_conv)
            session.commit()
            
            logfire.info("created_new_conversation", 
                       user_id=user_id, conversation_id=new_conv.id)
            return new_conv.id
    
    def get_active_conversation(self, user_id: int) -> Optional[int]:
        """קבלת השיחה הפעילה של המשתמש"""
        with self.Session() as session:
            conv = session.query(Conversation)\
                .filter(Conversation.user_id == user_id, Conversation.is_active == True)\
                .first()
            
            if not conv:
                # אם אין שיחה פעילה, יצירת שיחה חדשה
                return self.create_conversation(user_id)
            
            return conv.id
    
    def get_all_user_conversations(self, user_id: int) -> List[Dict[str, Any]]:
        """קבלת כל השיחות של המשתמש"""
        with self.Session() as session:
            convs = session.query(Conversation)\
                .filter(Conversation.user_id == user_id)\
                .order_by(desc(Conversation.updated_at))\
                .all()
            
            return [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                    "is_active": conv.is_active
                }
                for conv in convs
            ]
    
    #
    # שיטות לניהול הודעות
    #
    
    def save_message(self, user_id: int, user_message: str, assistant_response: str) -> Tuple[int, int]:
        """שמירת הודעת משתמש והתשובה מהסוכן"""
        with self.Session() as session:
            # קבלת שיחה פעילה
            conv_id = self.get_active_conversation(user_id)
            
            # שמירת הודעת המשתמש
            user_msg = Message(
                conversation_id=conv_id,
                role="user",
                content=user_message
            )
            session.add(user_msg)
            
            # שמירת תשובת המערכת
            assistant_msg = Message(
                conversation_id=conv_id,
                role="assistant",
                content=assistant_response
            )
            session.add(assistant_msg)
            
            # עדכון זמן השיחה
            conv = session.query(Conversation).get(conv_id)
            conv.updated_at = datetime.utcnow()
            
            session.commit()
            
            # שמירת ה-ID לפני סגירת הסשן
            user_msg_id = user_msg.id
            assistant_msg_id = assistant_msg.id
            
            # החזרת מזהי ההודעות
            return user_msg_id, assistant_msg_id
    
    def get_chat_history(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """קבלת היסטוריית השיחה הפעילה"""
        with self.Session() as session:
            # מציאת שיחה פעילה
            conv_id = self.get_active_conversation(user_id)
            
            # שליפת הודעות מסודרות לפי זמן
            messages = session.query(Message)\
                .filter(Message.conversation_id == conv_id)\
                .order_by(asc(Message.timestamp))\
                .all()
            
            # ארגון הודעות לפורמט המתאים לסוכן
            history = []
            i = 0
            while i < len(messages) - 1:
                if messages[i].role == 'user' and messages[i+1].role == 'assistant':
                    history.append({
                        'message': messages[i].content,
                        'response': messages[i+1].content
                    })
                i += 2
            
            # החזרת ההיסטוריה המוגבלת
            return history[-limit:] if len(history) > limit else history
    
    def get_all_user_message_history(self, user_id: int) -> List[Dict[str, Any]]:
        """קבלת כל היסטוריית ההודעות של המשתמש (משיחות קודמות)"""
        with self.Session() as session:
            # מציאת כל השיחות של המשתמש
            convs = session.query(Conversation.id)\
                .filter(Conversation.user_id == user_id)\
                .order_by(desc(Conversation.updated_at))\
                .all()
            
            conv_ids = [conv.id for conv in convs]
            
            if not conv_ids:
                return []
            
            # שליפת הודעות מכל השיחות
            all_messages = []
            for conv_id in conv_ids:
                messages = session.query(Message)\
                    .filter(Message.conversation_id == conv_id)\
                    .order_by(asc(Message.timestamp))\
                    .all()
                
                i = 0
                while i < len(messages) - 1:
                    if messages[i].role == 'user' and messages[i+1].role == 'assistant':
                        all_messages.append({
                            'message': messages[i].content,
                            'response': messages[i+1].content,
                            'timestamp': messages[i].timestamp.isoformat(),
                            'conversation_id': conv_id
                        })
                    i += 2
            
            return all_messages
    
    def clear_chat_history(self, user_id: int) -> int:
        """מחיקת היסטוריית שיחה נוכחית על ידי יצירת שיחה חדשה"""
        return self.create_conversation(user_id)
    
    #
    # שיטות למערכת RAG
    #
    
    async def create_embedding(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """יצירת embedding לטקסט באמצעות OpenAI API"""
        with logfire.span("creating_embedding", text_length=len(text)):
            try:
                # שימוש בגרסה הסינכרונית של ה-API
                response = openai.embeddings.create(
                    input=text,
                    model=model
                )
                return response.data[0].embedding
            except Exception as e:
                logfire.error("embedding_creation_error", error=str(e))
                # החזרת וקטור אפס במקרה של שגיאה
                return [0.0] * 1536
    
    async def add_document(self, title: str, content: str, source: str, metadata: dict = None) -> int:
        """הוספת מסמך למסד הנתונים"""
        try:
            # יצירת מסמך חדש
            document = Document(
                title=title,
                source=source,
                content=content,
                doc_metadata=metadata or {}  # שינוי שם מ-metadata ל-doc_metadata
            )
            with self.Session() as session:
                session.add(document)
                session.commit()
                doc_id = document.id
            
            # חלוקה לקטעים (chunks)
            chunks = self._split_text_to_chunks(content, 1000)
            
            # יצירת embeddings לכל קטע ושמירתם
            for i, chunk_text in enumerate(chunks):
                embedding = await self.create_embedding(chunk_text)
                
                with self.Session() as session:
                    chunk = DocumentChunk(
                        document_id=doc_id,
                        content=chunk_text,
                        chunk_index=i,
                        embedding=embedding
                    )
                    session.add(chunk)
                    session.commit()
            
            logfire.info("added_document_to_rag", 
                        doc_id=doc_id, 
                        title=title, 
                        chunks_count=len(chunks))
            return doc_id
        except Exception as e:
            logfire.error("error_adding_document", error=str(e))
            return -1
    
    def _split_text_to_chunks(self, text: str, chunk_size: int) -> List[str]:
        """חלוקת טקסט לקטעים באורך דומה"""
        # פיצול פשוט לפי אורך. ניתן לשפר זאת בעתיד לפיצול חכם יותר
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            if chunk.strip():  # הוסף רק קטעים עם תוכן
                chunks.append(chunk)
        return chunks
    
    async def search_relevant_chunks(self, query: str, limit: int = 5, min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """חיפוש קטעים רלוונטיים במערכת RAG לפי שאילתה"""
        with logfire.span("rag_search", query=query):
            try:
                print(f"חיפוש קטעים רלוונטיים עבור: '{query}'")
                
                # יצירת embedding לשאילתה
                query_embedding = await self.create_embedding(query)
                print(f"נוצר embedding לשאילתה באורך: {len(query_embedding)}")
                
                async with self.AsyncSession() as session:
                    # שאילתה פשוטה שמחזירה את כל הקטעים
                    query_sql = text("""
                    SELECT 
                        dc.id, 
                        dc.content, 
                        d.title, 
                        d.source,
                        dc.embedding
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    """)
                    
                    result = await session.execute(query_sql)
                    rows = result.fetchall()
                    print(f"נמצאו {len(rows)} קטעים במסד הנתונים")
                    
                    # חישוב דמיון קוסינוס בקוד Python
                    chunks_with_similarity = []
                    for row in rows:
                        # חישוב דמיון קוסינוס בין וקטורים
                        similarity = self._cosine_similarity(query_embedding, row.embedding) if row.embedding else 0
                        print(f"קטע {row.id}, כותרת: {row.title}, דמיון: {similarity:.4f}")
                        
                        # הוספת הקטע לרשימת התוצאות אם הדמיון מעל הסף המינימלי
                        # אם הסף הוא 0, נוסיף את כל הקטעים
                        if similarity >= min_similarity:
                            chunks_with_similarity.append({
                                "id": row.id,
                                "content": row.content,
                                "title": row.title,
                                "source": row.source,
                                "similarity": similarity
                            })
                    
                    # מיון לפי דמיון והגבלה למספר התוצאות הרצוי
                    chunks = sorted(chunks_with_similarity, key=lambda x: x["similarity"], reverse=True)[:limit]
                    
                    print(f"מוחזרים {len(chunks)} קטעים מתוך {len(chunks_with_similarity)} שנמצאו")
                    
                    # אם אין תוצאות, נחזיר לפחות את הקטעים הכי דומים (גם אם הדמיון נמוך)
                    if not chunks and chunks_with_similarity:
                        print("אין תוצאות מעל הסף, מחזיר את הקטעים הכי דומים")
                        chunks = sorted(chunks_with_similarity, key=lambda x: x["similarity"], reverse=True)[:limit]
                    
                    logfire.info("rag_search_results", 
                               query=query, 
                               chunks_found=len(chunks))
                    return chunks
            except Exception as e:
                print(f"שגיאה בחיפוש קטעים: {e}")
                logfire.error("rag_search_error", error=str(e))
                return []
    
    def _cosine_similarity(self, vec1, vec2):
        """חישוב דמיון קוסינוס בין שני וקטורים"""
        if not vec1 or not vec2:
            return 0
        
        try:
            import numpy as np
            
            # המרה למערכי numpy
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            # חישוב דמיון קוסינוס
            dot_product = np.dot(vec1_np, vec2_np)
            norm_vec1 = np.linalg.norm(vec1_np)
            norm_vec2 = np.linalg.norm(vec2_np)
            
            if norm_vec1 == 0 or norm_vec2 == 0:
                return 0
                
            return dot_product / (norm_vec1 * norm_vec2)
        except Exception as e:
            logfire.error("cosine_similarity_error", error=str(e))
            return 0
    
    def get_message_count(self) -> int:
        """קבלת מספר ההודעות הכולל במערכת - שימושי לסטטיסטיקות"""
        with self.Session() as session:
            count = session.query(Message).count()
            return count
    
    def get_user_count(self) -> int:
        """קבלת מספר המשתמשים הייחודיים - שימושי לסטטיסטיקות"""
        with self.Session() as session:
            # COUNT DISTINCT user_id
            count = session.query(User.id).distinct().count()
            return count
            
    async def close(self):
        """סגירת החיבור למסד הנתונים"""
        if self.engine:
            logfire.info('database_connection_closing')
            # סגירת מנועים
            self.engine.dispose()
            if self.async_engine:
                await self.async_engine.dispose()

# יצירת מופע גלובלי של Database
db = Database() 