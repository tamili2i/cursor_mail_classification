from .models import UserCreate, UserRead, UserInDB
from .core.security import verify_password

# In-memory "database"
fake_db = {}

def create_user(user: UserCreate) -> UserRead:
    user_id = len(fake_db) + 1
    user_db = UserInDB(id=user_id, email=user.email, hashed_password=user.password + "notreallyhashed")
    fake_db[user_id] = user_db
    return UserRead(id=user_id, email=user.email)

def get_user(user_id: int) -> UserRead:
    user = fake_db.get(user_id)
    if user:
        return UserRead(id=user.id, email=user.email)
    return None

def authenticate_user(email: str, password: str):
    # Replace this with your actual user lookup logic
    for user in fake_db.values():
        if user.email == email and verify_password(password, user.hashed_password):
            return user
    return None