"""
מודול לניתוח מכירות ודוחות בחנות WooCommerce.
מאפשר ניתוח מגמות מכירות, זיהוי מוצרים פופולריים, ניתוח התנהגות לקוחות ויצירת דוחות.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta, date
import calendar
import statistics
from collections import Counter, defaultdict

from src.tools.woocommerce_tools import get_woocommerce_api
from src.services.woocommerce.api import WooCommerceAPI, CachedWooCommerceAPI

logger = logging.getLogger(__name__)

class SalesAnalyzer:
    """מנהל ניתוח מכירות המאפשר ניתוח נתוני מכירות וייצור דוחות בחנות WooCommerce."""

    def __init__(self, woocommerce_api=None, use_cache=True, cache_ttl=300):
        """
        אתחול מנהל ניתוח המכירות.
        
        Args:
            woocommerce_api: אובייקט API של WooCommerce (אופציונלי)
            use_cache: האם להשתמש במטמון (ברירת מחדל: True)
            cache_ttl: זמן תפוגה של המטמון בשניות (ברירת מחדל: 5 דקות)
        """
        if woocommerce_api is None:
            woocommerce_api = get_woocommerce_api()
        
        # בדיקה האם ה-API כבר עטוף במטמון
        if use_cache and not isinstance(woocommerce_api, CachedWooCommerceAPI):
            self.api = CachedWooCommerceAPI(woocommerce_api, cache_ttl)
            self.using_cache = True
        else:
            self.api = woocommerce_api
            self.using_cache = isinstance(woocommerce_api, CachedWooCommerceAPI)
        
        self.cache_ttl = cache_ttl

    async def get_sales_by_period(self, period: str = 'month', start_date: Optional[datetime] = None, 
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        קבלת נתוני מכירות לפי תקופה.
        
        Args:
            period: התקופה לניתוח ('day', 'week', 'month', 'year')
            start_date: תאריך התחלה (אופציונלי, ברירת מחדל: לפי התקופה)
            end_date: תאריך סיום (אופציונלי, ברירת מחדל: היום)
            
        Returns:
            מילון עם נתוני המכירות לפי תקופה
        """
        # הגדרת תאריכי ברירת מחדל
        if end_date is None:
            end_date = datetime.now()
        
        if start_date is None:
            if period == 'day':
                # 30 ימים אחורה
                start_date = end_date - timedelta(days=30)
            elif period == 'week':
                # 12 שבועות אחורה
                start_date = end_date - timedelta(weeks=12)
            elif period == 'month':
                # 12 חודשים אחורה
                if end_date.month <= 12 and end_date.month > 11:  # חודש 12
                    start_date = end_date.replace(year=end_date.year - 1, month=1)
                elif end_date.month <= 11 and end_date.month > 0:  # חודשים 1-11
                    new_month = end_date.month + 1
                    start_date = end_date.replace(year=end_date.year - 1, month=new_month)
                else:
                    # במקרה של ערך חודש לא תקין, נחזור 12 חודשים אחורה
                    start_date = end_date - timedelta(days=365)
            elif period == 'year':
                # 5 שנים אחורה
                start_date = end_date.replace(year=end_date.year - 5)
            else:
                # ברירת מחדל: 30 ימים אחורה
                start_date = end_date - timedelta(days=30)
        
        # קבלת כל ההזמנות בטווח התאריכים
        params = {
            'after': start_date.isoformat(),
            'before': end_date.isoformat(),
            'per_page': 100,  # מקסימום הזמנות לבקשה
            'status': ['completed', 'processing', 'on-hold']  # סטטוסים רלוונטיים למכירות
        }
        
        try:
            # קבלת ההזמנות
            orders = await self._get_all_orders(params)
            
            # ארגון הנתונים לפי תקופה
            sales_data = self._organize_sales_by_period(orders, period, start_date, end_date)
            
            return sales_data
        except Exception as e:
            logger.error(f"שגיאה בקבלת נתוני מכירות לפי תקופה: {e}")
            return {"error": str(e)}

    async def _get_all_orders(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        קבלת כל ההזמנות העונות לקריטריונים.
        
        Args:
            params: פרמטרים לסינון ההזמנות
            
        Returns:
            רשימת כל ההזמנות
        """
        all_orders = []
        page = 1
        
        while True:
            # עדכון מספר העמוד
            params['page'] = page
            
            # קבלת הזמנות מהעמוד הנוכחי
            status_code, orders = await self.api._make_request("GET", "orders", params=params)
            
            if status_code != 200 or not orders:
                break
            
            all_orders.extend(orders)
            
            # אם קיבלנו פחות הזמנות מהמקסימום, סיימנו
            if len(orders) < params.get('per_page', 100):
                break
            
            page += 1
        
        return all_orders

    def _organize_sales_by_period(self, orders: List[Dict[str, Any]], period: str,
                                 start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        ארגון נתוני מכירות לפי תקופה.
        
        Args:
            orders: רשימת הזמנות
            period: התקופה לניתוח ('day', 'week', 'month', 'year')
            start_date: תאריך התחלה
            end_date: תאריך סיום
            
        Returns:
            מילון עם נתוני המכירות מאורגנים לפי תקופה
        """
        # מילון לשמירת נתוני המכירות לפי תקופה
        sales_by_period = {}
        
        # מילון לשמירת סך המכירות לפי תקופה
        total_sales_by_period = {}
        
        # מילון לשמירת מספר ההזמנות לפי תקופה
        order_count_by_period = {}
        
        # עיבוד כל ההזמנות
        for order in orders:
            # קבלת תאריך ההזמנה
            try:
                order_date = datetime.fromisoformat(order.get('date_created', '').replace('Z', '+00:00'))
            except (ValueError, TypeError):
                # אם התאריך לא תקין, נדלג על ההזמנה
                continue
            
            # חישוב המפתח לפי התקופה
            if period == 'day':
                period_key = order_date.strftime('%Y-%m-%d')
            elif period == 'week':
                # מספר השבוע בשנה
                year, week, _ = order_date.isocalendar()
                period_key = f"{year}-W{week:02d}"
            elif period == 'month':
                period_key = order_date.strftime('%Y-%m')
            elif period == 'year':
                period_key = order_date.strftime('%Y')
            else:
                # ברירת מחדל: יום
                period_key = order_date.strftime('%Y-%m-%d')
            
            # קבלת סכום ההזמנה
            order_total = float(order.get('total', 0))
            
            # עדכון נתוני המכירות
            if period_key not in sales_by_period:
                sales_by_period[period_key] = []
            
            sales_by_period[period_key].append({
                'id': order.get('id'),
                'date': order_date.isoformat(),
                'total': order_total,
                'status': order.get('status'),
                'customer_id': order.get('customer_id'),
                'items_count': len(order.get('line_items', []))
            })
            
            # עדכון סך המכירות
            total_sales_by_period[period_key] = total_sales_by_period.get(period_key, 0) + order_total
            
            # עדכון מספר ההזמנות
            order_count_by_period[period_key] = order_count_by_period.get(period_key, 0) + 1
        
        # יצירת רשימת כל התקופות בטווח (כולל תקופות ללא מכירות)
        all_periods = self._generate_all_periods(period, start_date, end_date)
        
        # מילוי נתונים עבור תקופות ללא מכירות
        for period_key in all_periods:
            if period_key not in sales_by_period:
                sales_by_period[period_key] = []
            
            if period_key not in total_sales_by_period:
                total_sales_by_period[period_key] = 0
            
            if period_key not in order_count_by_period:
                order_count_by_period[period_key] = 0
        
        # חישוב סטטיסטיקות
        total_sales = sum(total_sales_by_period.values())
        total_orders = sum(order_count_by_period.values())
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        # מציאת התקופה עם המכירות הגבוהות ביותר
        best_period = max(total_sales_by_period.items(), key=lambda x: x[1]) if total_sales_by_period else (None, 0)
        
        # מציאת התקופה עם המכירות הנמוכות ביותר (מבין תקופות עם מכירות)
        non_zero_periods = {k: v for k, v in total_sales_by_period.items() if v > 0}
        worst_period = min(non_zero_periods.items(), key=lambda x: x[1]) if non_zero_periods else (None, 0)
        
        # חישוב מגמה (אחוז שינוי בין התקופה הראשונה לאחרונה)
        sorted_periods = sorted(total_sales_by_period.items())
        trend_percentage = 0
        if len(sorted_periods) >= 2 and sorted_periods[0][1] > 0:
            first_period_sales = sorted_periods[0][1]
            last_period_sales = sorted_periods[-1][1]
            trend_percentage = ((last_period_sales - first_period_sales) / first_period_sales) * 100
        
        # ארגון התוצאה הסופית
        result = {
            'period_type': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_sales': total_sales,
            'total_orders': total_orders,
            'avg_order_value': avg_order_value,
            'best_period': {
                'period': best_period[0],
                'sales': best_period[1]
            },
            'worst_period': {
                'period': worst_period[0],
                'sales': worst_period[1]
            },
            'trend_percentage': trend_percentage,
            'sales_by_period': dict(sorted(total_sales_by_period.items())),
            'orders_by_period': dict(sorted(order_count_by_period.items())),
            'detailed_data': dict(sorted({k: v for k, v in sales_by_period.items() if v}.items()))
        }
        
        return result

    def _generate_all_periods(self, period: str, start_date: datetime, end_date: datetime) -> List[str]:
        """
        יצירת רשימת כל התקופות בטווח התאריכים.
        
        Args:
            period: התקופה לניתוח ('day', 'week', 'month', 'year')
            start_date: תאריך התחלה
            end_date: תאריך סיום
            
        Returns:
            רשימת כל התקופות בטווח
        """
        all_periods = []
        current_date = start_date
        
        if period == 'day':
            # יצירת רשימת כל הימים בטווח
            while current_date <= end_date:
                all_periods.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
        
        elif period == 'week':
            # יצירת רשימת כל השבועות בטווח
            # התאמה לתחילת השבוע (יום שני)
            current_date = current_date - timedelta(days=current_date.weekday())
            
            while current_date <= end_date:
                year, week, _ = current_date.isocalendar()
                all_periods.append(f"{year}-W{week:02d}")
                current_date += timedelta(weeks=1)
        
        elif period == 'month':
            # יצירת רשימת כל החודשים בטווח
            while (current_date.year < end_date.year or 
                  (current_date.year == end_date.year and current_date.month <= end_date.month)):
                all_periods.append(current_date.strftime('%Y-%m'))
                
                # מעבר לחודש הבא
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
        
        elif period == 'year':
            # יצירת רשימת כל השנים בטווח
            for year in range(start_date.year, end_date.year + 1):
                all_periods.append(str(year))
        
        return all_periods

    async def get_top_products(self, limit: int = 10, period: str = 'month', 
                              start_date: Optional[datetime] = None, 
                              end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        קבלת המוצרים הנמכרים ביותר.
        
        Args:
            limit: מספר המוצרים להחזרה
            period: התקופה לניתוח ('day', 'week', 'month', 'year')
            start_date: תאריך התחלה (אופציונלי)
            end_date: תאריך סיום (אופציונלי)
            
        Returns:
            מילון עם המוצרים הנמכרים ביותר
        """
        # הגדרת תאריכי ברירת מחדל
        if end_date is None:
            end_date = datetime.now()
        
        if start_date is None:
            if period == 'day':
                start_date = end_date - timedelta(days=30)
            elif period == 'week':
                start_date = end_date - timedelta(weeks=12)
            elif period == 'month':
                if end_date.month <= 12 and end_date.month > 11:  # חודש 12
                    start_date = end_date.replace(year=end_date.year - 1, month=1)
                elif end_date.month <= 11 and end_date.month > 0:  # חודשים 1-11
                    new_month = end_date.month + 1
                    start_date = end_date.replace(year=end_date.year - 1, month=new_month)
                else:
                    # במקרה של ערך חודש לא תקין, נחזור 12 חודשים אחורה
                    start_date = end_date - timedelta(days=365)
            elif period == 'year':
                start_date = end_date.replace(year=end_date.year - 5)
            else:
                start_date = end_date - timedelta(days=30)
        
        # קבלת כל ההזמנות בטווח התאריכים
        params = {
            'after': start_date.isoformat(),
            'before': end_date.isoformat(),
            'per_page': 100,
            'status': ['completed', 'processing']  # רק הזמנות שהושלמו או בתהליך
        }
        
        try:
            # קבלת ההזמנות
            orders = await self._get_all_orders(params)
            
            # ניתוח המוצרים הנמכרים ביותר
            top_products = self._analyze_top_products(orders, limit)
            
            return {
                'period_type': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'top_products': top_products
            }
        except Exception as e:
            logger.error(f"שגיאה בקבלת המוצרים הנמכרים ביותר: {e}")
            return {"error": str(e)}

    def _analyze_top_products(self, orders: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """
        ניתוח המוצרים הנמכרים ביותר מתוך רשימת הזמנות.
        
        Args:
            orders: רשימת הזמנות
            limit: מספר המוצרים להחזרה
            
        Returns:
            רשימת המוצרים הנמכרים ביותר
        """
        # מילון לשמירת נתוני מכירות לפי מוצר
        product_sales = defaultdict(lambda: {'quantity': 0, 'revenue': 0, 'orders': set()})
        
        # עיבוד כל ההזמנות
        for order in orders:
            order_id = order.get('id')
            line_items = order.get('line_items', [])
            
            for item in line_items:
                product_id = item.get('product_id')
                if not product_id:
                    continue
                
                product_name = item.get('name', f'מוצר {product_id}')
                quantity = item.get('quantity', 0)
                total = float(item.get('total', 0))
                
                # עדכון נתוני המוצר
                product_sales[product_id]['name'] = product_name
                product_sales[product_id]['quantity'] += quantity
                product_sales[product_id]['revenue'] += total
                product_sales[product_id]['orders'].add(order_id)
                
                # שמירת מידע נוסף על המוצר אם קיים
                if 'sku' in item and 'sku' not in product_sales[product_id]:
                    product_sales[product_id]['sku'] = item.get('sku')
                
                if 'price' in item and 'price' not in product_sales[product_id]:
                    product_sales[product_id]['price'] = item.get('price')
        
        # המרת מבנה הנתונים לרשימה ומיון לפי כמות
        products_list = []
        for product_id, data in product_sales.items():
            products_list.append({
                'id': product_id,
                'name': data['name'],
                'quantity_sold': data['quantity'],
                'revenue': data['revenue'],
                'orders_count': len(data['orders']),
                'avg_price': data['revenue'] / data['quantity'] if data['quantity'] > 0 else 0,
                'sku': data.get('sku', ''),
                'price': data.get('price', '')
            })
        
        # מיון לפי כמות מכירות (יורד)
        products_list.sort(key=lambda x: x['quantity_sold'], reverse=True)
        
        # החזרת המוצרים המובילים
        return products_list[:limit]

    async def get_customer_insights(self, period: str = 'month', 
                                   start_date: Optional[datetime] = None, 
                                   end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        קבלת תובנות על לקוחות.
        
        Args:
            period: התקופה לניתוח ('day', 'week', 'month', 'year')
            start_date: תאריך התחלה (אופציונלי)
            end_date: תאריך סיום (אופציונלי)
            
        Returns:
            מילון עם תובנות על לקוחות
        """
        # הגדרת תאריכי ברירת מחדל
        if end_date is None:
            end_date = datetime.now()
        
        if start_date is None:
            if period == 'day':
                start_date = end_date - timedelta(days=30)
            elif period == 'week':
                start_date = end_date - timedelta(weeks=12)
            elif period == 'month':
                if end_date.month <= 12 and end_date.month > 11:  # חודש 12
                    start_date = end_date.replace(year=end_date.year - 1, month=1)
                elif end_date.month <= 11 and end_date.month > 0:  # חודשים 1-11
                    new_month = end_date.month + 1
                    start_date = end_date.replace(year=end_date.year - 1, month=new_month)
                else:
                    # במקרה של ערך חודש לא תקין, נחזור 12 חודשים אחורה
                    start_date = end_date - timedelta(days=365)
            elif period == 'year':
                start_date = end_date.replace(year=end_date.year - 5)
            else:
                start_date = end_date - timedelta(days=30)
        
        # קבלת כל ההזמנות בטווח התאריכים
        params = {
            'after': start_date.isoformat(),
            'before': end_date.isoformat(),
            'per_page': 100,
            'status': ['completed', 'processing', 'on-hold']
        }
        
        try:
            # קבלת ההזמנות
            orders = await self._get_all_orders(params)
            
            # ניתוח נתוני לקוחות
            customer_insights = self._analyze_customer_data(orders)
            
            return {
                'period_type': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'customer_insights': customer_insights
            }
        except Exception as e:
            logger.error(f"שגיאה בקבלת תובנות על לקוחות: {e}")
            return {"error": str(e)}

    def _analyze_customer_data(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        ניתוח נתוני לקוחות מתוך רשימת הזמנות.
        
        Args:
            orders: רשימת הזמנות
            
        Returns:
            מילון עם תובנות על לקוחות
        """
        # מילון לשמירת נתוני לקוחות
        customer_data = defaultdict(lambda: {
            'orders': [],
            'total_spent': 0,
            'first_order_date': None,
            'last_order_date': None,
            'products_purchased': set(),
            'order_values': []
        })
        
        # מילון לשמירת נתוני לקוחות אנונימיים
        guest_orders = []
        
        # עיבוד כל ההזמנות
        for order in orders:
            order_id = order.get('id')
            customer_id = order.get('customer_id')
            order_total = float(order.get('total', 0))
            
            try:
                order_date = datetime.fromisoformat(order.get('date_created', '').replace('Z', '+00:00'))
            except (ValueError, TypeError):
                # אם התאריך לא תקין, נשתמש בתאריך נוכחי
                order_date = datetime.now()
            
            # קבלת רשימת מוצרים בהזמנה
            products = [item.get('product_id') for item in order.get('line_items', []) if item.get('product_id')]
            
            # אם יש מזהה לקוח, נעדכן את נתוני הלקוח
            if customer_id:
                # עדכון נתוני הלקוח
                customer_data[customer_id]['orders'].append(order_id)
                customer_data[customer_id]['total_spent'] += order_total
                customer_data[customer_id]['order_values'].append(order_total)
                customer_data[customer_id]['products_purchased'].update(products)
                
                # עדכון תאריך הזמנה ראשונה
                if (customer_data[customer_id]['first_order_date'] is None or 
                    order_date < customer_data[customer_id]['first_order_date']):
                    customer_data[customer_id]['first_order_date'] = order_date
                
                # עדכון תאריך הזמנה אחרונה
                if (customer_data[customer_id]['last_order_date'] is None or 
                    order_date > customer_data[customer_id]['last_order_date']):
                    customer_data[customer_id]['last_order_date'] = order_date
                
                # שמירת פרטי לקוח אם קיימים
                if 'billing' in order and 'first_name' in order['billing'] and 'customer_name' not in customer_data[customer_id]:
                    first_name = order['billing'].get('first_name', '')
                    last_name = order['billing'].get('last_name', '')
                    customer_data[customer_id]['customer_name'] = f"{first_name} {last_name}".strip()
                
                if 'billing' in order and 'email' in order['billing'] and 'email' not in customer_data[customer_id]:
                    customer_data[customer_id]['email'] = order['billing'].get('email', '')
            else:
                # הזמנה של אורח
                guest_orders.append({
                    'order_id': order_id,
                    'order_total': order_total,
                    'order_date': order_date.isoformat(),
                    'products_count': len(products)
                })
        
        # חישוב סטטיסטיקות כלליות
        total_customers = len(customer_data)
        total_orders = sum(len(data['orders']) for data in customer_data.values()) + len(guest_orders)
        total_revenue = sum(data['total_spent'] for data in customer_data.values()) + sum(order['order_total'] for order in guest_orders)
        
        # חישוב ערך ממוצע להזמנה
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # חישוב ערך ממוצע ללקוח
        avg_customer_value = total_revenue / total_customers if total_customers > 0 else 0
        
        # חישוב מספר הזמנות ממוצע ללקוח
        avg_orders_per_customer = sum(len(data['orders']) for data in customer_data.values()) / total_customers if total_customers > 0 else 0
        
        # מציאת הלקוחות המובילים (לפי סכום הזמנות)
        top_customers = []
        for customer_id, data in customer_data.items():
            top_customers.append({
                'customer_id': customer_id,
                'customer_name': data.get('customer_name', f'לקוח {customer_id}'),
                'email': data.get('email', ''),
                'total_spent': data['total_spent'],
                'orders_count': len(data['orders']),
                'avg_order_value': data['total_spent'] / len(data['orders']) if data['orders'] else 0,
                'first_order_date': data['first_order_date'].isoformat() if data['first_order_date'] else None,
                'last_order_date': data['last_order_date'].isoformat() if data['last_order_date'] else None,
                'days_since_last_order': (datetime.now() - data['last_order_date']).days if data['last_order_date'] else None,
                'products_count': len(data['products_purchased'])
            })
        
        # מיון הלקוחות לפי סכום הזמנות (יורד)
        top_customers.sort(key=lambda x: x['total_spent'], reverse=True)
        
        # חישוב התפלגות ערך הזמנות
        all_order_values = []
        for data in customer_data.values():
            all_order_values.extend(data['order_values'])
        
        order_values_stats = {}
        if all_order_values:
            order_values_stats = {
                'min': min(all_order_values),
                'max': max(all_order_values),
                'avg': sum(all_order_values) / len(all_order_values),
                'median': statistics.median(all_order_values) if len(all_order_values) > 0 else 0
            }
        
        # ארגון התוצאה הסופית
        result = {
            'total_customers': total_customers,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'avg_order_value': avg_order_value,
            'avg_customer_value': avg_customer_value,
            'avg_orders_per_customer': avg_orders_per_customer,
            'order_values_stats': order_values_stats,
            'top_customers': top_customers[:10],  # 10 הלקוחות המובילים
            'guest_orders_count': len(guest_orders),
            'guest_orders_revenue': sum(order['order_total'] for order in guest_orders)
        }
        
        return result

    async def generate_sales_report(self, report_type: str = 'monthly', 
                                  start_date: Optional[datetime] = None, 
                                  end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        יצירת דוח מכירות.
        
        Args:
            report_type: סוג הדוח ('daily', 'weekly', 'monthly', 'yearly')
            start_date: תאריך התחלה (אופציונלי)
            end_date: תאריך סיום (אופציונלי)
            
        Returns:
            מילון עם דוח המכירות
        """
        # המרת סוג הדוח לתקופה המתאימה
        period_mapping = {
            'daily': 'day',
            'weekly': 'week',
            'monthly': 'month',
            'yearly': 'year'
        }
        
        period = period_mapping.get(report_type, 'month')
        
        # קבלת נתוני מכירות לפי תקופה
        sales_data = await self.get_sales_by_period(period, start_date, end_date)
        
        # קבלת המוצרים הנמכרים ביותר
        top_products_data = await self.get_top_products(10, period, start_date, end_date)
        
        # קבלת תובנות על לקוחות
        customer_insights = await self.get_customer_insights(period, start_date, end_date)
        
        # יצירת הדוח
        report = {
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'sales_summary': {
                'total_sales': sales_data.get('total_sales', 0),
                'total_orders': sales_data.get('total_orders', 0),
                'avg_order_value': sales_data.get('avg_order_value', 0),
                'best_period': sales_data.get('best_period', {}),
                'worst_period': sales_data.get('worst_period', {}),
                'trend_percentage': sales_data.get('trend_percentage', 0)
            },
            'sales_by_period': sales_data.get('sales_by_period', {}),
            'top_products': top_products_data.get('top_products', []),
            'customer_insights': customer_insights.get('customer_insights', {})
        }
        
        return report

    def format_sales_report(self, report: Dict[str, Any]) -> str:
        """
        פורמט דוח מכירות לתצוגה.
        
        Args:
            report: דוח המכירות
            
        Returns:
            דוח מכירות מפורמט
        """
        if "error" in report:
            return f"🚫 שגיאה בהפקת דוח מכירות: {report['error']}"
        
        # פורמט כותרת הדוח
        report_type_he = {
            'daily': 'יומי',
            'weekly': 'שבועי',
            'monthly': 'חודשי',
            'yearly': 'שנתי'
        }
        
        report_title = f"דוח מכירות {report_type_he.get(report['report_type'], report['report_type'])}"
        
        # פורמט תאריכים
        start_date = report['period']['start_date']
        end_date = report['period']['end_date']
        
        date_range = ""
        if start_date and end_date:
            date_range = f"לתקופה {start_date} עד {end_date}"
        
        # פורמט סיכום מכירות
        sales_summary = report['sales_summary']
        total_sales = f"{sales_summary['total_sales']:.2f}"
        total_orders = str(sales_summary['total_orders'])
        avg_order_value = f"{sales_summary['avg_order_value']:.2f}"
        
        # פורמט מגמה
        trend = sales_summary['trend_percentage']
        trend_emoji = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"
        trend_text = f"{trend:.1f}%" if trend != 0 else "0%"
        
        # פורמט תקופות מובילות
        best_period = sales_summary['best_period']
        worst_period = sales_summary['worst_period']
        
        # פורמט מוצרים מובילים
        top_products = report['top_products']
        top_products_text = ""
        
        for i, product in enumerate(top_products[:5], 1):
            product_name = product['name']
            quantity = product['quantity_sold']
            revenue = f"{product['revenue']:.2f}"
            top_products_text += f"{i}. {product_name} - {quantity} יחידות (₪{revenue})\n"
        
        # פורמט תובנות לקוחות
        customer_insights = report['customer_insights']
        
        # בניית הדוח המפורמט
        formatted_report = f"""
📊 *{report_title}*
{date_range}

💰 *סיכום מכירות:*
• סך מכירות: ₪{total_sales}
• מספר הזמנות: {total_orders}
• ערך הזמנה ממוצע: ₪{avg_order_value}
• מגמה: {trend_emoji} {trend_text}

🏆 *תקופות מובילות:*
• תקופה מובילה: {best_period['period']} (₪{best_period['sales']:.2f})
• תקופה חלשה: {worst_period['period']} (₪{worst_period['sales']:.2f})

🛍️ *מוצרים מובילים:*
{top_products_text}

👥 *תובנות לקוחות:*
• מספר לקוחות: {customer_insights.get('total_customers', 0)}
• ערך ממוצע ללקוח: ₪{customer_insights.get('avg_customer_value', 0):.2f}
• הזמנות ממוצע ללקוח: {customer_insights.get('avg_orders_per_customer', 0):.1f}
• הזמנות אורחים: {customer_insights.get('guest_orders_count', 0)} (₪{customer_insights.get('guest_orders_revenue', 0):.2f})
"""
        
        return formatted_report

# פונקציות עזר לשימוש ישיר

async def get_sales_report(store_url: str, consumer_key: str, consumer_secret: str, 
                          report_type: str = 'monthly', start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    הפקת דוח מכירות.
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        report_type: סוג הדוח ('daily', 'weekly', 'monthly', 'yearly')
        start_date: תאריך התחלה (אופציונלי, פורמט ISO: YYYY-MM-DD)
        end_date: תאריך סיום (אופציונלי, פורמט ISO: YYYY-MM-DD)
        
    Returns:
        טאפל עם: האם הפעולה הצליחה, הודעה, דוח המכירות
    """
    try:
        # יצירת מופע של ה-API
        from src.services.woocommerce.api import WooCommerceAPI
        
        woo_api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # המרת תאריכים למבנה datetime אם סופקו
        start_datetime = None
        end_datetime = None
        
        if start_date:
            start_datetime = datetime.fromisoformat(start_date)
        
        if end_date:
            end_datetime = datetime.fromisoformat(end_date)
        
        # יצירת מנהל ניתוח מכירות
        sales_analyzer = SalesAnalyzer(woo_api)
        
        # הפקת הדוח
        report = await sales_analyzer.generate_sales_report(report_type, start_datetime, end_datetime)
        
        # פורמט הדוח לתצוגה
        formatted_report = sales_analyzer.format_sales_report(report)
        
        return True, formatted_report, report
    except Exception as e:
        logger.error(f"שגיאה בהפקת דוח מכירות: {e}")
        return False, f"שגיאה בהפקת דוח מכירות: {str(e)}", None

async def get_top_selling_products(store_url: str, consumer_key: str, consumer_secret: str, 
                                  limit: int = 10, period: str = 'month') -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
    """
    קבלת המוצרים הנמכרים ביותר.
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        limit: מספר המוצרים להחזרה
        period: התקופה לניתוח ('day', 'week', 'month', 'year')
        
    Returns:
        טאפל עם: האם הפעולה הצליחה, הודעה, רשימת המוצרים הנמכרים ביותר
    """
    try:
        # יצירת מופע של ה-API
        from src.services.woocommerce.api import WooCommerceAPI
        
        woo_api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # יצירת מנהל ניתוח מכירות
        sales_analyzer = SalesAnalyzer(woo_api)
        
        # קבלת המוצרים הנמכרים ביותר
        result = await sales_analyzer.get_top_products(limit, period)
        
        if "error" in result:
            return False, f"שגיאה בקבלת המוצרים הנמכרים ביותר: {result['error']}", None
        
        # יצירת הודעה מפורמטת
        products = result['top_products']
        message = f"🏆 *המוצרים הנמכרים ביותר ({period})*\n\n"
        
        for i, product in enumerate(products, 1):
            product_name = product['name']
            quantity = product['quantity_sold']
            revenue = f"{product['revenue']:.2f}"
            message += f"{i}. {product_name} - {quantity} יחידות (₪{revenue})\n"
        
        return True, message, products
    except Exception as e:
        logger.error(f"שגיאה בקבלת המוצרים הנמכרים ביותר: {e}")
        return False, f"שגיאה בקבלת המוצרים הנמכרים ביותר: {str(e)}", None
