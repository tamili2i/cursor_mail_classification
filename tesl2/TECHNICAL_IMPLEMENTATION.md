# Technical Implementation Guide

## 1. Class Hierarchy and Interfaces

### Core Interfaces

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

# Base Repository Interface
class IRepository(ABC):
    @abstractmethod
    async def create(self, entity: Any) -> Any:
        pass

    @abstractmethod
    async def get(self, id: int) -> Optional[Any]:
        pass

    @abstractmethod
    async def update(self, id: int, entity: Any) -> Any:
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass

# Service Interfaces
class ISeatService(ABC):
    @abstractmethod
    async def allocate_seat(self, employee_id: int, workbench_id: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def deallocate_seat(self, seat_id: int) -> bool:
        pass

    @abstractmethod
    async def get_available_seats(self, floor_id: int) -> List[Dict[str, Any]]:
        pass

class ITeamService(ABC):
    @abstractmethod
    async def create_team(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def assign_employee_to_team(self, employee_id: int, team_id: int) -> bool:
        pass

    @abstractmethod
    async def get_team_members(self, team_id: int) -> List[Dict[str, Any]]:
        pass

class IMeetingService(ABC):
    @abstractmethod
    async def book_room(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def cancel_booking(self, booking_id: int) -> bool:
        pass

    @abstractmethod
    async def get_room_availability(self, room_id: int, date: datetime) -> List[Dict[str, Any]]:
        pass

class IEmployeeService(ABC):
    @abstractmethod
    async def create_employee(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def update_employee_position(self, employee_id: int, position: str) -> bool:
        pass

    @abstractmethod
    async def get_employee_details(self, employee_id: int) -> Dict[str, Any]:
        pass
```

### Domain Models

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Employee(BaseModel):
    id: Optional[int]
    email: str
    first_name: str
    last_name: str
    position: str
    team_id: Optional[int]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Team(BaseModel):
    id: Optional[int]
    name: str
    department: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Seat(BaseModel):
    id: Optional[int]
    workbench_id: int
    user_id: Optional[int]
    seat_number: int
    is_allocated: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MeetingRoom(BaseModel):
    id: Optional[int]
    floor_id: int
    name: str
    capacity: int
    is_special: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Booking(BaseModel):
    id: Optional[int]
    room_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    purpose: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## 2. Method Signatures with Documentation

```python
class SeatService(ISeatService):
    """
    Service for managing seat allocation and deallocation.
    """
    
    async def allocate_seat(self, employee_id: int, workbench_id: int) -> Dict[str, Any]:
        """
        Allocate a seat to an employee at a specific workbench.
        
        Args:
            employee_id: The ID of the employee
            workbench_id: The ID of the workbench
            
        Returns:
            Dict containing the allocation details
            
        Raises:
            SeatAllocationError: If seat allocation fails
            ValidationError: If input parameters are invalid
        """
        pass

    async def deallocate_seat(self, seat_id: int) -> bool:
        """
        Deallocate a seat from an employee.
        
        Args:
            seat_id: The ID of the seat to deallocate
            
        Returns:
            bool: True if deallocation was successful
            
        Raises:
            SeatDeallocationError: If deallocation fails
        """
        pass

    async def get_available_seats(self, floor_id: int) -> List[Dict[str, Any]]:
        """
        Get all available seats on a specific floor.
        
        Args:
            floor_id: The ID of the floor
            
        Returns:
            List of dictionaries containing seat information
            
        Raises:
            FloorNotFoundError: If floor doesn't exist
        """
        pass
```

## 3. Dependency Injection Setup

```python
from fastapi import Depends
from typing import Annotated
from functools import lru_cache

# Configuration
class Settings:
    def __init__(self):
        self.database_url: str = "postgresql://user:pass@localhost/db"
        self.redis_url: str = "redis://localhost:6379"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Database
class Database:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = create_engine(settings.database_url)

def get_db(settings: Annotated[Settings, Depends(get_settings)]) -> Database:
    return Database(settings)

# Services
def get_seat_service(
    db: Annotated[Database, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> ISeatService:
    return SeatService(db, settings)

def get_team_service(
    db: Annotated[Database, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> ITeamService:
    return TeamService(db, settings)
```

## 4. Error Handling Strategy

```python
from fastapi import HTTPException
from typing import Optional

class SeatAllocationError(Exception):
    def __init__(self, message: str, code: str, details: Optional[Dict] = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)

class ErrorHandler:
    @staticmethod
    def handle_seat_allocation_error(error: SeatAllocationError) -> HTTPException:
        return HTTPException(
            status_code=400,
            detail={
                "message": error.message,
                "code": error.code,
                "details": error.details
            }
        )

# Usage in FastAPI
@app.exception_handler(SeatAllocationError)
async def seat_allocation_exception_handler(request: Request, exc: SeatAllocationError):
    return ErrorHandler.handle_seat_allocation_error(exc)
```

## 5. Unit Test Structure

```python
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Test Fixtures
@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def mock_settings():
    return Mock()

@pytest.fixture
def seat_service(mock_db, mock_settings):
    return SeatService(mock_db, mock_settings)

# Test Classes
class TestSeatService:
    async def test_allocate_seat_success(self, seat_service, mock_db):
        # Arrange
        employee_id = 1
        workbench_id = 1
        mock_db.execute.return_value = {"id": 1, "employee_id": employee_id}
        
        # Act
        result = await seat_service.allocate_seat(employee_id, workbench_id)
        
        # Assert
        assert result["id"] == 1
        assert result["employee_id"] == employee_id
        mock_db.execute.assert_called_once()

    async def test_allocate_seat_failure(self, seat_service, mock_db):
        # Arrange
        employee_id = 1
        workbench_id = 1
        mock_db.execute.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(SeatAllocationError):
            await seat_service.allocate_seat(employee_id, workbench_id)

class TestTeamService:
    async def test_create_team_success(self, team_service, mock_db):
        # Arrange
        team_data = {"name": "Engineering", "department": "IT"}
        mock_db.execute.return_value = {"id": 1, **team_data}
        
        # Act
        result = await team_service.create_team(team_data)
        
        # Assert
        assert result["id"] == 1
        assert result["name"] == team_data["name"]
        mock_db.execute.assert_called_once()
```

## 6. FastAPI Route Implementation

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter()

@router.post("/seats/allocate")
async def allocate_seat(
    employee_id: int,
    workbench_id: int,
    seat_service: Annotated[ISeatService, Depends(get_seat_service)]
):
    try:
        return await seat_service.allocate_seat(employee_id, workbench_id)
    except SeatAllocationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/seats/available/{floor_id}")
async def get_available_seats(
    floor_id: int,
    seat_service: Annotated[ISeatService, Depends(get_seat_service)]
):
    try:
        return await seat_service.get_available_seats(floor_id)
    except FloorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

## 7. Configuration Management

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str
    REDIS_TTL: int = 3600
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    
    class Config:
        env_file = ".env"
```

This implementation follows SOLID principles and includes:
- Single Responsibility Principle: Each class has a single responsibility
- Open/Closed Principle: New functionality can be added without modifying existing code
- Liskov Substitution Principle: Interfaces can be replaced with their implementations
- Interface Segregation: Small, specific interfaces
- Dependency Inversion: High-level modules depend on abstractions

The code is designed to be:
- Testable: All dependencies can be mocked
- Maintainable: Clear separation of concerns
- Scalable: Modular design allows for easy expansion
- Secure: Proper error handling and input validation 