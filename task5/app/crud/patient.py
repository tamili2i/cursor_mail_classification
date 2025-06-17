from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


def get_patient(db: Session, patient_id: int) -> Optional[Patient]:
    """
    Get a patient by ID.
    
    Args:
        db: Database session
        patient_id: ID of the patient to retrieve
        
    Returns:
        Patient object if found, None otherwise
    """
    return db.query(Patient).filter(Patient.id == patient_id).first()


def get_patients(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[Patient]:
    """
    Get a list of patients with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status
        
    Returns:
        List of Patient objects
    """
    query = db.query(Patient)
    
    if is_active is not None:
        query = query.filter(Patient.is_active == is_active)
        
    return query.offset(skip).limit(limit).all()


def create_patient(db: Session, patient: PatientCreate) -> Patient:
    """
    Create a new patient.
    
    Args:
        db: Database session
        patient: Patient data to create
        
    Returns:
        Created Patient object
    """
    db_patient = Patient(**patient.model_dump())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient


def update_patient(
    db: Session, 
    patient_id: int, 
    patient: PatientUpdate
) -> Optional[Patient]:
    """
    Update a patient.
    
    Args:
        db: Database session
        patient_id: ID of the patient to update
        patient: Updated patient data
        
    Returns:
        Updated Patient object if found, None otherwise
    """
    db_patient = get_patient(db, patient_id)
    if not db_patient:
        return None
        
    update_data = patient.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_patient, field, value)
        
    db.commit()
    db.refresh(db_patient)
    return db_patient


def delete_patient(db: Session, patient_id: int) -> bool:
    """
    Delete a patient (soft delete).
    
    Args:
        db: Database session
        patient_id: ID of the patient to delete
        
    Returns:
        True if patient was found and deleted, False otherwise
    """
    db_patient = get_patient(db, patient_id)
    if not db_patient:
        return False
        
    db_patient.is_active = False
    db.commit()
    return True 