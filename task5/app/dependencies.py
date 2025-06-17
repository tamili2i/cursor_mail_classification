from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.crud import doctor, patient, appointment


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_doctor_by_id(db: Session = Depends(get_db), doctor_id: int = None):
    """
    Get doctor by ID or raise 404.
    
    Args:
        db: Database session
        doctor_id: ID of the doctor to retrieve
        
    Returns:
        Doctor object
        
    Raises:
        HTTPException: If doctor not found
    """
    if doctor_id is None:
        return None
        
    db_doctor = doctor.get_doctor(db, doctor_id)
    if not db_doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    return db_doctor


def get_patient_by_id(db: Session = Depends(get_db), patient_id: int = None):
    """
    Get patient by ID or raise 404.
    
    Args:
        db: Database session
        patient_id: ID of the patient to retrieve
        
    Returns:
        Patient object
        
    Raises:
        HTTPException: If patient not found
    """
    if patient_id is None:
        return None
        
    db_patient = patient.get_patient(db, patient_id)
    if not db_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    return db_patient


def get_appointment_by_id(db: Session = Depends(get_db), appointment_id: int = None):
    """
    Get appointment by ID or raise 404.
    
    Args:
        db: Database session
        appointment_id: ID of the appointment to retrieve
        
    Returns:
        Appointment object
        
    Raises:
        HTTPException: If appointment not found
    """
    if appointment_id is None:
        return None
        
    db_appointment = appointment.get_appointment(db, appointment_id)
    if not db_appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    return db_appointment 