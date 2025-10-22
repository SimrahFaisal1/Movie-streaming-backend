from pymongo import MongoClient

# Connect to your local MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["movieDB"]

# Collections
users_col = db["users"]
movies_col = db["movies"]
watch_col = db["watchHistory"]
reviews_col = db["reviews"]
