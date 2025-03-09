"""
בדיקות יחידה למודול query_parser.py
"""
import pytest
from unittest.mock import patch, MagicMock
import re
from datetime import datetime

from src.tools.content.query_parser import (
    extract_entities,
    extract_dates,
    extract_numbers,
    extract_email,
    extract_phone,
    extract_address,
    extract_product_details,
    extract_order_details,
    extract_customer_details,
    identify_specific_intent,
    extract_parameters,
    parse_query
)


def test_extract_entities():
    """בודק את הפונקציה extract_entities"""
    # בדיקה עם שם, אימייל וטלפון
    text = "שמי הוא ישראל ישראלי, האימייל שלי הוא israel@example.com והטלפון שלי הוא 052-1234567"
    entities = extract_entities(text)
    assert entities["names"] == ["ישראל ישראלי"]
    assert entities["emails"] == ["israel@example.com"]
    assert entities["phones"] == ["052-1234567"]
    
    # בדיקה עם שם בלבד
    text = "שמי הוא דוד כהן"
    entities = extract_entities(text)
    assert entities["names"] == ["דוד כהן"]
    assert entities["emails"] == []
    assert entities["phones"] == []
    
    # בדיקה עם אימייל בלבד
    text = "האימייל שלי הוא david@example.co.il"
    entities = extract_entities(text)
    assert entities["names"] == []
    assert entities["emails"] == ["david@example.co.il"]
    assert entities["phones"] == []
    
    # בדיקה עם טלפון בלבד
    text = "הטלפון שלי הוא 03-1234567"
    entities = extract_entities(text)
    assert entities["names"] == []
    assert entities["emails"] == []
    assert entities["phones"] == ["03-1234567"]
    
    # בדיקה ללא ישויות
    text = "אני רוצה לדעת על המוצרים שלכם"
    entities = extract_entities(text)
    assert entities["names"] == []
    assert entities["emails"] == []
    assert entities["phones"] == []


def test_extract_dates():
    """בודק את הפונקציה extract_dates"""
    # בדיקה עם תאריך בפורמט ישראלי
    text = "אני רוצה להזמין את המוצר ל-15/04/2023"
    dates = extract_dates(text)
    assert len(dates) == 1
    assert isinstance(dates[0], datetime)
    assert dates[0].day == 15
    assert dates[0].month == 4
    assert dates[0].year == 2023
    
    # בדיקה עם תאריך בפורמט אמריקאי
    text = "ההזמנה בוצעה ב-04/15/2023"
    dates = extract_dates(text)
    assert len(dates) == 1
    assert dates[0].day == 15
    assert dates[0].month == 4
    assert dates[0].year == 2023
    
    # בדיקה עם תאריך בפורמט מילולי
    text = "אני רוצה לקבל את המוצר ב-15 באפריל 2023"
    dates = extract_dates(text)
    assert len(dates) == 1
    assert dates[0].day == 15
    assert dates[0].month == 4
    assert dates[0].year == 2023
    
    # בדיקה עם מספר תאריכים
    text = "אני רוצה להזמין את המוצר ל-15/04/2023 ולקבל אותו עד 20/04/2023"
    dates = extract_dates(text)
    assert len(dates) == 2
    assert dates[0].day == 15
    assert dates[0].month == 4
    assert dates[0].year == 2023
    assert dates[1].day == 20
    assert dates[1].month == 4
    assert dates[1].year == 2023
    
    # בדיקה ללא תאריכים
    text = "אני רוצה לדעת על המוצרים שלכם"
    dates = extract_dates(text)
    assert dates == []


def test_extract_numbers():
    """בודק את הפונקציה extract_numbers"""
    # בדיקה עם מספרים רגילים
    text = "אני רוצה 5 יחידות מהמוצר מספר 123"
    numbers = extract_numbers(text)
    assert numbers == [5, 123]
    
    # בדיקה עם מספרים עם פסיקים
    text = "המחיר הוא 1,234.56 שקלים"
    numbers = extract_numbers(text)
    assert numbers == [1234.56]
    
    # בדיקה עם מספרים שליליים
    text = "הסכום הוא -50 שקלים"
    numbers = extract_numbers(text)
    assert numbers == [-50]
    
    # בדיקה ללא מספרים
    text = "אני רוצה לדעת על המוצרים שלכם"
    numbers = extract_numbers(text)
    assert numbers == []


