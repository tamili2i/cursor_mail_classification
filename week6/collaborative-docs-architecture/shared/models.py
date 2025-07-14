from pydantic import BaseModel, EmailStr, constr
from typing import Optional, Any
from datetime import datetime

class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class DocumentBase(BaseModel):
    title: constr(min_length=1, max_length=256)
    content: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None 