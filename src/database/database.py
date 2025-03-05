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
from contextlib import contextmanager, asynccontextmanager
import logging
import traceback

# יבוא הגדרות מקובץ config
from src.core.config import LOGFIRE_API_KEY, LOGFIRE_PROJECT

# הגדרת פרויקט logfire מראש
if 'LOGFIRE_PROJECT' not in os.environ:
    os.environ['LOGFIRE_PROJECT'] = LOGFIRE_PROJECT

import logfire
# נסיון להגדיר את ה-PydanticPlugin אם הוא זמין
try:
    logfire.configure(
        token=LOGFIRE_API_KEY,
        pydantic_plugin=logfire.PydanticPlugin(record='all')
    )
except (AttributeError, ImportError):
    # אם ה-PydanticPlugin לא זמין, נגדיר רק את הטוקן
    logfire.configure(token=LOGFIRE_API_KEY)

from src.core.config import DATABASE_URL
from src.database.models import Base, User, Conversation, Message, Document, DocumentChunk

# הגדרת לוגר
logger = logging.getLogger(__name__)

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
    
    def get_chat_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        קבלת היסטוריית השיחה הפעילה
        
        Args:
            user_id: מזהה המשתמש בטלגרם
            limit: מספר ההודעות המקסימלי לשליפה
            
        Returns:
            רשימת הודעות בפורמט {message, response}
        """
        with self.Session() as session:
            try:
                # מציאת המשתמש לפי מזהה טלגרם
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    logger.warning(f"User {user_id} not found in database")
                    return []
                
                # מציאת השיחה האחרונה של המשתמש
                conv = session.query(Conversation)\
                    .filter(Conversation.user_id == user.id)\
                    .order_by(Conversation.updated_at.desc())\
                    .first()
                
                if not conv:
                    logger.warning(f"No active conversation found for user {user_id}")
                    return []
                
                # שליפת הודעות מסודרות לפי זמן
                messages = session.query(Message)\
                    .filter(Message.conversation_id == conv.id)\
                    .order_by(Message.timestamp.asc())\
                    .all()
                
                # ארגון הודעות לפורמט המתאים לסוכן
                history = []
                i = 0
                while i < len(messages) - 1:
                    if messages[i].role == 'user' and i+1 < len(messages) and messages[i+1].role == 'assistant':
                        history.append({
                            'message': messages[i].content,
                            'response': messages[i+1].content
                        })
                        i += 2
                    else:
                        # אם אין זוג מסודר, נוסיף רק את ההודעה הנוכחית
                        history.append({
                            'message': messages[i].content,
                            'response': "" if i+1 >= len(messages) else messages[i+1].content
                        })
                        i += 1
                
                # החזרת ההיסטוריה המוגבלת
                return history[-limit:] if len(history) > limit else history
            except Exception as e:
                logger.error(f"Error getting chat history: {e}")
                return []
    
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
            max_retries = 5
            retry_delay = 1.0  # שניה אחת בהתחלה
            
            for attempt in range(max_retries):
                try:
                    # שימוש בגרסה הסינכרונית של ה-API
                    response = openai.embeddings.create(
                        input=text,
                        model=model
                    )
                    return response.data[0].embedding
                except Exception as e:
                    error_message = str(e).lower()
                    
                    # בדיקה אם זו שגיאת rate limit
                    if "rate limit" in error_message or "429" in error_message:
                        if attempt < max_retries - 1:  # אם זה לא הניסיון האחרון
                            # לוג על הניסיון החוזר
                            logfire.warning(
                                "embedding_rate_limit", 
                                attempt=attempt + 1, 
                                max_retries=max_retries,
                                retry_delay=retry_delay
                            )
                            
                            # המתנה לפני הניסיון הבא עם הכפלת זמן ההמתנה בכל פעם (exponential backoff)
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2  # הכפלת זמן ההמתנה לניסיון הבא
                            continue
                    
                    # אם הגענו לכאן, זו שגיאה אחרת או שנגמרו הניסיונות
                    logfire.error("embedding_creation_error", error=str(e), attempt=attempt + 1)
                    
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
                    # בדיקה אם הטבלה document_chunks קיימת
                    try:
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
                    except Exception as e:
                        print(f"שגיאה בשאילתת SQL: {str(e)}")
                        # אם יש שגיאה, ננסה לבדוק אם הטבלאות קיימות
                        check_tables_sql = text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        """)
                        tables_result = await session.execute(check_tables_sql)
                        tables = [row[0] for row in tables_result.fetchall()]
                        print(f"טבלאות קיימות: {tables}")
                        
                        if 'documents' not in tables or 'document_chunks' not in tables:
                            print("הטבלאות document_chunks או documents לא קיימות")
                            return []
                        
                        # בדיקת מבנה הטבלה
                        check_columns_sql = text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'document_chunks'
                        """)
                        columns_result = await session.execute(check_columns_sql)
                        columns = [row[0] for row in columns_result.fetchall()]
                        print(f"עמודות בטבלת document_chunks: {columns}")
                        
                        # אם אין עמודת embedding, נחזיר רשימה ריקה
                        if 'embedding' not in columns:
                            print("עמודת embedding לא קיימת בטבלת document_chunks")
                            return []
                        
                        # ננסה שאילתה אחרת שלא משתמשת בעמודות שאולי לא קיימות
                        query_sql = text("""
                        SELECT 
                            dc.id, 
                            dc.content, 
                            d.title, 
                            d.source
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        LIMIT :limit
                        """)
                        
                        result = await session.execute(query_sql, {"limit": limit})
                        rows = result.fetchall()
                        print(f"נמצאו {len(rows)} קטעים במסד הנתונים (ללא embedding)")
                        
                        # נחזיר את התוצאות ללא חישוב דמיון
                        return [
                            {
                                "id": row.id,
                                "content": row.content,
                                "title": row.title,
                                "source": row.source,
                                "similarity": 0,
                                "similarity_percentage": 0
                            }
                            for row in rows
                        ]
                    
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
                                "similarity": similarity,
                                "similarity_percentage": similarity * 100  # המרה לאחוזים
                            })
                    
                    # מיון התוצאות לפי דמיון (מהגבוה לנמוך)
                    sorted_chunks = sorted(chunks_with_similarity, key=lambda x: x["similarity"], reverse=True)
                    
                    # החזרת מספר התוצאות המבוקש
                    return sorted_chunks[:limit]
            except Exception as e:
                print(f"שגיאה כללית בחיפוש קטעים: {str(e)}")
                logfire.error('search_relevant_chunks_error', error=str(e))
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
            
    async def close_all_connections(self):
        """סגירת כל החיבורים לדאטהבייס"""
        if self.async_engine:
            await self.async_engine.dispose()
        if self.engine:
            self.engine.dispose()
        logger.info("כל החיבורים לדאטהבייס נסגרו")

    @contextmanager
    def Session(self):
        """מנהל הקשר לסשן סינכרוני"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_session(self):
        """מנהל הקשר לסשן אסינכרוני"""
        session = self.AsyncSession()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

    async def get_conversation_messages(self, conversation_id: int, limit: int = 10, session = None) -> List[Message]:
        """
        שליפת הודעות משיחה לפי מזהה השיחה
        
        Args:
            conversation_id: מזהה השיחה
            limit: מספר ההודעות המקסימלי לשליפה
            session: סשן מסד נתונים (אופציונלי)
            
        Returns:
            רשימת הודעות
        """
        if session is None:
            session = await self.get_session()
            close_session = True
        else:
            close_session = False
        
        try:
            # שליפת ההודעות האחרונות מהשיחה בסדר כרונולוגי
            query = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
            
            if limit:
                query = query.limit(limit)
            
            result = await session.execute(query)
            messages = result.scalars().all()
            
            return messages
        except Exception as e:
            logger.error(f"Error getting conversation messages: {e}")
            return []
        finally:
            if close_session:
                await session.close()

# יצירת אובייקט מסד נתונים גלובלי
db = Database() 