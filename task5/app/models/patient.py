from datetime import datetime
from typing import List
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Date
from sqlalchemy.orm import relationship

from app.core.database import Base


class Patient(Base):
    """Patient model for storing patient information."""
    
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    appointments = relationship("Appointment", back_populates="patient") 