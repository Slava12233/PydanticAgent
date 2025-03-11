"""
מודול לניהול מדיה ב-WordPress/WooCommerce
"""
import os
import base64
import logging
import time
import mimetypes
from datetime import datetime
from io import BytesIO
from typing import Dict, Any, Optional

import requests
from PIL import Image
from woocommerce import API

# יצירת לוגר
logger = logging.getLogger(__name__)

class MediaHandler:
    """
    מחלקה לניהול מדיה ב-WordPress/WooCommerce
    """
    
    def __init__(
        self, 
        wp_url: str, 
        wp_user: str, 
        wp_password: str,
        consumer_key: str = None,
        consumer_secret: str = None
    ):
        """
        אתחול המחלקה
        
        Args:
            wp_url: כתובת האתר
            wp_user: שם משתמש ב-WordPress
            wp_password: סיסמה או סיסמת אפליקציה ב-WordPress
            consumer_key: מפתח צרכן של WooCommerce (אופציונלי)
            consumer_secret: סוד צרכן של WooCommerce (אופציונלי)
        """
        # וידוא שה-URL מתחיל בפרוטוקול
        if not wp_url.startswith('http://') and not wp_url.startswith('https://'):
            wp_url = 'https://' + wp_url
            
        self.wp_url = wp_url.rstrip('/')
        self.wp_user = wp_user
        self.wp_password = wp_password
        
        # אם סופקו מפתחות WooCommerce, נשמור אותם
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        
        # יצירת מופע של ספריית WooCommerce אם סופקו מפתחות
        self.wcapi = None
        if consumer_key and consumer_secret:
            self.wcapi = API(
                url=self.wp_url,
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
                version="wc/v3",
                timeout=30
            )
        
        # הגדרת כותרות HTTP בסיסיות
        self.headers = {
            "Accept": "application/json"
        }
        
        # הוספת אימות בסיסי
        auth_string = f"{self.wp_user}:{self.wp_password}"
        auth_header = base64.b64encode(auth_string.encode()).decode()
        self.headers["Authorization"] = f"Basic {auth_header}"
    
    def _retry_operation(self, operation, max_retries=3, delay=1):
        """
        מבצע פעולה עם ניסיונות חוזרים במקרה של כישלון
        
        Args:
            operation: פונקציה לביצוע
            max_retries: מספר ניסיונות מקסימלי
            delay: זמן המתנה בין ניסיונות (בשניות)
            
        Returns:
            תוצאת הפעולה
            
        Raises:
            Exception: אם כל הניסיונות נכשלו
        """
        retries = 0
        last_error = None
        
        while retries < max_retries:
            try:
                return operation()
            except Exception as e:
                retries += 1
                last_error = e
                wait_time = delay * (2 ** (retries - 1))  # exponential backoff
                
                logger.warning(
                    f"שגיאה בפעולה (ניסיון {retries}/{max_retries}): {str(e)}. "
                    f"ממתין {wait_time} שניות לפני ניסיון חוזר."
                )
                
                time.sleep(wait_time)
        
        # אם הגענו לכאן, כל הניסיונות נכשלו
        logger.error(f"כל הניסיונות נכשלו. שגיאה אחרונה: {str(last_error)}")
        raise last_error
    
    def optimize_image(self, image_data: bytes, max_size: tuple = (800, 800)) -> bytes:
        """
        אופטימיזציה של תמונה
        
        Args:
            image_data: נתוני התמונה כ-bytes
            max_size: גודל מקסימלי (רוחב, גובה)
            
        Returns:
            bytes: נתוני התמונה המאופטמת
        """
        try:
            # פתיחת התמונה
            img = Image.open(BytesIO(image_data))
            
            # שינוי גודל אם צריך
            if img.width > max_size[0] or img.height > max_size[1]:
                img.thumbnail(max_size, Image.LANCZOS)
            
            # שמירה בפורמט JPEG עם איכות טובה
            output = BytesIO()
            
            # שמירה בפורמט המקורי או JPEG אם לא ניתן
            if img.format == 'PNG' and img.mode == 'RGBA':
                img.save(output, format='PNG')
            else:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(output, format='JPEG', quality=85, optimize=True)
            
            output.seek(0)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"שגיאה באופטימיזציה של תמונה: {str(e)}")
            # אם יש שגיאה, נחזיר את התמונה המקורית
            return image_data
    
    def save_temp_image(self, image_data: bytes, prefix: str = "temp") -> str:
        """
        שמירת תמונה זמנית לדיסק
        
        Args:
            image_data: נתוני התמונה כ-bytes
            prefix: קידומת לשם הקובץ
            
        Returns:
            str: נתיב הקובץ שנשמר
        """
        try:
            # יצירת תיקייה זמנית אם לא קיימת
            temp_dir = os.path.join(os.getcwd(), "temp_images")
            os.makedirs(temp_dir, exist_ok=True)
            
            # קביעת סיומת הקובץ לפי סוג התמונה
            img = Image.open(BytesIO(image_data))
            extension = img.format.lower() if img.format else "jpg"
            
            # יצירת שם קובץ ייחודי
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{prefix}_{timestamp}.{extension}"
            file_path = os.path.join(temp_dir, filename)
            
            # שמירת הקובץ
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            logger.debug(f"תמונה נשמרה בהצלחה: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"שגיאה בשמירת תמונה זמנית: {str(e)}")
            raise
    
    def upload_media(self, file_path: str) -> Dict[str, Any]:
        """
        העלאת קובץ מדיה ל-WordPress
        
        Args:
            file_path: נתיב הקובץ להעלאה
            
        Returns:
            Dict[str, Any]: פרטי המדיה שהועלתה
        """
        try:
            # בדיקה שהקובץ קיים
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"הקובץ לא נמצא: {file_path}")
            
            # קביעת סוג MIME לפי סיומת הקובץ
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "application/octet-stream"
            
            # קריאת הקובץ
            with open(file_path, "rb") as f:
                file_data = f.read()
            
            # שם הקובץ
            filename = os.path.basename(file_path)
            
            # הגדרת כותרות להעלאה
            upload_headers = self.headers.copy()
            upload_headers["Content-Type"] = mime_type
            upload_headers["Content-Disposition"] = f'attachment; filename="{filename}"'
            
            # פונקציה לביצוע בקשת ההעלאה
            def upload_request():
                response = requests.post(
                    f"{self.wp_url}/wp-json/wp/v2/media",
                    headers=upload_headers,
                    data=file_data,
                    timeout=60  # זמן ארוך יותר להעלאות
                )
                
                if response.status_code not in (200, 201):
                    error_msg = f"שגיאה בהעלאת מדיה: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                return response.json()
            
            # ביצוע הבקשה עם ניסיונות חוזרים
            result = self._retry_operation(upload_request)
            
            logger.info(f"מדיה הועלתה בהצלחה: {result.get('id')} - {result.get('source_url')}")
            return result
            
        except Exception as e:
            logger.error(f"שגיאה בהעלאת מדיה: {str(e)}")
            raise
    
    def upload_image_from_bytes(self, image_data: bytes, prefix: str = "upload") -> Dict[str, Any]:
        """
        העלאת תמונה מנתוני bytes
        
        Args:
            image_data: נתוני התמונה כ-bytes
            prefix: קידומת לשם הקובץ הזמני
            
        Returns:
            Dict[str, Any]: פרטי המדיה שהועלתה
        """
        try:
            # אופטימיזציה של התמונה
            optimized_image = self.optimize_image(image_data)
            
            # שמירה זמנית
            temp_file = self.save_temp_image(optimized_image, prefix)
            
            try:
                # העלאה
                result = self.upload_media(temp_file)
                
                return result
            finally:
                # ניקוי הקובץ הזמני
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    logger.warning(f"שגיאה בניקוי קובץ זמני: {str(e)}")
        
        except Exception as e:
            logger.error(f"שגיאה בהעלאת תמונה מ-bytes: {str(e)}")
            raise
    
    def upload_image_from_url(self, image_url: str, prefix: str = "url_upload") -> Dict[str, Any]:
        """
        העלאת תמונה מ-URL
        
        Args:
            image_url: כתובת התמונה
            prefix: קידומת לשם הקובץ הזמני
            
        Returns:
            Dict[str, Any]: פרטי המדיה שהועלתה
        """
        try:
            # הורדת התמונה
            response = requests.get(image_url, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"שגיאה בהורדת תמונה מ-URL: {response.status_code}")
            
            # העלאת התמונה מהנתונים שהורדו
            return self.upload_image_from_bytes(response.content, prefix)
            
        except Exception as e:
            logger.error(f"שגיאה בהעלאת תמונה מ-URL: {str(e)}")
            raise
    
    def set_product_image(self, product_id: int, image_data: bytes = None, image_url: str = None) -> Dict[str, Any]:
        """
        הגדרת תמונת מוצר
        
        Args:
            product_id: מזהה המוצר
            image_data: נתוני התמונה כ-bytes (אופציונלי)
            image_url: כתובת התמונה (אופציונלי)
            
        Returns:
            Dict[str, Any]: פרטי המוצר המעודכן
            
        Raises:
            ValueError: אם לא סופקו נתוני תמונה או URL
        """
        if not image_data and not image_url:
            raise ValueError("חייב לספק נתוני תמונה או URL")
        
        if not self.wcapi:
            raise ValueError("נדרשים מפתחות WooCommerce API לעדכון מוצר")
        
        try:
            # העלאת התמונה
            if image_data:
                media_result = self.upload_image_from_bytes(image_data, f"product_{product_id}")
            else:
                media_result = self.upload_image_from_url(image_url, f"product_{product_id}")
            
            # קבלת URL של התמונה שהועלתה
            image_src = media_result.get("source_url")
            
            if not image_src:
                raise ValueError("לא ניתן לקבל את כתובת התמונה שהועלתה")
            
            # עדכון המוצר עם התמונה החדשה
            data = {
                "images": [
                    {
                        "src": image_src,
                        "position": 0
                    }
                ]
            }
            
            response = self.wcapi.put(f"products/{product_id}", data)
            
            if response.status_code not in (200, 201):
                raise Exception(f"שגיאה בעדכון תמונת מוצר: {response.status_code} - {response.text}")
            
            logger.info(f"תמונת מוצר עודכנה בהצלחה: {product_id}")
            return response.json()
            
        except Exception as e:
            logger.error(f"שגיאה בהגדרת תמונת מוצר: {str(e)}")
            raise 