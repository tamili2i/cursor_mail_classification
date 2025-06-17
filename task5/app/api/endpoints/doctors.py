from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.crud import doctor as doctor_crud
from app.schemas.doctor import Doctor, DoctorCreate, DoctorUpdate
from app.dependencies import get_db

router = APIRouter()


@router.get("/", response_model=List[Doctor])
def read_doctors(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    specialization: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """
    Retrieve doctors with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        specialization: Filter by specialization
        is_active: Filter by active status
        
    Returns:
        List of doctors
    """
    doctors = doctor_crud.get_doctors(
        db, skip=skip, limit=limit,
        specialization=specialization,
        is_active=is_active
    )
    return doctors


@router.post("/", response_model=Doctor, status_code=status.HTTP_201_CREATED)
def create_doctor(
    doctor: DoctorCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new doctor.
    
    Args:
        doctor: Doctor data to create
        db: Database session
        
    Returns:
        Created doctor
    """
    return doctor_crud.create_doctor(db=db, doctor=doctor)


@router.get("/{doctor_id}", response_model=Doctor)
def read_doctor(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific doctor by ID.
    
    Args:
        doctor_id: ID of the doctor to retrieve
        db: Database session
        
    Returns:
        Doctor object
        
    Raises:
        HTTPException: If doctor not found
    """
    db_doctor = doctor_crud.get_doctor(db, doctor_id=doctor_id)
    if not db_doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    return db_doctor


@router.put("/{doctor_id}", response_model=Doctor)
def update_doctor(
    doctor_id: int,
    doctor: DoctorUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a doctor.
    
    Args:
        doctor_id: ID of the doctor to update
        doctor: Updated doctor data
        db: Database session
        
    Returns:
        Updated doctor
        
    Raises:
        HTTPException: If doctor not found
    """
    db_doctor = doctor_crud.update_doctor(
        db=db,
        doctor_id=doctor_id,
        doctor=doctor
    )
    if not db_doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    return db_doctor


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a doctor (soft delete).
    
    Args:
        doctor_id: ID of the doctor to delete
        db: Database session
        
    Returns:
        None
        
    Raises:
        HTTPException: If doctor not found
    """
    success = doctor_crud.delete_doctor(db=db, doctor_id=doctor_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        ) 