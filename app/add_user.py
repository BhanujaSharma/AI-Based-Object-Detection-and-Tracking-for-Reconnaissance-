from pymongo import MongoClient
from passlib.context import CryptContext

# Connect to your MongoDB Atlas instance
client = MongoClient("mongodb+srv://bhanujasharma2223:bRh51nQwd9UooE5C@majorproject.elha1mu.mongodb.net/?retryWrites=true&w=majority&appName=MajorProject")
db = client["ai_recon_tracking"]
users_col = db["users"]

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define the new user credentials
username = "admin1"
password = "admin123"
zone = "zone_a"
role = "admin"  # ✅ include this to make the user an admin

# Hash the password securely
hashed_password = pwd_context.hash(password)

# Insert user into MongoDB
users_col.insert_one({
    "username": username,
    "password": hashed_password,
    "zone": zone,
    "role": role   # ✅ critical for dashboard access and permissions
})

print(f"✅ Admin user '{username}' added successfully.")
