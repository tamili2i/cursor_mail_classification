from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.appointment import AppointmentStatus


class AppointmentBase(BaseModel):
    """Base schema for Appointment."""
    doctor_id: int
    patient_id: int
    appointment_datetime: datetime
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    """Schema for creating a new Appointment."""
    pass


class AppointmentUpdate(BaseModel):
    """Schema for updating an Appointment."""
    appointment_datetime: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None


class AppointmentInDB(AppointmentBase):
    """Schema for Appointment in database."""
    id: int
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Appointment(AppointmentInDB):
    """Schema for Appointment response."""
    pass 