def test_extract_email():
    """בודק את הפונקציה extract_email"""
    # בדיקה עם אימייל אחד
    text = "האימייל שלי הוא israel@example.com"
    emails = extract_email(text)
    assert emails == ["israel@example.com"]
    
    # בדיקה עם מספר אימיילים
    text = "האימיילים שלי הם israel@example.com ו-david@example.co.il"
    emails = extract_email(text)
    assert emails == ["israel@example.com", "david@example.co.il"]
    
    # בדיקה עם אימייל עם תווים מיוחדים
    text = "האימייל שלי הוא israel.david_cohen+tag@example-site.co.il"
    emails = extract_email(text)
    assert emails == ["israel.david_cohen+tag@example-site.co.il"]
    
    # בדיקה ללא אימיילים
    text = "אני רוצה לדעת על המוצרים שלכם"
    emails = extract_email(text)
    assert emails == []


def test_extract_phone():
    """בודק את הפונקציה extract_phone"""
    # בדיקה עם מספר טלפון עם מקפים
    text = "הטלפון שלי הוא 052-1234567"
    phones = extract_phone(text)
    assert phones == ["052-1234567"]
    
    # בדיקה עם מספר טלפון עם סוגריים
    text = "הטלפון שלי הוא (052) 1234567"
    phones = extract_phone(text)
    assert phones == ["(052) 1234567"]
    
    # בדיקה עם מספר טלפונים
    text = "הטלפונים שלי הם 052-1234567 ו-03-1234567"
    phones = extract_phone(text)
    assert phones == ["052-1234567", "03-1234567"]
    
    # בדיקה ללא מספרי טלפון
    text = "אני רוצה לדעת על המוצרים שלכם"
    phones = extract_phone(text)
    assert phones == []


def test_extract_address():
    """בודק את הפונקציה extract_address"""
    # בדיקה עם כתובת סטנדרטית
    text = "הכתובת שלי היא רחוב הרצל 10, תל אביב"
    addresses = extract_address(text)
    assert addresses == ["רחוב הרצל 10, תל אביב"]
    
    # בדיקה עם כתובת עם מיקוד
    text = "הכתובת שלי היא רחוב הרצל 10, תל אביב, מיקוד 6120601"
    addresses = extract_address(text)
    assert addresses == ["רחוב הרצל 10, תל אביב, מיקוד 6120601"]
    
    # בדיקה עם מספר כתובות
    text = "הכתובות שלי הן רחוב הרצל 10, תל אביב ורחוב ויצמן 5, ירושלים"
    addresses = extract_address(text)
    assert len(addresses) == 2
    assert "רחוב הרצל 10, תל אביב" in addresses
    assert "רחוב ויצמן 5, ירושלים" in addresses
    
    # בדיקה ללא כתובות
    text = "אני רוצה לדעת על המוצרים שלכם"
    addresses = extract_address(text)
    assert addresses == []


def test_extract_product_details():
    """בודק את הפונקציה extract_product_details"""
    # בדיקה עם פרטי מוצר מלאים
    text = "אני מחפש את המוצר חולצה כחולה במידה L במחיר 100 שקלים"
    product_details = extract_product_details(text)
    assert product_details["name"] == "חולצה כחולה"
    assert product_details["size"] == "L"
    assert product_details["price"] == "100 שקלים"
    
    # בדיקה עם פרטי מוצר חלקיים
    text = "אני מחפש חולצה כחולה"
    product_details = extract_product_details(text)
    assert product_details["name"] == "חולצה כחולה"
    assert product_details["size"] == ""
    assert product_details["price"] == ""
    
    # בדיקה ללא פרטי מוצר
    text = "אני רוצה לדעת על החנות שלכם"
    product_details = extract_product_details(text)
    assert product_details["name"] == ""
    assert product_details["size"] == ""
    assert product_details["price"] == ""


