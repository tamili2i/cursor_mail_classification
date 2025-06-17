from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, constr


class DoctorBase(BaseModel):
    """Base schema for Doctor."""
    first_name: str
    last_name: str
    specialization: str
    email: EmailStr
    phone_number: constr(regex=r'^\+?[1-9]\d{1,14}$')


class DoctorCreate(DoctorBase):
    """Schema for creating a new Doctor."""
    pass


class DoctorUpdate(BaseModel):
    """Schema for updating a Doctor."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    specialization: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[constr(regex=r'^\+?[1-9]\d{1,14}$')] = None
    is_active: Optional[bool] = None


class DoctorInDB(DoctorBase):
    """Schema for Doctor in database."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Doctor(DoctorInDB):
    """Schema for Doctor response."""
    pass 