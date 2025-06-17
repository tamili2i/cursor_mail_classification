from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate


def get_appointment(db: Session, appointment_id: int) -> Optional[Appointment]:
    """
    Get an appointment by ID.
    
    Args:
        db: Database session
        appointment_id: ID of the appointment to retrieve
        
    Returns:
        Appointment object if found, None otherwise
    """
    return db.query(Appointment).filter(Appointment.id == appointment_id).first()


def get_appointments(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    status: Optional[AppointmentStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Appointment]:
    """
    Get a list of appointments with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        doctor_id: Filter by doctor ID
        patient_id: Filter by patient ID
        status: Filter by appointment status
        start_date: Filter by start date
        end_date: Filter by end date
        
    Returns:
        List of Appointment objects
    """
    query = db.query(Appointment)
    
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    if status:
        query = query.filter(Appointment.status == status)
    if start_date:
        query = query.filter(Appointment.appointment_datetime >= start_date)
    if end_date:
        query = query.filter(Appointment.appointment_datetime <= end_date)
        
    return query.offset(skip).limit(limit).all()


def create_appointment(db: Session, appointment: AppointmentCreate) -> Appointment:
    """
    Create a new appointment.
    
    Args:
        db: Database session
        appointment: Appointment data to create
        
    Returns:
        Created Appointment object
        
    Raises:
        ValueError: If appointment time slot is not available
    """
    # Check if the time slot is available
    existing_appointment = db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.appointment_datetime == appointment.appointment_datetime,
            Appointment.status != AppointmentStatus.CANCELLED
        )
    ).first()
    
    if existing_appointment:
        raise ValueError("Appointment slot is not available")
    
    db_appointment = Appointment(**appointment.model_dump())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


def update_appointment(
    db: Session,
    appointment_id: int,
    appointment: AppointmentUpdate
) -> Optional[Appointment]:
    """
    Update an appointment.
    
    Args:
        db: Database session
        appointment_id: ID of the appointment to update
        appointment: Updated appointment data
        
    Returns:
        Updated Appointment object if found, None otherwise
        
    Raises:
        ValueError: If new appointment time slot is not available
    """
    db_appointment = get_appointment(db, appointment_id)
    if not db_appointment:
        return None
        
    update_data = appointment.model_dump(exclude_unset=True)
    
    # Check if the new time slot is available
    if "appointment_datetime" in update_data:
        existing_appointment = db.query(Appointment).filter(
            and_(
                Appointment.doctor_id == db_appointment.doctor_id,
                Appointment.appointment_datetime == update_data["appointment_datetime"],
                Appointment.id != appointment_id,
                Appointment.status != AppointmentStatus.CANCELLED
            )
        ).first()
        
        if existing_appointment:
            raise ValueError("Appointment slot is not available")
    
    for field, value in update_data.items():
        setattr(db_appointment, field, value)
        
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


def cancel_appointment(db: Session, appointment_id: int) -> bool:
    """
    Cancel an appointment.
    
    Args:
        db: Database session
        appointment_id: ID of the appointment to cancel
        
    Returns:
        True if appointment was found and cancelled, False otherwise
    """
    db_appointment = get_appointment(db, appointment_id)
    if not db_appointment:
        return False
        
    db_appointment.status = AppointmentStatus.CANCELLED
    db.commit()
    return True 