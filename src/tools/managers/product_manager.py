"""
מודול לניהול מוצרים ב-WooCommerce
"""
import logging
import os
import json
import re
import tempfile
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import httpx
import imghdr

from src.services.woocommerce.api import WooCommerceAPI, CachedWooCommerceAPI
from src.tools.intent.product_intent import extract_product_data, identify_missing_required_fields

logger = logging.getLogger(__name__)

class ProductManager:
    """
    מחלקה לניהול מוצרים ב-WooCommerce
    """
    
    def __init__(self, woocommerce_api, use_cache=True, cache_ttl=300):
        """
        אתחול מנהל המוצרים
        
        Args:
            woocommerce_api: אובייקט API של WooCommerce
            use_cache: האם להשתמש במטמון (ברירת מחדל: True)
            cache_ttl: זמן תפוגה של המטמון בשניות (ברירת מחדל: 5 דקות)
        """
        # בדיקה האם ה-API כבר עטוף במטמון
        if use_cache and not isinstance(woocommerce_api, CachedWooCommerceAPI):
            self.woocommerce = CachedWooCommerceAPI(woocommerce_api, cache_ttl)
            self.using_cache = True
        else:
            self.woocommerce = woocommerce_api
            self.using_cache = isinstance(woocommerce_api, CachedWooCommerceAPI)
        
        # מטמון פנימי לקטגוריות
        self.categories_cache = None
        self.categories_cache_timestamp = None
        self.cache_ttl = cache_ttl
    
    def _is_categories_cache_valid(self):
        """
        בדיקה האם מטמון הקטגוריות תקף
        
        Returns:
            True אם המטמון תקף, False אחרת
        """
        if self.categories_cache is None or self.categories_cache_timestamp is None:
            return False
        
        import time
        current_time = time.time()
        
        return current_time - self.categories_cache_timestamp < self.cache_ttl

    async def create_product(self, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        יצירת מוצר חדש
        
        Args:
            product_data: נתוני המוצר
            
        Returns:
            המוצר שנוצר או None אם היצירה נכשלה
        """
        # וידוא שיש את כל השדות הנדרשים
        missing_fields = identify_missing_required_fields(product_data)
        if missing_fields:
            missing_fields_str = ", ".join(missing_fields)
            logger.error(f"לא ניתן ליצור מוצר: חסרים שדות חובה: {missing_fields_str}")
            return None
        
        # הכנת נתוני המוצר לשליחה ל-API
        api_product_data = self._prepare_product_data_for_api(product_data)
        
        # טיפול בקטגוריות אם קיימות
        if "categories" in api_product_data:
            categories = api_product_data["categories"]
            api_categories = []
            
            for category in categories:
                if "name" in category:
                    # חיפוש או יצירת קטגוריה
                    category_id = await self._find_or_create_category(category["name"])
                    if category_id:
                        api_categories.append({"id": category_id})
                    else:
                        # אם לא הצלחנו למצוא או ליצור, נשתמש בשם
                        api_categories.append({"name": category["name"]})
            
            # עדכון הקטגוריות בנתוני המוצר
            if api_categories:
                api_product_data["categories"] = api_categories
        
        try:
            # שליחת הבקשה ליצירת מוצר
            status_code, response = await self.woocommerce._make_request("POST", "products", data=api_product_data)
            
            if status_code in (200, 201):
                logger.info(f"מוצר נוצר בהצלחה: {response.get('name', 'ללא שם')} (ID: {response.get('id', 'לא ידוע')})")
                return response
            else:
                logger.error(f"שגיאה ביצירת מוצר: {status_code} - {response}")
                return None
                
        except Exception as e:
            logger.error(f"שגיאה לא צפויה ביצירת מוצר: {str(e)}")
            return None
    
    async def _find_or_create_category(self, category_name: str) -> Optional[int]:
        """
        חיפוש קטגוריה קיימת או יצירת קטגוריה חדשה
        
        Args:
            category_name: שם הקטגוריה
            
        Returns:
            מזהה הקטגוריה או None אם לא נמצאה/נוצרה
        """
        try:
            # חיפוש הקטגוריה לפי שם
            status_code, existing_categories = await self.woocommerce._make_request(
                "GET", 
                "products/categories", 
                params={"search": category_name}
            )
            
            if status_code == 200 and existing_categories:
                # חיפוש התאמה מדויקת
                exact_match = next((cat for cat in existing_categories if cat.get("name").lower() == category_name.lower()), None)
                
                if exact_match:
                    # אם נמצאה התאמה מדויקת, נחזיר את ה-ID שלה
                    logger.info(f"נמצאה קטגוריה קיימת: {category_name} (ID: {exact_match['id']})")
                    return exact_match["id"]
            
            # אם לא נמצאה התאמה, ננסה ליצור קטגוריה חדשה
            status_code, new_category = await self.woocommerce._make_request(
                "POST", 
                "products/categories", 
                data={"name": category_name}
            )
            
            if status_code in (200, 201) and new_category:
                logger.info(f"נוצרה קטגוריה חדשה: {category_name} (ID: {new_category['id']})")
                return new_category["id"]
            else:
                logger.warning(f"לא ניתן ליצור קטגוריה חדשה: {category_name}")
                return None
                
        except Exception as e:
            logger.error(f"שגיאה בטיפול בקטגוריה {category_name}: {str(e)}")
            return None
    
    async def update_product(self, product_id: int, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        עדכון מוצר קיים
        
        Args:
            product_id: מזהה המוצר
            product_data: נתוני המוצר לעדכון
            
        Returns:
            המוצר המעודכן או None אם העדכון נכשל
        """
        # הכנת נתוני המוצר לשליחה ל-API
        api_product_data = self._prepare_product_data_for_api(product_data)
        
        # טיפול בקטגוריות אם קיימות
        if "categories" in api_product_data:
            categories = api_product_data["categories"]
            api_categories = []
            
            for category in categories:
                if "name" in category:
                    # חיפוש או יצירת קטגוריה
                    category_id = await self._find_or_create_category(category["name"])
                    if category_id:
                        api_categories.append({"id": category_id})
                    else:
                        # אם לא הצלחנו למצוא או ליצור, נשתמש בשם
                        api_categories.append({"name": category["name"]})
            
            # עדכון הקטגוריות בנתוני המוצר
            if api_categories:
                api_product_data["categories"] = api_categories
        
        try:
            # שליחת הבקשה לעדכון מוצר
            status_code, response = await self.woocommerce._make_request("PUT", f"products/{product_id}", data=api_product_data)
            
            if status_code in (200, 201):
                logger.info(f"מוצר עודכן בהצלחה: {response.get('name', 'ללא שם')} (ID: {response.get('id', 'לא ידוע')})")
                return response
            else:
                logger.error(f"שגיאה בעדכון מוצר: {status_code} - {response}")
                return None
                
        except Exception as e:
            logger.error(f"שגיאה לא צפויה בעדכון מוצר: {str(e)}")
            return None
    
    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        קבלת מוצר לפי מזהה
        
        Args:
            product_id: מזהה המוצר
            
        Returns:
            נתוני המוצר או None אם המוצר לא נמצא
        """
        try:
            # שליחת הבקשה לקבלת מוצר
            status_code, response = await self.woocommerce._make_request("GET", f"products/{product_id}")
            
            if status_code == 200:
                return response
            else:
                logger.error(f"שגיאה בקבלת מוצר: {status_code} - {response}")
                return None
                
        except Exception as e:
            logger.error(f"שגיאה לא צפויה בקבלת מוצר: {str(e)}")
            return None
    
    async def search_products(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        חיפוש מוצרים לפי מונח חיפוש
        
        Args:
            search_term: מונח החיפוש
            limit: מספר התוצאות המקסימלי
            
        Returns:
            רשימה של מוצרים שתואמים את החיפוש
        """
        try:
            # שליחת הבקשה לחיפוש מוצרים
            params = {
                "search": search_term,
                "per_page": limit
            }
            status_code, response = await self.woocommerce._make_request("GET", "products", params=params)
            
            if status_code == 200 and isinstance(response, list):
                return response
            else:
                logger.error(f"שגיאה בחיפוש מוצרים: {status_code} - {response}")
                return []
                
        except Exception as e:
            logger.error(f"שגיאה לא צפויה בחיפוש מוצרים: {str(e)}")
            return []
    
    async def upload_product_image(self, image_path: str, alt_text: str = "") -> Optional[Dict[str, Any]]:
        """
        העלאת תמונת מוצר
        
        Args:
            image_path: נתיב לקובץ התמונה או URL
            alt_text: טקסט חלופי לתמונה
            
        Returns:
            פרטי התמונה שהועלתה או None אם ההעלאה נכשלה
        """
        try:
            # בדיקה אם מדובר ב-URL או בקובץ מקומי
            if image_path.startswith(("http://", "https://")):
                # אם זה URL, נשתמש בו ישירות
                image_url = image_path
                logger.info(f"שימוש בתמונה מ-URL: {image_url}")
                
                # בדיקת תקינות ה-URL באמצעות בקשת HEAD
                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.head(image_url, timeout=10.0)
                        if response.status_code != 200:
                            logger.error(f"URL התמונה אינו תקין: {image_url}, קוד תגובה: {response.status_code}")
                            return None
                        
                        # בדיקה שהקובץ הוא אכן תמונה
                        content_type = response.headers.get("content-type", "")
                        if not content_type.startswith("image/"):
                            logger.error(f"הקובץ ב-URL אינו תמונה: {image_url}, סוג תוכן: {content_type}")
                            return None
                    except Exception as e:
                        logger.error(f"שגיאה בבדיקת URL התמונה: {str(e)}")
                        return None
                
                # יצירת נתוני תמונה עם ה-URL
                image_data = {
                    "src": image_url,
                    "alt": alt_text
                }
                
                logger.info(f"תמונה מ-URL נוספה בהצלחה: {image_url}")
                return image_data
            else:
                # בדיקה שהקובץ קיים
                if not os.path.exists(image_path):
                    logger.error(f"קובץ התמונה לא קיים: {image_path}")
                    return None
                
                # בדיקת סוג הקובץ
                image_type = imghdr.what(image_path)
                if not image_type:
                    logger.error(f"הקובץ אינו תמונה תקינה: {image_path}")
                    return None
                
                # העלאת התמונה באמצעות ה-API של WooCommerce
                # כאן יש לממש את הקוד להעלאת תמונה לשרת WooCommerce
                # לדוגמה, שימוש ב-API של WordPress להעלאת מדיה
                
                # לצורך הדוגמה, נחזיר מבנה נתונים מדומה
                # במימוש אמיתי, יש להחליף זאת בקריאה אמיתית ל-API
                image_data = {
                    "id": 123,
                    "src": f"https://example.com/wp-content/uploads/{os.path.basename(image_path)}",
                    "alt": alt_text
                }
                
                logger.info(f"תמונה הועלתה בהצלחה: {image_data['src']}")
                return image_data
                
        except Exception as e:
            logger.error(f"שגיאה לא צפויה בהעלאת תמונה: {str(e)}")
            return None
    
    def _prepare_product_data_for_api(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        הכנת נתוני המוצר לשליחה ל-API
        
        Args:
            product_data: נתוני המוצר המקוריים
            
        Returns:
            נתוני המוצר מוכנים לשליחה ל-API
        """
        api_data = {}
        
        # העתקת שדות בסיסיים
        basic_fields = ["name", "description", "short_description", "sku", "regular_price", 
                        "sale_price", "status", "featured", "catalog_visibility", 
                        "virtual", "downloadable", "tax_status", "tax_class"]
        
        for field in basic_fields:
            if field in product_data:
                api_data[field] = product_data[field]
        
        # טיפול במחיר אם קיים
        if "price" in product_data and "regular_price" not in product_data:
            api_data["regular_price"] = str(product_data["price"])
        
        # המרת מחירים למחרוזות (נדרש ע"י ה-API)
        price_fields = ["regular_price", "sale_price"]
        for field in price_fields:
            if field in api_data:
                api_data[field] = str(api_data[field])
        
        # טיפול בסוג המוצר
        if "type" in product_data:
            api_data["type"] = product_data["type"]
        else:
            # ברירת מחדל: מוצר פשוט
            api_data["type"] = "simple"
        
        # טיפול בניהול מלאי
        if "stock_quantity" in product_data:
            api_data["manage_stock"] = True
            api_data["stock_quantity"] = product_data["stock_quantity"]
            
            # קביעת סטטוס מלאי אוטומטית
            if product_data["stock_quantity"] > 0:
                api_data["stock_status"] = "instock"
            else:
                api_data["stock_status"] = "outofstock"
        elif "stock_status" in product_data:
            api_data["stock_status"] = product_data["stock_status"]
        
        # טיפול בקטגוריות - נשתמש בשמות בלבד ונטפל בהם בצורה נכונה בפונקציית create_product
        if "categories" in product_data:
            categories = product_data["categories"]
            api_categories = []
            
            # בדיקה אם יש קטגוריות קיימות
            if isinstance(categories, list):
                # אם יש רשימת קטגוריות, נשתמש בהן
                for category_name in categories:
                    api_categories.append({"name": category_name})
            elif isinstance(categories, str):
                # אם זו מחרוזת, נפצל אותה לרשימה
                category_names = [cat.strip() for cat in categories.split(",") if cat.strip()]
                for category_name in category_names:
                    api_categories.append({"name": category_name})
            
            # שמירת הקטגוריות המוכנות
            if api_categories:
                api_data["categories"] = api_categories
        
        # טיפול בתגיות
        if "tags" in product_data:
            tags = product_data["tags"]
            if isinstance(tags, list):
                api_data["tags"] = [{"name": tag} for tag in tags]
            elif isinstance(tags, str):
                api_data["tags"] = [{"name": tag.strip()} for tag in tags.split(",") if tag.strip()]
        
        # טיפול בתמונות
        if "images" in product_data:
            images = product_data["images"]
            api_images = []
            
            if isinstance(images, list):
                for image in images:
                    if isinstance(image, dict):
                        # אם זה כבר מילון עם מבנה נכון, נוסיף אותו כמו שהוא
                        if "src" in image:
                            api_images.append(image)
                    elif isinstance(image, str):
                        # אם זו מחרוזת, נבדוק אם זה URL או נתיב מקומי
                        if image.startswith(("http://", "https://")):
                            api_images.append({"src": image})
                        else:
                            # כאן יש לטפל בהעלאת תמונות מקומיות
                            # במימוש אמיתי, יש להעלות את התמונה ולקבל URL
                            logger.warning(f"נתיב תמונה מקומי לא נתמך עדיין: {image}")
            elif isinstance(images, str):
                # אם זו מחרוזת בודדת, נבדוק אם זה URL או נתיב מקומי
                if images.startswith(("http://", "https://")):
                    api_images.append({"src": images})
                else:
                    # כאן יש לטפל בהעלאת תמונות מקומיות
                    logger.warning(f"נתיב תמונה מקומי לא נתמך עדיין: {images}")
            
            # שמירת התמונות המוכנות
            if api_images:
                api_data["images"] = api_images
        
        # טיפול בתיאורי תמונות
        if "image_descriptions" in product_data and api_data.get("images"):
            image_descriptions = product_data["image_descriptions"]
            
            # אם יש תיאורי תמונות, נוסיף אותם לתמונות המתאימות
            if isinstance(image_descriptions, dict):
                for i, image in enumerate(api_data["images"]):
                    image_url = image.get("src", "")
                    if image_url in image_descriptions:
                        api_data["images"][i]["alt"] = image_descriptions[image_url]
        
        # טיפול במאפיינים (attributes)
        if "attributes" in product_data:
            attributes = product_data["attributes"]
            if isinstance(attributes, dict):
                api_attributes = []
                for name, options in attributes.items():
                    if isinstance(options, str):
                        options = [opt.strip() for opt in options.split(",") if opt.strip()]
                    api_attributes.append({
                        "name": name,
                        "options": options,
                        "visible": True,
                        "variation": True if product_data.get("type") == "variable" else False
                    })
                api_data["attributes"] = api_attributes
            elif isinstance(attributes, str):
                # אם attributes הוא מחרוזת, ננסה לפרסר אותו כמאפיין בודד
                api_data["attributes"] = [{
                    "name": "מאפיינים",
                    "options": [attributes],
                    "visible": True,
                    "variation": False
                }]
        
        # טיפול במידות
        if "dimensions" in product_data:
            dimensions = product_data["dimensions"]
            if isinstance(dimensions, dict):
                api_data["dimensions"] = dimensions
            elif isinstance(dimensions, str):
                # ניסיון לפרסר מחרוזת מידות (לדוגמה: "10x20x30")
                match = re.match(r"(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)", dimensions)
                if match:
                    api_data["dimensions"] = {
                        "length": match.group(1),
                        "width": match.group(2),
                        "height": match.group(3)
                    }
        
        # טיפול במשקל
        if "weight" in product_data:
            api_data["weight"] = str(product_data["weight"])
        
        return api_data

    async def get_categories(self):
        """
        קבלת כל הקטגוריות מהחנות
        
        Returns:
            רשימת קטגוריות
        """
        # בדיקה אם יש מטמון תקף
        if self._is_categories_cache_valid():
            return self.categories_cache
        
        try:
            # קבלת כל הקטגוריות
            response = self.woocommerce.get("products/categories", params={"per_page": 100})
            
            # בדיקת תקינות התשובה
            if response.status_code != 200:
                raise Exception(f"שגיאה בקבלת קטגוריות: {response.status_code} - {response.text}")
            
            # המרת התשובה ל-JSON
            categories = response.json()
            
            # שמירה במטמון
            import time
            self.categories_cache = categories
            self.categories_cache_timestamp = time.time()
            
            return categories
        except Exception as e:
            raise Exception(f"שגיאה בקבלת קטגוריות: {str(e)}")

    async def get_products(self, per_page=20, page=1, **kwargs):
        """
        קבלת מוצרים מהחנות
        
        Args:
            per_page: מספר מוצרים בכל עמוד
            page: מספר העמוד
            **kwargs: פרמטרים נוספים לסינון
        
        Returns:
            רשימת מוצרים
        """
        try:
            # הכנת פרמטרים לבקשה
            params = {
                "per_page": per_page,
                "page": page,
                **kwargs
            }
            
            # קבלת מוצרים
            response = self.woocommerce.get("products", params=params)
            
            # בדיקת תקינות התשובה
            if response.status_code != 200:
                raise Exception(f"שגיאה בקבלת מוצרים: {response.status_code} - {response.text}")
            
            # המרת התשובה ל-JSON
            products = response.json()
            
            return products
        except Exception as e:
            raise Exception(f"שגיאה בקבלת מוצרים: {str(e)}")

async def create_product_from_text(store_url: str, consumer_key: str, consumer_secret: str, text: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    יצירת מוצר מטקסט חופשי
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        text: טקסט חופשי עם פרטי המוצר
        
    Returns:
        טאפל עם: הצלחה (בוליאני), הודעה (מחרוזת), נתוני המוצר שנוצר (מילון או None)
    """
    try:
        # חילוץ פרטי המוצר מהטקסט
        product_data = extract_product_data(text)
        
        # בדיקה אם יש מספיק פרטים
        missing_fields = identify_missing_required_fields(product_data)
        if missing_fields:
            missing_fields_str = ", ".join(missing_fields)
            return False, f"לא ניתן ליצור מוצר: חסרים שדות חובה: {missing_fields_str}", None
        
        # יצירת מופע API
        api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # בדיקת חיבור לחנות
        connection_test = await api.test_connection()
        if not connection_test:
            return False, "לא ניתן להתחבר לחנות WooCommerce. אנא בדוק את פרטי החיבור.", None
        
        # יצירת מנהל מוצרים
        product_manager = ProductManager(api)
        
        # יצירת המוצר
        created_product = await product_manager.create_product(product_data)
        
        if created_product:
            product_name = created_product.get("name", "ללא שם")
            product_id = created_product.get("id", "לא ידוע")
            return True, f"המוצר '{product_name}' (ID: {product_id}) נוצר בהצלחה!", created_product
        else:
            return False, "לא ניתן ליצור את המוצר. אנא נסה שוב או בדוק את הלוגים לפרטים נוספים.", None
            
    except Exception as e:
        logger.error(f"שגיאה לא צפויה ביצירת מוצר מטקסט: {str(e)}")
        return False, f"אירעה שגיאה לא צפויה: {str(e)}", None

async def update_product_from_text(store_url: str, consumer_key: str, consumer_secret: str, product_id: int, text: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    עדכון מוצר מטקסט חופשי
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        product_id: מזהה המוצר לעדכון
        text: טקסט חופשי עם פרטי המוצר לעדכון
        
    Returns:
        טאפל עם: הצלחה (בוליאני), הודעה (מחרוזת), נתוני המוצר המעודכן (מילון או None)
    """
    try:
        # חילוץ פרטי המוצר מהטקסט
        product_data = extract_product_data(text)
        
        # בדיקה אם יש פרטים לעדכון
        if not product_data:
            return False, "לא נמצאו פרטים לעדכון המוצר.", None
        
        # יצירת מופע API
        api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # בדיקת חיבור לחנות
        connection_test = await api.test_connection()
        if not connection_test:
            return False, "לא ניתן להתחבר לחנות WooCommerce. אנא בדוק את פרטי החיבור.", None
        
        # יצירת מנהל מוצרים
        product_manager = ProductManager(api)
        
        # קבלת המוצר הקיים
        existing_product = await product_manager.get_product(product_id)
        if not existing_product:
            return False, f"לא נמצא מוצר עם מזהה {product_id}.", None
        
        # עדכון המוצר
        updated_product = await product_manager.update_product(product_id, product_data)
        
        if updated_product:
            product_name = updated_product.get("name", "ללא שם")
            return True, f"המוצר '{product_name}' (ID: {product_id}) עודכן בהצלחה!", updated_product
        else:
            return False, "לא ניתן לעדכן את המוצר. אנא נסה שוב או בדוק את הלוגים לפרטים נוספים.", None
            
    except Exception as e:
        logger.error(f"שגיאה לא צפויה בעדכון מוצר מטקסט: {str(e)}")
        return False, f"אירעה שגיאה לא צפויה: {str(e)}", None

async def search_products_by_text(store_url: str, consumer_key: str, consumer_secret: str, search_text: str, limit: int = 10) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    חיפוש מוצרים לפי טקסט
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        search_text: טקסט לחיפוש
        limit: מספר התוצאות המקסימלי
        
    Returns:
        טאפל עם: הצלחה (בוליאני), הודעה (מחרוזת), רשימת מוצרים
    """
    try:
        # יצירת מופע API
        api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # בדיקת חיבור לחנות
        connection_test = await api.test_connection()
        if not connection_test:
            return False, "לא ניתן להתחבר לחנות WooCommerce. אנא בדוק את פרטי החיבור.", []
        
        # יצירת מנהל מוצרים
        product_manager = ProductManager(api)
        
        # חיפוש מוצרים
        products = await product_manager.search_products(search_text, limit)
        
        if products:
            return True, f"נמצאו {len(products)} מוצרים התואמים לחיפוש '{search_text}'.", products
        else:
            return False, f"לא נמצאו מוצרים התואמים לחיפוש '{search_text}'.", []
            
    except Exception as e:
        logger.error(f"שגיאה לא צפויה בחיפוש מוצרים: {str(e)}")
        return False, f"אירעה שגיאה לא צפויה: {str(e)}", []

def format_product_for_display(product: Dict[str, Any]) -> str:
    """
    פורמט מוצר להצגה למשתמש
    
    Args:
        product: נתוני המוצר
        
    Returns:
        מחרוזת מפורמטת עם פרטי המוצר
    """
    if not product:
        return "אין פרטי מוצר להצגה."
    
    # שדות בסיסיים
    product_id = product.get("id", "לא ידוע")
    name = product.get("name", "ללא שם")
    status = product.get("status", "")
    status_emoji = "🟢" if status == "publish" else "🟠" if status == "draft" else "⚪"
    status_text = "פורסם" if status == "publish" else "טיוטה" if status == "draft" else status
    
    # מחירים
    regular_price = product.get("regular_price", "")
    sale_price = product.get("sale_price", "")
    
    if sale_price and float(sale_price) > 0:
        discount_percent = ""
        try:
            if regular_price and float(regular_price) > 0:
                discount = (float(regular_price) - float(sale_price)) / float(regular_price) * 100
                discount_percent = f" (הנחה של {discount:.1f}%)"
        except (ValueError, TypeError):
            pass
        
        price_html = f"💰 מחיר רגיל: {regular_price}₪\n💸 מחיר מבצע: {sale_price}₪{discount_percent}"
    else:
        price_html = f"💰 מחיר: {regular_price}₪"
    
    # מלאי
    stock_status = product.get("stock_status", "")
    stock_quantity = product.get("stock_quantity", "")
    
    if stock_status == "instock":
        stock_emoji = "✅"
        stock_text = "במלאי"
        if stock_quantity:
            stock_text = f"במלאי ({stock_quantity} יחידות)"
    elif stock_status == "outofstock":
        stock_emoji = "❌"
        stock_text = "אזל מהמלאי"
    elif stock_status == "onbackorder":
        stock_emoji = "⏳"
        stock_text = "ניתן להזמין מראש"
    else:
        stock_emoji = "❓"
        stock_text = "מצב מלאי לא ידוע"
    
    stock_html = f"{stock_emoji} {stock_text}"
    
    # קטגוריות
    categories = product.get("categories", [])
    categories_html = ""
    if categories:
        category_names = [cat.get("name", "") for cat in categories]
        categories_html = f"🗂️ קטגוריות: {', '.join(category_names)}"
    
    # תגיות
    tags = product.get("tags", [])
    tags_html = ""
    if tags:
        tag_names = [tag.get("name", "") for tag in tags]
        tags_html = f"🏷️ תגיות: {', '.join(tag_names)}"
    
    # תמונות
    images = product.get("images", [])
    images_html = ""
    if images and len(images) > 0:
        main_image = images[0].get("src", "")
        if len(images) == 1:
            images_html = f"🖼️ תמונה: {main_image}"
        else:
            images_html = f"🖼️ תמונות: {len(images)} תמונות (ראשית: {main_image})"
    
    # מידות ומשקל
    dimensions_html = ""
    weight = product.get("weight", "")
    dimensions = product.get("dimensions", {})
    
    if weight:
        dimensions_html = f"⚖️ משקל: {weight} ק\"ג"
    
    if dimensions and isinstance(dimensions, dict):
        length = dimensions.get("length", "")
        width = dimensions.get("width", "")
        height = dimensions.get("height", "")
        
        if length and width and height:
            if dimensions_html:
                dimensions_html += "\n"
            dimensions_html += f"📏 מידות: {length} × {width} × {height} ס\"מ"
    
    # בניית המחרוזת המלאה
    product_html = f"""
🛍️ *{name}* (מזהה: {product_id})
{status_emoji} סטטוס: {status_text}
{price_html}
📦 {stock_html}
"""
    
    # הוספת תיאור אם קיים
    description = product.get("description", "")
    short_description = product.get("short_description", "")
    
    if short_description:
        # הסרת תגיות HTML
        short_description = re.sub(r'<[^>]+>', '', short_description)
        product_html += f"📝 תיאור קצר: {short_description}\n"
    
    if description:
        # הסרת תגיות HTML
        description = re.sub(r'<[^>]+>', '', description)
        # קיצור התיאור אם הוא ארוך מדי
        if len(description) > 200:
            description = description[:197] + "..."
        
        if not short_description:
            product_html += f"📝 תיאור: {description}\n"
        elif description != short_description:
            product_html += f"📄 תיאור מלא: {description}\n"
    
    # הוספת פרטים נוספים אם קיימים
    if categories_html:
        product_html += f"{categories_html}\n"
    
    if tags_html:
        product_html += f"{tags_html}\n"
    
    if dimensions_html:
        product_html += f"{dimensions_html}\n"
    
    if images_html:
        product_html += f"{images_html}\n"
    
    # הוספת קישור למוצר אם קיים
    permalink = product.get("permalink", "")
    if permalink:
        product_html += f"\n🔗 קישור למוצר: {permalink}"
    
    return product_html
