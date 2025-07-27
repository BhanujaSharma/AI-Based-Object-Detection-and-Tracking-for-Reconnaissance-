from pymongo import MongoClient
from passlib.context import CryptContext

# Setup MongoDB connection (USE YOUR ACTUAL URI BELOW)
client = MongoClient("mongodb+srv://bhanujasharma2223:bRh51nQwd9UooE5C@majorproject.elha1mu.mongodb.net/?retryWrites=true&w=majority&appName=MajorProject")
db = client["ai_recon_tracking"]
users_col = db["users"]

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define the new user credentials
username = "admin1"
password = "admin123"
zone = "zone_a"  # this zone will be used to filter logs

# Hash the password securely
hashed_password = pwd_context.hash(password)

# Insert into MongoDB
users_col.insert_one({
    "username": username,
    "password": hashed_password,
    "zone": zone
})

print(f"✅ Admin user '{username}' added successfully.")