def test_extract_order_details():
    """בודק את הפונקציה extract_order_details"""
    # בדיקה עם פרטי הזמנה מלאים
    text = "אני רוצה לבדוק את ההזמנה מספר 12345 מתאריך 15/04/2023 בסכום 200 שקלים"
    order_details = extract_order_details(text)
    assert order_details["order_number"] == "12345"
    assert isinstance(order_details["order_date"], datetime)
    assert order_details["order_date"].day == 15
    assert order_details["order_date"].month == 4
    assert order_details["order_date"].year == 2023
    assert order_details["total"] == "200 שקלים"
    
    # בדיקה עם פרטי הזמנה חלקיים
    text = "אני רוצה לבדוק את ההזמנה מספר 12345"
    order_details = extract_order_details(text)
    assert order_details["order_number"] == "12345"
    assert order_details["order_date"] is None
    assert order_details["total"] == ""
    
    # בדיקה ללא פרטי הזמנה
    text = "אני רוצה לדעת על החנות שלכם"
    order_details = extract_order_details(text)
    assert order_details["order_number"] == ""
    assert order_details["order_date"] is None
    assert order_details["total"] == ""


def test_extract_customer_details():
    """בודק את הפונקציה extract_customer_details"""
    # בדיקה עם פרטי לקוח מלאים
    text = "שמי הוא ישראל ישראלי, האימייל שלי הוא israel@example.com והטלפון שלי הוא 052-1234567"
    customer_details = extract_customer_details(text)
    assert customer_details["name"] == "ישראל ישראלי"
    assert customer_details["email"] == "israel@example.com"
    assert customer_details["phone"] == "052-1234567"
    
    # בדיקה עם פרטי לקוח חלקיים
    text = "שמי הוא ישראל ישראלי"
    customer_details = extract_customer_details(text)
    assert customer_details["name"] == "ישראל ישראלי"
    assert customer_details["email"] == ""
    assert customer_details["phone"] == ""
    
    # בדיקה ללא פרטי לקוח
    text = "אני רוצה לדעת על החנות שלכם"
    customer_details = extract_customer_details(text)
    assert customer_details["name"] == ""
    assert customer_details["email"] == ""
    assert customer_details["phone"] == ""


def test_identify_specific_intent():
    """בודק את הפונקציה identify_specific_intent"""
    # בדיקה עם כוונת לקוח
    text = "אני רוצה לעדכן את הפרטים שלי"
    intent = identify_specific_intent(text)
    assert intent == "customer"
    
    # בדיקה עם כוונת מוצר
    text = "אני מחפש חולצה כחולה"
    intent = identify_specific_intent(text)
    assert intent == "product"
    
    # בדיקה עם כוונת הזמנה
    text = "מה המצב של ההזמנה שלי מספר 12345"
    intent = identify_specific_intent(text)
    assert intent == "order"
    
    # בדיקה עם טקסט לא ברור
    text = "שלום, מה שלומך?"
    intent = identify_specific_intent(text)
    assert intent == "unclear"


def test_extract_parameters():
    """בודק את הפונקציה extract_parameters"""
    # בדיקה עם פרמטרים של לקוח
    text = "שמי הוא ישראל ישראלי, האימייל שלי הוא israel@example.com"
    params = extract_parameters(text, "customer")
    assert params["name"] == "ישראל ישראלי"
    assert params["email"] == "israel@example.com"
    
    # בדיקה עם פרמטרים של מוצר
    text = "אני מחפש חולצה כחולה במידה L"
    params = extract_parameters(text, "product")
    assert params["name"] == "חולצה כחולה"
    assert params["size"] == "L"
    
    # בדיקה עם פרמטרים של הזמנה
    text = "אני רוצה לבדוק את ההזמנה מספר 12345"
    params = extract_parameters(text, "order")
    assert params["order_number"] == "12345"


@patch('src.tools.content.query_parser.identify_specific_intent')
@patch('src.tools.content.query_parser.extract_parameters')
def test_parse_query(mock_extract_parameters, mock_identify_intent):
    """בודק את הפונקציה parse_query"""
    # הגדרת התנהגות המוקים
    mock_identify_intent.return_value = "customer"
    mock_extract_parameters.return_value = {"name": "ישראל ישראלי", "email": "israel@example.com"}
    
    # בדיקת הפונקציה
    text = "שמי הוא ישראל ישראלי, האימייל שלי הוא israel@example.com"
    result = parse_query(text)
    
    # וידוא שהפונקציות הנכונות נקראו
    mock_identify_intent.assert_called_once_with(text)
    mock_extract_parameters.assert_called_once_with(text, "customer")
    
    # בדיקת התוצאה
    assert result["intent"] == "customer"
    assert result["parameters"] == {"name": "ישראל ישראלי", "email": "israel@example.com"} 