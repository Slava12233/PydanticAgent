"""
מודלים לתגובות ומבני נתונים של המערכת
"""
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from enum import Enum

class ResponseType(str, Enum):
    """סוגי תגובות במערכת"""
    CHAT = "chat"
    HANDLER = "handler"
    SERVICE = "service"
    ERROR = "error"

class BaseResponse(BaseModel):
    """מודל בסיסי לכל התגובות במערכת"""
    type: ResponseType
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ChatResponse(BaseResponse):
    """מודל לתגובת הצ'אט המובנית"""
    type: ResponseType = ResponseType.CHAT
    confidence: Optional[float] = None
    sources: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None

class HandlerResponse(BaseResponse):
    """מודל לתגובת handler"""
    type: ResponseType = ResponseType.HANDLER
    handler_name: str
    handler_action: str

class ServiceResponse(BaseResponse):
    """מודל לתגובת שירות"""
    type: ResponseType = ResponseType.SERVICE
    service_name: str
    operation: str
    
class ErrorResponse(BaseResponse):
    """מודל לתגובת שגיאה"""
    type: ResponseType = ResponseType.ERROR
    error_code: str
    error_details: Optional[str] = None
    stack_trace: Optional[str] = None

# טיפוס מאוחד לכל סוגי התגובות
AnyResponse = Union[ChatResponse, HandlerResponse, ServiceResponse, ErrorResponse]

def create_error_response(
    message: str,
    error_code: str,
    error_details: Optional[str] = None,
    stack_trace: Optional[str] = None
) -> ErrorResponse:
    """
    יצירת תגובת שגיאה
    
    Args:
        message: הודעת השגיאה
        error_code: קוד השגיאה
        error_details: פרטי השגיאה (אופציונלי)
        stack_trace: מעקב המחסנית (אופציונלי)
        
    Returns:
        תגובת שגיאה מובנית
    """
    return ErrorResponse(
        success=False,
        message=message,
        error_code=error_code,
        error_details=error_details,
        stack_trace=stack_trace
    )

class TaskIdentification(BaseModel):
    """מודל לזיהוי משימה"""
    task_type: str
    confidence: float
    parameters: Optional[Dict[str, Any]] = None
    context: Optional[str] = None 