# app/auth.py
from app.database import users_col
from passlib.context import CryptContext

# Setup password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def authenticate_user(username: str, password: str):
    user = users_col.find_one({"username": username})
    if not user:
        return None
    if pwd_context.verify(password, user["password"]):
        return user
    return None
