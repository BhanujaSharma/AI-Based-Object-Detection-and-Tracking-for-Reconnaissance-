from pymongo import MongoClient
from gridfs import GridFS

# ✅ Use your actual Atlas URI directly
MONGO_URI = "mongodb+srv://bhanujasharma2223:bRh51nQwd9UooE5C@majorproject.elha1mu.mongodb.net/?retryWrites=true&w=majority&appName=MajorProject"

client = MongoClient(MONGO_URI)
db = client["ai_recon_tracking"]

# Collections
collection = db["detections"]
users_col = db["users"]
fs = GridFS(db)
