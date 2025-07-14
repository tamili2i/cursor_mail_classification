from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict
from shared.models import ErrorResponse

# Event type constants
USER_JOINED = "user_joined"
USER_LEFT = "user_left"
DOCUMENT_CHANGE = "document_change"
CURSOR_POSITION = "cursor_position"
DOCUMENT_SAVED = "document_saved"
PRESENCE = "presence"
ATTRIBUTION = "attribution"
RECOVERY = "recovery"

class UserJoinedEvent(BaseModel):
    type: str = Field(USER_JOINED, const=True)
    user_id: str
    username: Optional[str] = None

class UserLeftEvent(BaseModel):
    type: str = Field(USER_LEFT, const=True)
    user_id: str

class DocumentChangeEvent(BaseModel):
    type: str = Field(DOCUMENT_CHANGE, const=True)
    user_id: str
    op: Dict[str, Any]  # OT operation (insert, delete, etc.)
    version: int
    timestamp: float

class CursorPositionEvent(BaseModel):
    type: str = Field(CURSOR_POSITION, const=True)
    user_id: str
    position: int
    selection: Optional[List[int]] = None

class DocumentSavedEvent(BaseModel):
    type: str = Field(DOCUMENT_SAVED, const=True)
    user_id: str
    version: int
    timestamp: float

class PresenceEvent(BaseModel):
    type: str = Field(PRESENCE, const=True)
    users: List[Dict[str, Any]]  # [{user_id, username, cursor_position, ...}]

class AttributionEvent(BaseModel):
    type: str = Field(ATTRIBUTION, const=True)
    changes: List[Dict[str, Any]]  # [{user_id, op, timestamp}]

class RecoveryEvent(BaseModel):
    type: str = Field(RECOVERY, const=True)
    state: Dict[str, Any]

class EventEnvelope(BaseModel):
    type: str
    payload: Any 