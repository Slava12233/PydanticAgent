"""
מודול לניהול תקשורת עם ה-API של טלגרם
"""
import aiohttp
import json
from datetime import datetime
from typing import Optional, Dict, Any, Union, List
from urllib.parse import urljoin
import logging
from src.utils.logger import setup_logger

# הגדרת לוגר
logger = setup_logger('telegram_bot_api')

class TelegramBotAPI:
    """מחלקה לניהול תקשורת עם ה-API של טלגרם"""
    
    def __init__(self, base_url: str):
        """
        אתחול המחלקה
        
        Args:
            base_url: כתובת הבסיס של ה-API
        """
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """כניסה למנהל ההקשר"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """יציאה ממנהל ההקשר"""
        if self.session:
            await self.session.close()
    
    def _build_url(self, endpoint: str) -> str:
        """
        בניית כתובת URL מלאה
        
        Args:
            endpoint: נקודת הקצה
            
        Returns:
            כתובת URL מלאה
        """
        return urljoin(self.base_url + '/', endpoint.lstrip('/'))
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        שליחת בקשת GET
        
        Args:
            endpoint: נקודת הקצה
            params: פרמטרים לבקשה (אופציונלי)
            
        Returns:
            תשובת השרת
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
        
        url = self._build_url(endpoint)
        logger.debug(f"Sending GET request to {url}")
        
        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Error in GET request to {url}: {str(e)}")
            raise
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        שליחת בקשת POST
        
        Args:
            endpoint: נקודת הקצה
            data: נתונים לשליחה (אופציונלי)
            files: קבצים לשליחה (אופציונלי)
            
        Returns:
            תשובת השרת
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
        
        url = self._build_url(endpoint)
        logger.debug(f"Sending POST request to {url}")
        
        try:
            if files:
                # שליחת טופס עם קבצים
                form_data = aiohttp.FormData()
                
                # הוספת הנתונים לטופס
                if data:
                    for key, value in data.items():
                        form_data.add_field(key, str(value))
                
                # הוספת הקבצים לטופס
                for key, file_data in files.items():
                    form_data.add_field(key, file_data['file'],
                                      filename=file_data.get('filename'),
                                      content_type=file_data.get('content_type'))
                
                async with self.session.post(url, data=form_data) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                # שליחת JSON רגיל
                async with self.session.post(url, json=data) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Error in POST request to {url}: {str(e)}")
            raise
    
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        שליחת בקשת PUT
        
        Args:
            endpoint: נקודת הקצה
            data: נתונים לשליחה
            
        Returns:
            תשובת השרת
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
        
        url = self._build_url(endpoint)
        logger.debug(f"Sending PUT request to {url}")
        
        try:
            async with self.session.put(url, json=data) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Error in PUT request to {url}: {str(e)}")
            raise
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        שליחת בקשת DELETE
        
        Args:
            endpoint: נקודת הקצה
            
        Returns:
            תשובת השרת
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
        
        url = self._build_url(endpoint)
        logger.debug(f"Sending DELETE request to {url}")
        
        try:
            async with self.session.delete(url) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Error in DELETE request to {url}: {str(e)}")
            raise
    
    async def download_file(self, url: str, save_path: str) -> bool:
        """
        הורדת קובץ
        
        Args:
            url: כתובת הקובץ
            save_path: נתיב לשמירת הקובץ
            
        Returns:
            האם ההורדה הצליחה
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
        
        logger.debug(f"Downloading file from {url} to {save_path}")
        
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                
                with open(save_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                
                return True
        except Exception as e:
            logger.error(f"Error downloading file from {url}: {str(e)}")
            return False
    
    async def get_exchange_rates(self, base_currency: str = 'ILS') -> Dict[str, float]:
        """
        קבלת שערי חליפין
        
        Args:
            base_currency: מטבע בסיס (ברירת מחדל: שקל)
            
        Returns:
            מילון שערי חליפין
        """
        try:
            response = await self.get('/exchange-rates', params={'base': base_currency})
            return response.get('rates', {})
        except Exception as e:
            logger.error(f"Error getting exchange rates: {e}")
            return {}
    
    async def get_shipping_rates(
        self,
        origin: str,
        destination: str,
        weight: float
    ) -> List[Dict]:
        """
        קבלת תעריפי משלוח
        
        Args:
            origin: כתובת מוצא
            destination: כתובת יעד
            weight: משקל בק"ג
            
        Returns:
            רשימת אפשרויות משלוח
        """
        try:
            response = await self.post('/shipping/rates', {
                'origin': origin,
                'destination': destination,
                'weight': weight
            })
            return response.get('rates', [])
        except Exception as e:
            logger.error(f"Error getting shipping rates: {e}")
            return []
    
    async def create_shipping_label(
        self,
        shipping_method: str,
        origin: Dict,
        destination: Dict,
        items: List[Dict]
    ) -> Optional[str]:
        """
        יצירת תווית משלוח
        
        Args:
            shipping_method: שיטת משלוח
            origin: פרטי השולח
            destination: פרטי הנמען
            items: פריטים למשלוח
            
        Returns:
            קישור לתווית משלוח אם נוצרה בהצלחה, אחרת None
        """
        try:
            response = await self.post('/shipping/labels', {
                'shipping_method': shipping_method,
                'origin': origin,
                'destination': destination,
                'items': items
            })
            return response.get('label_url')
        except Exception as e:
            logger.error(f"Error creating shipping label: {e}")
            return None
    
    async def get_tracking_info(self, tracking_number: str) -> Optional[Dict]:
        """
        קבלת מידע מעקב משלוח
        
        Args:
            tracking_number: מספר מעקב
            
        Returns:
            מידע מעקב אם נמצא, אחרת None
        """
        try:
            response = await self.get(f'/shipping/tracking/{tracking_number}')
            return response
        except Exception as e:
            logger.error(f"Error getting tracking info: {e}")
            return None
    
    async def process_payment(
        self,
        amount: float,
        currency: str,
        payment_method: str,
        payment_details: Dict
    ) -> Optional[Dict]:
        """
        עיבוד תשלום
        
        Args:
            amount: סכום
            currency: מטבע
            payment_method: שיטת תשלום
            payment_details: פרטי תשלום
            
        Returns:
            פרטי העסקה אם הצליחה, אחרת None
        """
        try:
            response = await self.post('/payments/process', {
                'amount': amount,
                'currency': currency,
                'payment_method': payment_method,
                'payment_details': payment_details
            })
            return response
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            return None
    
    async def verify_address(self, address: str) -> Dict:
        """
        אימות כתובת
        
        Args:
            address: כתובת לאימות
            
        Returns:
            תוצאות אימות
        """
        try:
            response = await self.post('/address/verify', {'address': address})
            return response
        except Exception as e:
            logger.error(f"Error verifying address: {e}")
            return {
                'is_valid': False,
                'error': str(e)
            }
    
    async def get_weather(self, city: str) -> Optional[Dict]:
        """
        קבלת תחזית מזג אוויר
        
        Args:
            city: שם העיר
            
        Returns:
            תחזית מזג אוויר אם נמצאה, אחרת None
        """
        try:
            response = await self.get('/weather', params={'city': city})
            return response
        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            return None
    
    async def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[str]:
        """
        תרגום טקסט
        
        Args:
            text: טקסט לתרגום
            source_lang: שפת מקור
            target_lang: שפת יעד
            
        Returns:
            טקסט מתורגם אם הצליח, אחרת None
        """
        try:
            response = await self.post('/translate', {
                'text': text,
                'source': source_lang,
                'target': target_lang
            })
            return response.get('translated_text')
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            return None
    
    async def send_sms(
        self,
        phone_number: str,
        message: str,
        sender_id: str = None
    ) -> bool:
        """
        שליחת SMS
        
        Args:
            phone_number: מספר טלפון
            message: תוכן ההודעה
            sender_id: מזהה שולח (אופציונלי)
            
        Returns:
            האם ההודעה נשלחה בהצלחה
        """
        try:
            response = await self.post('/sms/send', {
                'phone_number': phone_number,
                'message': message,
                'sender_id': sender_id
            })
            return response.get('success', False)
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False,
        attachments: List[Dict] = None
    ) -> bool:
        """
        שליחת אימייל
        
        Args:
            to_email: כתובת אימייל
            subject: נושא
            body: תוכן
            html: האם התוכן בפורמט HTML
            attachments: קבצים מצורפים (אופציונלי)
            
        Returns:
            האם האימייל נשלח בהצלחה
        """
        try:
            response = await self.post('/email/send', {
                'to': to_email,
                'subject': subject,
                'body': body,
                'html': html,
                'attachments': attachments or []
            })
            return response.get('success', False)
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    async def generate_qr_code(
        self,
        data: str,
        size: int = 200,
        format: str = 'PNG'
    ) -> Optional[bytes]:
        """
        יצירת קוד QR
        
        Args:
            data: מידע לקידוד
            size: גודל בפיקסלים
            format: פורמט תמונה
            
        Returns:
            תמונת הקוד אם נוצרה בהצלחה, אחרת None
        """
        try:
            response = await self.post('/qr/generate', {
                'data': data,
                'size': size,
                'format': format
            })
            return response.get('image')
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None
    
    async def analyze_sentiment(self, text: str) -> Dict:
        """
        ניתוח רגשות בטקסט
        
        Args:
            text: טקסט לניתוח
            
        Returns:
            תוצאות הניתוח
        """
        try:
            response = await self.post('/nlp/sentiment', {'text': text})
            return response
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.0
            }
    
    async def get_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
        metrics: List[str]
    ) -> Dict:
        """
        קבלת סטטיסטיקות
        
        Args:
            start_date: תאריך התחלה
            end_date: תאריך סיום
            metrics: מדדים לחישוב
            
        Returns:
            תוצאות הסטטיסטיקות
        """
        try:
            response = await self.get('/statistics', {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'metrics': ','.join(metrics)
            })
            return response
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {} 