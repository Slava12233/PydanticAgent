#!/usr/bin/env python
"""
סקריפט לצפייה בנתוני טלגרם השמורים במסד הנתונים
"""

import asyncio
import argparse

from src.database.database import Database
from src.services.telegram.message_viewer import MessageViewer

async def main():
    """פונקציה ראשית"""
    parser = argparse.ArgumentParser(description='כלי לצפייה בנתוני טלגרם השמורים במסד הנתונים')
    parser.add_argument('--csv', help='ייצוא הודעות לקובץ CSV')
    parser.add_argument('--limit', type=int, default=100, help='מספר ההודעות להצגה')
    parser.add_argument('--conversations', action='store_true', help='הצגת שיחות במקום הודעות')
    parser.add_argument('--stats', action='store_true', help='הצגת סטטיסטיקות')
    
    args = parser.parse_args()
    
    # יצירת מופע של מסד הנתונים
    db = Database()
    await db.initialize()
    
    # יצירת מופע של הצופה בהודעות
    viewer = MessageViewer(db)
    
    try:
        if args.stats:
            # הצגת סטטיסטיקות
            stats = await viewer.get_statistics()
            print(viewer.format_statistics(stats))
            
        elif args.conversations:
            # הצגת שיחות
            conversations = await viewer.get_conversations()
            print(viewer.format_conversations_table(conversations))
            print(f"\nסה\"כ: {len(conversations)} שיחות")
            
        else:
            # הצגת הודעות
            messages = await viewer.get_messages(args.limit)
            
            if args.csv:
                # ייצוא לקובץ CSV
                await viewer.export_messages_to_csv(args.csv, args.limit)
            else:
                # הצגה למסך
                print(viewer.format_messages_table(messages))
                print(f"\nסה\"כ: {len(messages)} הודעות")
    
    finally:
        await db.close()

if __name__ == '__main__':
    asyncio.run(main()) 