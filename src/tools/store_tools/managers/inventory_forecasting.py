"""
מודול לחיזוי מלאי בחנות WooCommerce.
מאפשר ניתוח מגמות מכירה וחיזוי מלאי עתידי.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from src.tools.store_tools.managers.base_manager import BaseManager

logger = logging.getLogger(__name__)

class InventoryForecasting(BaseManager):
    """מחלקה לחיזוי מלאי המאפשרת ניתוח מגמות וחיזוי עתידי."""

    def _get_resource_name(self) -> str:
        """מחזיר את שם המשאב"""
        return "products"

    async def forecast_inventory(self, product_id: int, days: int = 30, forecast_periods: List[int] = None) -> Dict[str, Any]:
        """
        חיזוי מלאי למוצר.
        
        Args:
            product_id: מזהה המוצר
            days: מספר ימים לחיזוי (ברירת מחדל: 30)
            forecast_periods: רשימת תקופות לחיזוי בימים (ברירת מחדל: [7, 14, 30, 60, 90])
            
        Returns:
            תחזית המלאי
        """
        try:
            # הגדרת תקופות חיזוי ברירת מחדל אם לא סופקו
            if forecast_periods is None:
                forecast_periods = [7, 14, 30, 60, 90]
            
            # קבלת מידע על המוצר
            success, message, product = await self.get(product_id)
            if not success:
                logger.warning(f"מוצר עם מזהה {product_id} לא נמצא")
                return {
                    "success": False,
                    "message": f"שגיאה בחיזוי מלאי: מוצר לא נמצא",
                    "forecast": None
                }
            
            # חישוב תאריך התחלה (30 ימים אחורה)
            start_date = datetime.now() - timedelta(days=days)
            
            # פרמטרים לשליפת הזמנות
            orders_params = {
                "after": start_date.isoformat(),
                "per_page": 100
            }
            
            # קבלת הזמנות
            success, message, orders = await self.list(orders_params)
            if not success:
                logger.error(f"שגיאה בקבלת הזמנות: {message}")
                return {
                    "success": False,
                    "message": "שגיאה בקבלת היסטוריית הזמנות",
                    "forecast": None
                }
            
            # ניתוח קצב המכירות
            total_sold = 0
            for order in orders:
                if order.get("status") not in ["completed", "processing"]:
                    continue
                
                for item in order.get("line_items", []):
                    if item.get("product_id") == product_id:
                        total_sold += item.get("quantity", 0)
            
            # חישוב ממוצע מכירות יומי
            daily_sales_avg = total_sold / days if days > 0 else 0
            
            # חישוב ימים עד אזילת המלאי
            current_stock = product.get("stock_quantity", 0) or 0
            days_until_stockout = round(current_stock / daily_sales_avg) if daily_sales_avg > 0 else float('inf')
            
            # חיזוי מלאי לפי ימים
            inventory_forecast = {}
            
            for forecast_day in forecast_periods:
                predicted_stock = max(0, current_stock - (daily_sales_avg * forecast_day))
                inventory_forecast[f"{forecast_day}_days"] = round(predicted_stock)
            
            # הכנת נתוני התחזית
            forecast_data = {
                "product_id": product_id,
                "product_name": product.get("name"),
                "current_stock": current_stock,
                "daily_sales_avg": round(daily_sales_avg, 4),
                "days_until_stockout": days_until_stockout if days_until_stockout != float('inf') else None,
                "total_sold_last_30_days": total_sold,
                "forecast": inventory_forecast,
                "analysis_period_days": days,
                "will_be_out_of_stock": days_until_stockout <= days if days_until_stockout != float('inf') else False,
                "reorder_recommendation": days_until_stockout <= days * 1.5 if days_until_stockout != float('inf') else False,
                "out_of_stock_date": (datetime.now() + timedelta(days=days_until_stockout)).isoformat() if days_until_stockout != float('inf') else None
            }
            
            return {
                "success": True,
                "message": "תחזית מלאי חושבה בהצלחה",
                "forecast": forecast_data
            }
        except Exception as e:
            logger.error(f"שגיאה בחיזוי מלאי למוצר {product_id}: {e}")
            return {
                "success": False,
                "message": f"שגיאה בחיזוי מלאי: {str(e)}",
                "forecast": None
            } 