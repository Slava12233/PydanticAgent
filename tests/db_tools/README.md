# כלי בדיקה ותחזוקה של מסד הנתונים

תיקייה זו מכילה כלים לבדיקה ותחזוקה של מסד הנתונים של הבוט.

## קבצים

- `check_table.py` - בדיקת מבנה טבלת users
- `check_databases.py` - בדיקת מסדי הנתונים והסכמות הקיימים
- `check_telegram_bot_db.py` - בדיקת מבנה הטבלאות במסד הנתונים telegram_bot
- `fix_user_role.py` - הוספת עמודת role לטבלת users

## שימוש

כדי להריץ את הכלים, יש להשתמש בפקודות הבאות:

```bash
# בדיקת מבנה טבלת users
python tests/db_tools/check_table.py

# בדיקת מסדי הנתונים והסכמות הקיימים
python tests/db_tools/check_databases.py

# בדיקת מבנה הטבלאות במסד הנתונים telegram_bot
python tests/db_tools/check_telegram_bot_db.py

# הוספת עמודת role לטבלת users
python tests/db_tools/fix_user_role.py
``` 