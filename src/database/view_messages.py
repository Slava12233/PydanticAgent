#!/usr/bin/env python
"""
כלי לצפייה בהודעות השמורות במסד הנתונים
"""
import os
import sys
import csv
import argparse
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from tabulate import tabulate

# הוספת תיקיית הפרויקט לנתיב החיפוש
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.config import POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
from src.database.models import User, Conversation, Message

def get_db_connection():
    """יצירת חיבור למסד הנתונים"""
    db_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()

def view_messages(csv_file=None, limit=100):
    """הצגת הודעות מהמסד נתונים"""
    session = get_db_connection()
    
    try:
        # שליפת הודעות עם מידע על המשתמש והשיחה
        query = """
        SELECT 
            m.id, 
            u.username, 
            u.first_name, 
            u.last_name, 
            c.title as conversation_title,
            m.role, 
            m.content, 
            m.timestamp
        FROM 
            messages m
        JOIN 
            conversations c ON m.conversation_id = c.id
        JOIN 
            users u ON c.user_id = u.id
        ORDER BY 
            m.timestamp DESC
        LIMIT :limit
        """
        
        result = session.execute(text(query), {"limit": limit})
        
        # המרת התוצאות לרשימה של מילונים
        messages = []
        for row in result:
            messages.append({
                'id': row.id,
                'username': row.username or 'אנונימי',
                'name': f"{row.first_name or ''} {row.last_name or ''}".strip() or 'לא ידוע',
                'conversation': row.conversation_title,
                'role': row.role,
                'content': row.content[:50] + ('...' if len(row.content) > 50 else ''),
                'timestamp': row.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # אם צריך לייצא ל-CSV
        if csv_file:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=messages[0].keys())
                writer.writeheader()
                writer.writerows(messages)
            print(f"נשמרו {len(messages)} הודעות לקובץ {csv_file}")
            return
        
        # הדפסת הטבלה למסך
        print(tabulate(messages, headers='keys', tablefmt='pretty'))
        print(f"\nסה\"כ: {len(messages)} הודעות")
        
        # הצגת סטטיסטיקות
        user_count = session.query(User).count()
        conversation_count = session.query(Conversation).count()
        message_count = session.query(Message).count()
        
        print(f"\nסטטיסטיקות:")
        print(f"- מספר משתמשים: {user_count}")
        print(f"- מספר שיחות: {conversation_count}")
        print(f"- סה\"כ הודעות: {message_count}")
        
    finally:
        session.close()

def view_conversations():
    """הצגת שיחות מהמסד נתונים"""
    session = get_db_connection()
    
    try:
        # שליפת שיחות עם מידע על המשתמש ומספר ההודעות
        query = """
        SELECT 
            c.id, 
            u.username, 
            u.first_name, 
            u.last_name, 
            c.title,
            c.created_at,
            c.updated_at,
            c.is_active,
            COUNT(m.id) as message_count
        FROM 
            conversations c
        JOIN 
            users u ON c.user_id = u.id
        LEFT JOIN 
            messages m ON c.id = m.conversation_id
        GROUP BY 
            c.id, u.username, u.first_name, u.last_name
        ORDER BY 
            c.updated_at DESC
        """
        
        result = session.execute(text(query))
        
        # המרת התוצאות לרשימה של מילונים
        conversations = []
        for row in result:
            conversations.append({
                'id': row.id,
                'username': row.username or 'אנונימי',
                'name': f"{row.first_name or ''} {row.last_name or ''}".strip() or 'לא ידוע',
                'title': row.title,
                'created_at': row.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': row.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_active': 'כן' if row.is_active else 'לא',
                'message_count': row.message_count
            })
        
        # הדפסת הטבלה למסך
        print(tabulate(conversations, headers='keys', tablefmt='pretty'))
        print(f"\nסה\"כ: {len(conversations)} שיחות")
        
    finally:
        session.close()

def view_documents():
    """הצגת מסמכים מהמסד נתונים"""
    session = get_db_connection()
    
    try:
        # שליפת מסמכים עם מידע על מספר הקטעים
        query = """
        SELECT 
            d.id, 
            d.title,
            d.source,
            d.upload_date,
            COUNT(dc.id) as chunk_count
        FROM 
            documents d
        LEFT JOIN 
            document_chunks dc ON d.id = dc.document_id
        GROUP BY 
            d.id
        ORDER BY 
            d.upload_date DESC
        """
        
        result = session.execute(text(query))
        
        # המרת התוצאות לרשימה של מילונים
        documents = []
        for row in result:
            documents.append({
                'id': row.id,
                'title': row.title,
                'source': row.source,
                'upload_date': row.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
                'chunk_count': row.chunk_count
            })
        
        # הדפסת הטבלה למסך
        print(tabulate(documents, headers='keys', tablefmt='pretty'))
        print(f"\nסה\"כ: {len(documents)} מסמכים")
        
    finally:
        session.close()

def main():
    """פונקציה ראשית"""
    parser = argparse.ArgumentParser(description='כלי לצפייה בהודעות השמורות במסד הנתונים')
    parser.add_argument('--csv', action='store_true', help='ייצוא לקובץ CSV')
    parser.add_argument('--limit', type=int, default=100, help='מספר ההודעות להצגה')
    parser.add_argument('--conversations', action='store_true', help='הצגת שיחות במקום הודעות')
    parser.add_argument('--documents', action='store_true', help='הצגת מסמכים במערכת RAG')
    
    args = parser.parse_args()
    
    if args.conversations:
        view_conversations()
    elif args.documents:
        view_documents()
    else:
        csv_file = 'messages.csv' if args.csv else None
        view_messages(csv_file, args.limit)

if __name__ == '__main__':
    main() 