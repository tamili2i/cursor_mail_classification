import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.config import settings
from app.services.user import (
    get_user,
    get_user_by_email,
    get_user_by_username,
    get_users,
    create_user,
    update_user,
    delete_user,
    authenticate_user
)
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import create_access_token
from app.models.user import User

client = TestClient(app)

# Test data
TEST_USER_DATA = {
    "email": "integration@test.com",
    "username": "integration_test",
    "password": "Test@123",
    "full_name": "Integration Test User"
}

@pytest.fixture
def test_user(db: Session):
    """Fixture to create a test user"""
    user_in = UserCreate(**TEST_USER_DATA)
    user = create_user(db, user_in)
    yield user
    # Cleanup
    db.delete(user)
    db.commit()

@pytest.fixture
def auth_headers(test_user):
    """Fixture to create authentication headers"""
    access_token = create_access_token(test_user.email)
    return {"Authorization": f"Bearer {access_token}"}

class TestUserServiceIntegration:
    def test_create_user_success(self, db: Session):
        """Test successful user creation with database interaction"""
        # Arrange
        user_in = UserCreate(**TEST_USER_DATA)
        
        # Act
        user = create_user(db, user_in)
        
        # Assert
        assert user.email == TEST_USER_DATA["email"]
        assert user.username == TEST_USER_DATA["username"]
        assert user.full_name == TEST_USER_DATA["full_name"]
        assert user.is_active is True
        
        # Verify database persistence
        db_user = get_user_by_email(db, TEST_USER_DATA["email"])
        assert db_user is not None
        assert db_user.id == user.id

    def test_create_user_duplicate_email(self, db: Session, test_user):
        """Test user creation with duplicate email"""
        # Arrange
        user_in = UserCreate(**TEST_USER_DATA)
        
        # Act & Assert
        with pytest.raises(Exception):
            create_user(db, user_in)

    def test_get_user_by_email(self, db: Session, test_user):
        """Test retrieving user by email"""
        # Act
        user = get_user_by_email(db, TEST_USER_DATA["email"])
        
        # Assert
        assert user is not None
        assert user.email == TEST_USER_DATA["email"]
        assert user.username == TEST_USER_DATA["username"]

    def test_get_user_by_username(self, db: Session, test_user):
        """Test retrieving user by username"""
        # Act
        user = get_user_by_username(db, TEST_USER_DATA["username"])
        
        # Assert
        assert user is not None
        assert user.username == TEST_USER_DATA["username"]
        assert user.email == TEST_USER_DATA["email"]

    def test_update_user(self, db: Session, test_user):
        """Test user update functionality"""
        # Arrange
        update_data = UserUpdate(
            full_name="Updated Name",
            password="NewPassword@123"
        )
        
        # Act
        updated_user = update_user(db, test_user.id, update_data)
        
        # Assert
        assert updated_user is not None
        assert updated_user.full_name == "Updated Name"
        assert updated_user.id == test_user.id

    def test_delete_user(self, db: Session, test_user):
        """Test user deletion"""
        # Act
        result = delete_user(db, test_user.id)
        
        # Assert
        assert result is True
        deleted_user = get_user(db, test_user.id)
        assert deleted_user is None

    def test_authenticate_user(self, db: Session, test_user):
        """Test user authentication"""
        # Act
        authenticated_user = authenticate_user(
            db,
            TEST_USER_DATA["email"],
            TEST_USER_DATA["password"]
        )
        
        # Assert
        assert authenticated_user is not None
        assert authenticated_user.id == test_user.id

    def test_authenticate_user_wrong_password(self, db: Session, test_user):
        """Test authentication with wrong password"""
        # Act
        authenticated_user = authenticate_user(
            db,
            TEST_USER_DATA["email"],
            "wrong_password"
        )
        
        # Assert
        assert authenticated_user is None

class TestUserServiceErrorHandling:
    def test_database_connection_error(self, db: Session):
        """Test handling of database connection errors"""
        # Arrange
        with patch.object(db, 'commit', side_effect=SQLAlchemyError):
            user_in = UserCreate(**TEST_USER_DATA)
            
            # Act & Assert
            with pytest.raises(SQLAlchemyError):
                create_user(db, user_in)

    def test_get_users_pagination(self, db: Session):
        """Test pagination with invalid parameters"""
        # Act
        users = get_users(db, skip=-1, limit=0)
        
        # Assert
        assert isinstance(users, list)
        assert len(users) == 0

class TestUserServiceAPI:
    def test_create_user_endpoint(self, db: Session):
        """Test user creation through API endpoint"""
        # Arrange
        user_data = {
            "email": "api_test@example.com",
            "username": "api_test_user",
            "password": "ApiTest@123",
            "full_name": "API Test User"
        }
        
        # Act
        response = client.post(
            f"{settings.API_V1_STR}/users/",
            json=user_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        
        # Cleanup
        user = get_user_by_email(db, user_data["email"])
        if user:
            db.delete(user)
            db.commit()

    def test_get_user_endpoint(self, db: Session, test_user, auth_headers):
        """Test user retrieval through API endpoint"""
        # Act
        response = client.get(
            f"{settings.API_V1_STR}/users/{test_user.id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    def test_update_user_endpoint(self, db: Session, test_user, auth_headers):
        """Test user update through API endpoint"""
        # Arrange
        update_data = {
            "full_name": "Updated via API",
            "password": "NewApiPassword@123"
        }
        
        # Act
        response = client.put(
            f"{settings.API_V1_STR}/users/{test_user.id}",
            headers=auth_headers,
            json=update_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["id"] == test_user.id

    def test_delete_user_endpoint(self, db: Session, test_user, auth_headers):
        """Test user deletion through API endpoint"""
        # Act
        response = client.delete(
            f"{settings.API_V1_STR}/users/{test_user.id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        
        # Verify deletion
        deleted_user = get_user(db, test_user.id)
        assert deleted_user is None 