from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import patient as patient_crud
from app.schemas.patient import Patient, PatientCreate, PatientUpdate
from app.dependencies import get_db

router = APIRouter()


@router.get("/", response_model=List[Patient])
def read_patients(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
):
    """
    Retrieve patients with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status
        
    Returns:
        List of patients
    """
    patients = patient_crud.get_patients(
        db, skip=skip, limit=limit,
        is_active=is_active
    )
    return patients


@router.post("/", response_model=Patient, status_code=status.HTTP_201_CREATED)
def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new patient.
    
    Args:
        patient: Patient data to create
        db: Database session
        
    Returns:
        Created patient
    """
    return patient_crud.create_patient(db=db, patient=patient)


@router.get("/{patient_id}", response_model=Patient)
def read_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific patient by ID.
    
    Args:
        patient_id: ID of the patient to retrieve
        db: Database session
        
    Returns:
        Patient object
        
    Raises:
        HTTPException: If patient not found
    """
    db_patient = patient_crud.get_patient(db, patient_id=patient_id)
    if not db_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    return db_patient


@router.put("/{patient_id}", response_model=Patient)
def update_patient(
    patient_id: int,
    patient: PatientUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a patient.
    
    Args:
        patient_id: ID of the patient to update
        patient: Updated patient data
        db: Database session
        
    Returns:
        Updated patient
        
    Raises:
        HTTPException: If patient not found
    """
    db_patient = patient_crud.update_patient(
        db=db,
        patient_id=patient_id,
        patient=patient
    )
    if not db_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    return db_patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a patient (soft delete).
    
    Args:
        patient_id: ID of the patient to delete
        db: Database session
        
    Returns:
        None
        
    Raises:
        HTTPException: If patient not found
    """
    success = patient_crud.delete_patient(db=db, patient_id=patient_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        ) 