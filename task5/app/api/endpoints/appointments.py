from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import appointment as appointment_crud
from app.schemas.appointment import Appointment, AppointmentCreate, AppointmentUpdate
from app.models.appointment import AppointmentStatus
from app.dependencies import get_db, get_doctor_by_id, get_patient_by_id

router = APIRouter()


@router.get("/", response_model=List[Appointment])
def read_appointments(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    status: Optional[AppointmentStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Retrieve appointments with optional filtering.
    
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
        List of appointments
    """
    appointments = appointment_crud.get_appointments(
        db,
        skip=skip,
        limit=limit,
        doctor_id=doctor_id,
        patient_id=patient_id,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    return appointments


@router.post("/", response_model=Appointment, status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db),
    doctor: dict = Depends(get_doctor_by_id),
    patient: dict = Depends(get_patient_by_id)
):
    """
    Create a new appointment.
    
    Args:
        appointment: Appointment data to create
        db: Database session
        doctor: Doctor object (from dependency)
        patient: Patient object (from dependency)
        
    Returns:
        Created appointment
        
    Raises:
        HTTPException: If appointment slot is not available
    """
    try:
        return appointment_crud.create_appointment(db=db, appointment=appointment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{appointment_id}", response_model=Appointment)
def read_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific appointment by ID.
    
    Args:
        appointment_id: ID of the appointment to retrieve
        db: Database session
        
    Returns:
        Appointment object
        
    Raises:
        HTTPException: If appointment not found
    """
    db_appointment = appointment_crud.get_appointment(db, appointment_id=appointment_id)
    if not db_appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    return db_appointment


@router.put("/{appointment_id}", response_model=Appointment)
def update_appointment(
    appointment_id: int,
    appointment: AppointmentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an appointment.
    
    Args:
        appointment_id: ID of the appointment to update
        appointment: Updated appointment data
        db: Database session
        
    Returns:
        Updated appointment
        
    Raises:
        HTTPException: If appointment not found or slot is not available
    """
    try:
        db_appointment = appointment_crud.update_appointment(
            db=db,
            appointment_id=appointment_id,
            appointment=appointment
        )
        if not db_appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        return db_appointment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{appointment_id}/cancel", response_model=Appointment)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel an appointment.
    
    Args:
        appointment_id: ID of the appointment to cancel
        db: Database session
        
    Returns:
        Cancelled appointment
        
    Raises:
        HTTPException: If appointment not found
    """
    success = appointment_crud.cancel_appointment(db=db, appointment_id=appointment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    return appointment_crud.get_appointment(db, appointment_id) 