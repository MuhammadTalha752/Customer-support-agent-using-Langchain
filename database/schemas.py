from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
 
 
class ComplaintCreate(BaseModel):
    user_id: str
    description: str = Field(..., min_length=5)
 
 
class ComplaintOut(BaseModel):
    complaint_number: str
    user_id: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
 
    class Config:
        from_attributes = True
 
 
class ComplaintStatusUpdate(BaseModel):
    status: str  # e.g. "open", "in_progress", "resolved", "closed"
 
 
class ChatMessage(BaseModel):
    session_id: str
    user_id: str
    message: str
 
 
class ChatResponse(BaseModel):
    reply: str
    tool_used: Optional[str] = None
 