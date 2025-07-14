from pydantic import BaseModel, Field, constr
from typing import List, Optional, Any
from datetime import datetime
from shared.models import ErrorResponse, DocumentBase

class DocumentBase(BaseModel):
    title: constr(min_length=1, max_length=256)
    content: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    title: Optional[constr(min_length=1, max_length=256)] = None
    content: Optional[str] = None

class DocumentOut(DocumentBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    class Config:
        orm_mode = True

class DocumentVersion(BaseModel):
    version_number: int
    content: str
    diff: Optional[Any] = None
    created_at: datetime
    created_by: str

class DocumentVersionOut(DocumentVersion):
    id: str
    document_id: str
    class Config:
        orm_mode = True

class Permission(BaseModel):
    user_id: str
    permission: str  # read, write, admin

class ShareRequest(BaseModel):
    user_ids: List[str]
    permission: str  # read, write, admin

class Collaborator(BaseModel):
    user_id: str
    role: str
    added_at: datetime

class SearchRequest(BaseModel):
    query: str
    page: int = 1
    size: int = 10

class SearchResult(BaseModel):
    id: str
    title: str
    snippet: Optional[str] = None
    score: Optional[float] = None

class AnalyticsEvent(BaseModel):
    event: str  # view, edit, share, etc.
    user_id: Optional[str]
    timestamp: datetime
    details: Optional[Any] = None

class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None 