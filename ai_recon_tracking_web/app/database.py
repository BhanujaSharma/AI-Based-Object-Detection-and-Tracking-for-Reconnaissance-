from pymongo import MongoClient
import gridfs

# Connect to MongoDB
client = MongoClient("your connection string")
db = client["ai_recon_tracking"]

# Define the collection you're using
collection = db["detections"]  # <--- Add this line

# GridFS for storing images
fs = gridfs.GridFS(db)

# Also keep other collections if needed
users_col = db["users"]
