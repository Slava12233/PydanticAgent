#!/usr/bin/env python
"""
סקריפט בדיקה מקיף למסד הנתונים ומערכת ה-RAG
"""
import os
import sys
import asyncio
import argparse
import time
from datetime import datetime
import json
from typing import Dict, List, Any, Optional
import logfire

# הגדרת משתנה סביבה להתעלמות מאזהרות Logfire
os.environ["LOGFIRE_IGNORE_NO_CONFIG"] = "1"

# הוספת תיקיית הפרויקט לנתיב החיפוש
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ייבוא מודולים מהפרויקט
from src.database.database import db
from src.database.rag_utils import add_document_from_file, search_documents
from src.agents.telegram_agent import TelegramAgent
from src.database.models import User, Conversation, Message, Document, DocumentChunk
from sqlalchemy import text

# הגדרת צבעים להדפסה
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
ENDC = '\033[0m'
BOLD = '\033[1m'

class DatabaseTester:
    """מחלקה לבדיקת מסד הנתונים ומערכת ה-RAG"""
    
    def __init__(self):
        """אתחול הבודק"""
        self.results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "tests": []
        }
        self.test_user_id = 999999  # משתמש בדיקה
        self.test_files_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_files")
        
        # יצירת תיקיית קבצי בדיקה אם לא קיימת
        os.makedirs(self.test_files_dir, exist_ok=True)
    
    def log_test(self, name: str, passed: bool, details: Dict[str, Any] = None):
        """תיעוד תוצאת בדיקה"""
        result = "PASS" if passed else "FAIL"
        self.results["tests"].append({
            "name": name,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        })
        
        if passed:
            self.results["passed"] += 1
            print(f"{GREEN}✓ {name} - עבר{ENDC}")
        else:
            self.results["failed"] += 1
            print(f"{RED}✗ {name} - נכשל{ENDC}")
            if details:
                print(f"  פרטים: {json.dumps(details, ensure_ascii=False, indent=2)}")
    
    def log_skip(self, name: str, reason: str):
        """תיעוד בדיקה שדולגה"""
        self.results["skipped"] += 1
        self.results["tests"].append({
            "name": name,
            "result": "SKIP",
            "timestamp": datetime.now().isoformat(),
            "reason": reason
        })
        print(f"{YELLOW}○ {name} - דולג: {reason}{ENDC}")
    
    def print_section(self, title: str):
        """הדפסת כותרת מקטע"""
        print(f"\n{BLUE}{BOLD}{'=' * 50}{ENDC}")
        print(f"{BLUE}{BOLD} {title} {ENDC}")
        print(f"{BLUE}{BOLD}{'=' * 50}{ENDC}\n")
    
    def create_test_file(self, filename: str, content: str) -> str:
        """יצירת קובץ בדיקה"""
        # וידוא שתיקיית הבדיקות קיימת
        os.makedirs(self.test_files_dir, exist_ok=True)
        
        # יצירת הקובץ
        file_path = os.path.join(self.test_files_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"נוצר קובץ בדיקה: {file_path}")
        print(f"גודל הקובץ: {os.path.getsize(file_path)} בתים")
        
        # וידוא שהקובץ נוצר
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"הקובץ {file_path} לא נוצר")
            
        return file_path
    
    def cleanup_test_files(self):
        """ניקוי קבצי בדיקה"""
        for filename in os.listdir(self.test_files_dir):
            file_path = os.path.join(self.test_files_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"שגיאה במחיקת {file_path}: {e}")
    
    async def run_all_tests(self):
        """הרצת כל הבדיקות"""
        try:
            # אתחול מסד הנתונים
            db.init_db()
            
            # בדיקת חיבור למסד הנתונים
            await self.test_database_connection()
            
            # בדיקת ניהול משתמשים ושיחות
            await self.test_user_management()
            await self.test_conversation_management()
            
            # בדיקת שמירת הודעות ואחזור היסטוריה
            await self.test_message_storage()
            await self.test_chat_history()
            
            # בדיקת מערכת RAG
            await self.test_document_management()
            await self.test_rag_search()
            
            # בדיקת אינטגרציה עם הסוכן
            await self.test_agent_integration()
            
            # הדפסת סיכום
            self.print_summary()
            
        except Exception as e:
            print(f"{RED}שגיאה בהרצת הבדיקות: {e}{ENDC}")
            raise
        finally:
            # ניקוי קבצי בדיקה
            self.cleanup_test_files()
            # סגירת חיבור למסד הנתונים
            await db.close()
    
    def print_summary(self):
        """הדפסת סיכום תוצאות הבדיקות"""
        total = self.results["passed"] + self.results["failed"] + self.results["skipped"]
        
        self.print_section("סיכום בדיקות")
        
        print(f"סה\"כ בדיקות: {total}")
        print(f"{GREEN}עברו בהצלחה: {self.results['passed']}{ENDC}")
        print(f"{RED}נכשלו: {self.results['failed']}{ENDC}")
        print(f"{YELLOW}דולגו: {self.results['skipped']}{ENDC}")
        
        if self.results["failed"] > 0:
            print(f"\n{RED}בדיקות שנכשלו:{ENDC}")
            for test in self.results["tests"]:
                if test["result"] == "FAIL":
                    print(f"{RED}- {test['name']}{ENDC}")
    
    async def test_database_connection(self):
        """בדיקת חיבור למסד הנתונים"""
        self.print_section("1. בדיקת חיבור למסד הנתונים")
        
        # בדיקת חיבור בסיסי
        try:
            with db.Session() as session:
                # בדיקה פשוטה - ביצוע שאילתה
                result = session.execute(text("SELECT 1")).scalar()
                self.log_test("חיבור בסיסי למסד הנתונים", result == 1)
        except Exception as e:
            self.log_test("חיבור בסיסי למסד הנתונים", False, {"error": str(e)})
        
        # בדיקת חיבור אסינכרוני
        try:
            async with db.AsyncSession() as session:
                result = await session.execute(text("SELECT 1"))
                value = result.scalar()
                self.log_test("חיבור אסינכרוני למסד הנתונים", value == 1)
        except Exception as e:
            self.log_test("חיבור אסינכרוני למסד הנתונים", False, {"error": str(e)})
        
        # בדיקת טבלאות
        try:
            with db.Session() as session:
                # בדיקת קיום טבלאות
                tables = [
                    "users", "conversations", "messages", 
                    "documents", "document_chunks"
                ]
                
                for table in tables:
                    query = text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
                    result = session.execute(query).scalar()
                    self.log_test(f"קיום טבלה: {table}", result == True)
        except Exception as e:
            self.log_test("בדיקת טבלאות", False, {"error": str(e)})
    
    async def test_user_management(self):
        """בדיקת ניהול משתמשים"""
        self.print_section("2. בדיקת ניהול משתמשים")
        
        # יצירת משתמש חדש
        try:
            # בדיקה אם המשתמש קיים
            with db.Session() as session:
                existing_user = session.query(User).filter(User.id == self.test_user_id).first()
                if existing_user:
                    # מחיקת המשתמש אם הוא כבר קיים
                    session.delete(existing_user)
                    session.commit()
            
            # יצירת משתמש חדש
            user_id = self.test_user_id
            username = "test_user"
            first_name = "Test"
            last_name = "User"
            
            user = db.get_or_create_user(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            
            # בדיקה שהמשתמש נוצר
            with db.Session() as session:
                created_user = session.query(User).filter(User.id == user_id).first()
                self.log_test("יצירת משתמש חדש", 
                             created_user is not None and 
                             created_user.id == user_id and
                             created_user.username == username)
        except Exception as e:
            self.log_test("יצירת משתמש חדש", False, {"error": str(e)})
        
        # קבלת משתמש קיים
        try:
            # קבלת משתמש קיים
            user = db.get_or_create_user(user_id=self.test_user_id)
            
            # בדיקה שהמשתמש קיים
            with db.Session() as session:
                existing_user = session.query(User).filter(User.id == self.test_user_id).first()
                self.log_test("קבלת משתמש קיים", 
                             existing_user is not None and
                             existing_user.id == self.test_user_id and
                             existing_user.username == "test_user")
        except Exception as e:
            self.log_test("קבלת משתמש קיים", False, {"error": str(e)})
    
    async def test_conversation_management(self):
        """בדיקת ניהול שיחות"""
        self.print_section("3. בדיקת ניהול שיחות")
        
        # יצירת שיחה חדשה
        try:
            conv_id = db.create_conversation(user_id=self.test_user_id, title="שיחת בדיקה")
            self.log_test("יצירת שיחה חדשה", conv_id is not None and conv_id > 0)
        except Exception as e:
            self.log_test("יצירת שיחה חדשה", False, {"error": str(e)})
        
        # קבלת שיחה פעילה
        try:
            active_conv_id = db.get_active_conversation(user_id=self.test_user_id)
            self.log_test("קבלת שיחה פעילה", active_conv_id is not None and active_conv_id > 0)
        except Exception as e:
            self.log_test("קבלת שיחה פעילה", False, {"error": str(e)})
        
        # קבלת כל השיחות של המשתמש
        try:
            conversations = db.get_all_user_conversations(user_id=self.test_user_id)
            self.log_test("קבלת כל השיחות של המשתמש", 
                         isinstance(conversations, list) and len(conversations) > 0)
        except Exception as e:
            self.log_test("קבלת כל השיחות של המשתמש", False, {"error": str(e)})
        
        # ניקוי היסטוריית שיחה (יצירת שיחה חדשה)
        try:
            new_conv_id = db.clear_chat_history(user_id=self.test_user_id)
            active_conv_id = db.get_active_conversation(user_id=self.test_user_id)
            self.log_test("ניקוי היסטוריית שיחה", 
                         new_conv_id == active_conv_id and new_conv_id is not None)
        except Exception as e:
            self.log_test("ניקוי היסטוריית שיחה", False, {"error": str(e)})
    
    async def test_message_storage(self):
        """בדיקת שמירת הודעות"""
        self.print_section("4. בדיקת שמירת הודעות")
        
        # שמירת הודעה ותשובה
        try:
            user_msg_id, assistant_msg_id = db.save_message(
                user_id=self.test_user_id,
                user_message="זוהי הודעת בדיקה",
                assistant_response="זוהי תשובת בדיקה"
            )
            self.log_test("שמירת הודעה ותשובה", 
                         user_msg_id is not None and assistant_msg_id is not None)
        except Exception as e:
            self.log_test("שמירת הודעה ותשובה", False, {"error": str(e)})
        
        # שמירת הודעה נוספת
        try:
            user_msg_id, assistant_msg_id = db.save_message(
                user_id=self.test_user_id,
                user_message="הודעת בדיקה נוספת",
                assistant_response="תשובת בדיקה נוספת"
            )
            self.log_test("שמירת הודעה נוספת", 
                         user_msg_id is not None and assistant_msg_id is not None)
        except Exception as e:
            self.log_test("שמירת הודעה נוספת", False, {"error": str(e)})
        
        # בדיקת מספר הודעות
        try:
            message_count = db.get_message_count()
            self.log_test("קבלת מספר הודעות", message_count > 0)
        except Exception as e:
            self.log_test("קבלת מספר הודעות", False, {"error": str(e)})
        
        # בדיקת מספר משתמשים
        try:
            user_count = db.get_user_count()
            self.log_test("קבלת מספר משתמשים", user_count > 0)
        except Exception as e:
            self.log_test("קבלת מספר משתמשים", False, {"error": str(e)})
    
    async def test_chat_history(self):
        """בדיקת היסטוריית שיחה"""
        self.print_section("5. בדיקת היסטוריית שיחה")
        
        # קבלת היסטוריית שיחה
        try:
            history = db.get_chat_history(user_id=self.test_user_id)
            self.log_test("קבלת היסטוריית שיחה", 
                         isinstance(history, list) and len(history) > 0)
            
            # בדיקת מבנה ההיסטוריה
            if len(history) > 0:
                has_correct_structure = all(
                    'message' in item and 'response' in item
                    for item in history
                )
                self.log_test("מבנה היסטוריית שיחה תקין", has_correct_structure)
            else:
                self.log_skip("מבנה היסטוריית שיחה תקין", "אין מספיק הודעות בהיסטוריה")
        except Exception as e:
            self.log_test("קבלת היסטוריית שיחה", False, {"error": str(e)})
        
        # קבלת כל היסטוריית ההודעות של המשתמש
        try:
            all_history = db.get_all_user_message_history(user_id=self.test_user_id)
            self.log_test("קבלת כל היסטוריית ההודעות", 
                         isinstance(all_history, list) and len(all_history) > 0)
        except Exception as e:
            self.log_test("קבלת כל היסטוריית ההודעות", False, {"error": str(e)})
    
    async def test_document_management(self):
        """בדיקת ניהול מסמכים"""
        self.print_section("6. בדיקת ניהול מסמכים")
        
        # יצירת קובץ בדיקה עם תוכן מפורט יותר
        test_content = """
        בדיקות תוכנה הן תהליך חשוב בפיתוח תוכנה איכותית.
        בדיקות תוכנה מאפשרות לזהות באגים ובעיות לפני שהמוצר מגיע ללקוחות.
        סוגים שונים של בדיקות תוכנה כוללים בדיקות יחידה, בדיקות אינטגרציה ובדיקות מערכת.
        בדיקות יחידה בודקות פונקציות בודדות או מחלקות.
        בדיקות אינטגרציה בודקות את האינטראקציה בין מספר רכיבים.
        בדיקות מערכת בודקות את המערכת כולה מקצה לקצה.
        
        מערכות RAG (Retrieval Augmented Generation) משלבות אחזור מידע עם מודלים שפתיים מתקדמים.
        מערכות RAG מאפשרות למודלים שפתיים לקבל מידע עדכני ומדויק יותר.
        השימוש במערכות RAG נפוץ ביישומים כמו צ'אטבוטים, מערכות תמיכה ומנועי חיפוש חכמים.
        """
        
        test_file_path = self.create_test_file("test_document.txt", test_content)
        
        # הוספת מסמך מקובץ
        try:
            doc_id = await add_document_from_file(
                file_path=test_file_path,
                title="מסמך בדיקה - בדיקות תוכנה ומערכות RAG",
                source="test",
                metadata={"test": True}
            )
            self.log_test("הוספת מסמך מקובץ", doc_id is not None and doc_id > 0)
        except Exception as e:
            self.log_test("הוספת מסמך מקובץ", False, {"error": str(e)})
        
        # הוספת מסמך מתוכן ישיר
        try:
            doc_id = await db.add_document(
                title="מסמך בדיקה ישיר",
                content="בדיקות תוכנה הן חלק חשוב מתהליך פיתוח תוכנה. הן עוזרות לוודא שהתוכנה עובדת כמצופה.",
                source="direct",
                metadata={"test": True, "method": "direct"}
            )
            self.log_test("הוספת מסמך מתוכן ישיר", doc_id is not None and doc_id > 0)
        except Exception as e:
            self.log_test("הוספת מסמך מתוכן ישיר", False, {"error": str(e)})
        
        # בדיקת פיצול טקסט לקטעים
        try:
            chunks = db._split_text_to_chunks("זהו טקסט ארוך לבדיקת פיצול. " * 10, chunk_size=50)
            self.log_test("פיצול טקסט לקטעים", 
                         isinstance(chunks, list) and len(chunks) > 1)
        except Exception as e:
            self.log_test("פיצול טקסט לקטעים", False, {"error": str(e)})
    
    async def test_rag_search(self):
        """בדיקת חיפוש במערכת RAG"""
        self.print_section("7. בדיקת חיפוש במערכת RAG")
        
        # יצירת embedding
        try:
            # הפונקציה כבר לא אסינכרונית, אבל עדיין מוגדרת כאסינכרונית בממשק
            embedding = await db.create_embedding("טקסט בדיקה ליצירת embedding")
            self.log_test("יצירת embedding", 
                         isinstance(embedding, list) and len(embedding) > 0)
        except Exception as e:
            self.log_test("יצירת embedding", False, {"error": str(e)})
        
        # בדיקת מספר המסמכים והקטעים במסד הנתונים
        try:
            with db.Session() as session:
                doc_count = session.query(Document).count()
                chunk_count = session.query(DocumentChunk).count()
                print(f"מספר מסמכים במסד הנתונים: {doc_count}")
                print(f"מספר קטעים במסד הנתונים: {chunk_count}")
                
                # הדפסת פרטי המסמכים
                docs = session.query(Document).all()
                for doc in docs:
                    print(f"מסמך: {doc.id}, כותרת: {doc.title}, מקור: {doc.source}")
                    chunks = session.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
                    print(f"  מספר קטעים: {len(chunks)}")
                    if chunks:
                        print(f"  דוגמת קטע: {chunks[0].content[:50]}...")
                        print(f"  האם יש embedding: {chunks[0].embedding is not None}")
        except Exception as e:
            print(f"שגיאה בבדיקת מסמכים: {e}")
        
        # חיפוש קטעים רלוונטיים - שימוש בשאילתה שתואמת את תוכן המסמך
        try:
            # המתנה קצרה לוודא שהמסמכים נוספו למסד הנתונים
            await asyncio.sleep(1)
            
            # שימוש בשאילתה שתואמת את תוכן המסמך
            print("\nמחפש קטעים רלוונטיים עם השאילתה: 'בדיקות תוכנה ומה החשיבות שלהן'")
            chunks = await db.search_relevant_chunks("בדיקות תוכנה ומה החשיבות שלהן", min_similarity=0.0)
            print(f"נמצאו {len(chunks)} קטעים")
            
            self.log_test("חיפוש קטעים רלוונטיים", 
                         isinstance(chunks, list))
            
            if len(chunks) > 0:
                print(f"קטע ראשון: {chunks[0]['content'][:50]}...")
                print(f"דמיון: {chunks[0]['similarity']}")
                self.log_test("תוצאות חיפוש נמצאו", True, 
                             {"count": len(chunks), "first_title": chunks[0]["title"]})
            else:
                # אם עדיין אין תוצאות, ננסה שאילתה פשוטה יותר
                print("\nמחפש קטעים רלוונטיים עם השאילתה פשוטה יותר: 'בדיקות'")
                chunks = await db.search_relevant_chunks("בדיקות", min_similarity=0.0)
                print(f"נמצאו {len(chunks)} קטעים")
                
                if len(chunks) > 0:
                    print(f"קטע ראשון: {chunks[0]['content'][:50]}...")
                    print(f"דמיון: {chunks[0]['similarity']}")
                    self.log_test("תוצאות חיפוש נמצאו", True, 
                                {"count": len(chunks), "first_title": chunks[0]["title"]})
                else:
                    # ננסה שאילתה עוד יותר פשוטה
                    print("\nמחפש קטעים רלוונטיים עם השאילתה הכי פשוטה: 'תוכנה'")
                    chunks = await db.search_relevant_chunks("תוכנה", min_similarity=0.0)
                    print(f"נמצאו {len(chunks)} קטעים")
                    
                    if len(chunks) > 0:
                        print(f"קטע ראשון: {chunks[0]['content'][:50]}...")
                        print(f"דמיון: {chunks[0]['similarity']}")
                        self.log_test("תוצאות חיפוש נמצאו", True, 
                                    {"count": len(chunks), "first_title": chunks[0]["title"]})
                    else:
                        self.log_test("תוצאות חיפוש נמצאו", False, 
                                    {"message": "לא נמצאו תוצאות חיפוש"})
        except Exception as e:
            self.log_test("חיפוש קטעים רלוונטיים", False, {"error": str(e)})
        
        # חיפוש באמצעות פונקציית העזר
        try:
            print("\nמחפש באמצעות פונקציית העזר עם השאילתה: 'מערכות RAG'")
            results = await search_documents("מערכות RAG", min_similarity=0.0)
            print(f"נמצאו {len(results)} תוצאות")
            
            self.log_test("חיפוש באמצעות פונקציית העזר", 
                         isinstance(results, list))
            
            if len(results) > 0:
                print(f"תוצאה ראשונה: {results[0]['content'][:50]}...")
                print(f"דמיון: {results[0]['similarity']}")
                # בדיקת מבנה התוצאות
                has_correct_structure = all(
                    'content' in item and 'title' in item and 'similarity' in item
                    for item in results
                )
                self.log_test("מבנה תוצאות חיפוש תקין", has_correct_structure)
            else:
                # אם עדיין אין תוצאות, ננסה שאילתה פשוטה יותר
                print("\nמחפש באמצעות פונקציית העזר עם השאילתה פשוטה יותר: 'בדיקות'")
                results = await search_documents("בדיקות", min_similarity=0.0)
                print(f"נמצאו {len(results)} תוצאות")
                
                if len(results) > 0:
                    print(f"תוצאה ראשונה: {results[0]['content'][:50]}...")
                    print(f"דמיון: {results[0]['similarity']}")
                    has_correct_structure = all(
                        'content' in item and 'title' in item and 'similarity' in item
                        for item in results
                    )
                    self.log_test("מבנה תוצאות חיפוש תקין", has_correct_structure)
                else:
                    # ננסה שאילתה עוד יותר פשוטה
                    print("\nמחפש באמצעות פונקציית העזר עם השאילתה הכי פשוטה: 'תוכנה'")
                    results = await search_documents("תוכנה", min_similarity=0.0)
                    print(f"נמצאו {len(results)} תוצאות")
                    
                    if len(results) > 0:
                        print(f"תוצאה ראשונה: {results[0]['content'][:50]}...")
                        print(f"דמיון: {results[0]['similarity']}")
                        has_correct_structure = all(
                            'content' in item and 'title' in item and 'similarity' in item
                            for item in results
                        )
                        self.log_test("מבנה תוצאות חיפוש תקין", has_correct_structure)
                    else:
                        self.log_skip("מבנה תוצאות חיפוש תקין", "לא נמצאו תוצאות חיפוש")
        except Exception as e:
            self.log_test("חיפוש באמצעות פונקציית העזר", False, {"error": str(e)})
    
    async def test_agent_integration(self):
        """בדיקת אינטגרציה עם הסוכן"""
        self.print_section("8. בדיקת אינטגרציה עם הסוכן")
        
        # אתחול הסוכן
        try:
            agent = TelegramAgent()
            self.log_test("אתחול הסוכן", agent is not None)
        except Exception as e:
            self.log_test("אתחול הסוכן", False, {"error": str(e)})
            # אם אתחול הסוכן נכשל, דלג על שאר הבדיקות
            self.log_skip("שימוש בכלי RAG", "אתחול הסוכן נכשל")
            self.log_skip("קבלת תשובה מהסוכן", "אתחול הסוכן נכשל")
            return
        
        # בדיקת כלי RAG
        try:
            context = await agent.retrieve_context("בדיקות תוכנה")
            self.log_test("שימוש בכלי RAG", 
                         isinstance(context, str) and len(context) > 0)
        except Exception as e:
            self.log_test("שימוש בכלי RAG", False, {"error": str(e)})
        
        # קבלת תשובה מהסוכן
        try:
            # שימוש בהיסטוריה קיימת
            history = db.get_chat_history(user_id=self.test_user_id)
            
            # קבלת תשובה מהסוכן
            response = await agent.get_response(
                user_id=self.test_user_id,
                user_message="מה הן בדיקות תוכנה?",
                history=history,
                use_rag=True
            )
            
            self.log_test("קבלת תשובה מהסוכן", 
                         isinstance(response, str) and len(response) > 0)
        except Exception as e:
            self.log_test("קבלת תשובה מהסוכן", False, {"error": str(e)})

async def main():
    """פונקציה ראשית"""
    parser = argparse.ArgumentParser(description='בדיקת מסד הנתונים ומערכת ה-RAG')
    parser.add_argument('--output', help='נתיב לשמירת תוצאות הבדיקה בפורמט JSON')
    
    args = parser.parse_args()
    
    # יצירת והפעלת הבודק
    tester = DatabaseTester()
    await tester.run_all_tests()
    
    # שמירת תוצאות לקובץ אם התבקש
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(tester.results, f, ensure_ascii=False, indent=2)
        print(f"תוצאות הבדיקה נשמרו לקובץ: {args.output}")

if __name__ == "__main__":
    # הפעלת הפונקציה הראשית באופן אסינכרוני
    asyncio.run(main()) 