from passlib.context import CryptContext
from app.database import users_col

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    user = users_col.find_one({"username": username})
    if not user:
        return None
    if pwd_context.verify(password, user["password"]):
        print("User found:", user)

        return user
    return None
