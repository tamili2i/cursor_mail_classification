from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr, constr


class PatientBase(BaseModel):
    """Base schema for Patient."""
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: constr(regex=r'^\+?[1-9]\d{1,14}$')
    date_of_birth: date


class PatientCreate(PatientBase):
    """Schema for creating a new Patient."""
    pass


class PatientUpdate(BaseModel):
    """Schema for updating a Patient."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[constr(regex=r'^\+?[1-9]\d{1,14}$')] = None
    date_of_birth: Optional[date] = None
    is_active: Optional[bool] = None


class PatientInDB(PatientBase):
    """Schema for Patient in database."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Patient(PatientInDB):
    """Schema for Patient response."""
    pass 