from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.config import settings
from app.services.user import create_user
from app.schemas.user import UserCreate
from app.core.security import create_access_token

client = TestClient(app)

def test_create_user(db: Session):
    user_in = UserCreate(
        email="test@example.com",
        username="testuser",
        password="testpassword123",
        full_name="Test User"
    )
    user = create_user(db, user_in)
    assert user.email == user_in.email
    assert user.username == user_in.username
    assert user.full_name == user_in.full_name

def test_get_user(db: Session):
    user_in = UserCreate(
        email="test2@example.com",
        username="testuser2",
        password="testpassword123",
        full_name="Test User 2"
    )
    user = create_user(db, user_in)
    
    access_token = create_access_token(user.email)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email
    assert data["username"] == user.username

def test_update_user(db: Session):
    user_in = UserCreate(
        email="test3@example.com",
        username="testuser3",
        password="testpassword123",
        full_name="Test User 3"
    )
    user = create_user(db, user_in)
    
    access_token = create_access_token(user.email)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    update_data = {
        "full_name": "Updated Test User",
        "password": "newpassword123"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
        json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == update_data["full_name"]

def test_read_users_success(db: Session):
    # Arrange
    # Create multiple test users
    users = []
    for i in range(3):
        user_in = UserCreate(
            email=f"test{i}@example.com",
            username=f"testuser{i}",
            password="testpassword123",
            full_name=f"Test User {i}"
        )
        user = create_user(db, user_in)
        users.append(user)
    
    # Create a superuser for authentication
    superuser_in = UserCreate(
        email="super@example.com",
        username="superuser",
        password="superpassword123",
        full_name="Super User",
        is_superuser=True
    )
    superuser = create_user(db, superuser_in)
    
    access_token = create_access_token(superuser.email)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Act
    response = client.get(f"{settings.API_V1_STR}/users/", headers=headers)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # Should return at least our test users
    assert all("email" in user for user in data)
    assert all("username" in user for user in data)

def test_read_users_pagination(db: Session):
    # Arrange
    # Create 5 test users
    for i in range(5):
        user_in = UserCreate(
            email=f"pagination{i}@example.com",
            username=f"paginationuser{i}",
            password="testpassword123",
            full_name=f"Pagination User {i}"
        )
        create_user(db, user_in)
    
    superuser_in = UserCreate(
        email="super2@example.com",
        username="superuser2",
        password="superpassword123",
        full_name="Super User 2",
        is_superuser=True
    )
    superuser = create_user(db, superuser_in)
    
    access_token = create_access_token(superuser.email)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Act - Test with skip=2, limit=2
    response = client.get(
        f"{settings.API_V1_STR}/users/?skip=2&limit=2",
        headers=headers
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Should return exactly 2 users

def test_read_users_boundary_values(db: Session):
    # Arrange
    superuser_in = UserCreate(
        email="super3@example.com",
        username="superuser3",
        password="superpassword123",
        full_name="Super User 3",
        is_superuser=True
    )
    superuser = create_user(db, superuser_in)
    
    access_token = create_access_token(superuser.email)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Act & Assert - Test with skip=0, limit=0
    response = client.get(
        f"{settings.API_V1_STR}/users/?skip=0&limit=0",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0  # Should return empty list with limit=0
    
    # Act & Assert - Test with large skip value
    response = client.get(
        f"{settings.API_V1_STR}/users/?skip=1000",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0  # Should return empty list with large skip

def test_read_users_unauthorized():
    # Act - Try to access without authentication
    response = client.get(f"{settings.API_V1_STR}/users/")
    
    # Assert
    assert response.status_code == 401  # Unauthorized

def test_read_users_forbidden(db: Session):
    # Arrange
    # Create a regular user (non-superuser)
    user_in = UserCreate(
        email="regular@example.com",
        username="regularuser",
        password="testpassword123",
        full_name="Regular User"
    )
    user = create_user(db, user_in)
    
    access_token = create_access_token(user.email)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Act - Try to access with non-superuser
    response = client.get(f"{settings.API_V1_STR}/users/", headers=headers)
    
    # Assert
    assert response.status_code == 403  # Forbidden 