from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.doctor import Doctor
from app.schemas.doctor import DoctorCreate, DoctorUpdate


def get_doctor(db: Session, doctor_id: int) -> Optional[Doctor]:
    """
    Get a doctor by ID.
    
    Args:
        db: Database session
        doctor_id: ID of the doctor to retrieve
        
    Returns:
        Doctor object if found, None otherwise
    """
    return db.query(Doctor).filter(Doctor.id == doctor_id).first()


def get_doctors(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    specialization: Optional[str] = None,
    is_active: Optional[bool] = None
) -> List[Doctor]:
    """
    Get a list of doctors with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        specialization: Filter by specialization
        is_active: Filter by active status
        
    Returns:
        List of Doctor objects
    """
    query = db.query(Doctor)
    
    if specialization:
        query = query.filter(Doctor.specialization == specialization)
    if is_active is not None:
        query = query.filter(Doctor.is_active == is_active)
        
    return query.offset(skip).limit(limit).all()


def create_doctor(db: Session, doctor: DoctorCreate) -> Doctor:
    """
    Create a new doctor.
    
    Args:
        db: Database session
        doctor: Doctor data to create
        
    Returns:
        Created Doctor object
    """
    db_doctor = Doctor(**doctor.model_dump())
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor


def update_doctor(
    db: Session, 
    doctor_id: int, 
    doctor: DoctorUpdate
) -> Optional[Doctor]:
    """
    Update a doctor.
    
    Args:
        db: Database session
        doctor_id: ID of the doctor to update
        doctor: Updated doctor data
        
    Returns:
        Updated Doctor object if found, None otherwise
    """
    db_doctor = get_doctor(db, doctor_id)
    if not db_doctor:
        return None
        
    update_data = doctor.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_doctor, field, value)
        
    db.commit()
    db.refresh(db_doctor)
    return db_doctor


def delete_doctor(db: Session, doctor_id: int) -> bool:
    """
    Delete a doctor (soft delete).
    
    Args:
        db: Database session
        doctor_id: ID of the doctor to delete
        
    Returns:
        True if doctor was found and deleted, False otherwise
    """
    db_doctor = get_doctor(db, doctor_id)
    if not db_doctor:
        return False
        
    db_doctor.is_active = False
    db.commit()
    return True 