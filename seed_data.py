from pymongo import MongoClient
from datetime import datetime
import random

client = MongoClient("mongodb://localhost:27017")
db = client["movieDB"]

users_col = db["users"]
movies_col = db["movies"]
watch_col = db["watchHistory"]
reviews_col = db["reviews"]

users_col.delete_many({})
movies_col.delete_many({})
watch_col.delete_many({})
reviews_col.delete_many({})

users = [
    {"name": "Alice", "email": "alice@example.com", "subscription": "premium"},
    {"name": "Bob", "email": "bob@example.com", "subscription": "basic"},
]
users_col.insert_many(users)

movies = [
    {"title": "The Godfather", "year": 1972, "genres": ["Crime", "Drama"], "cast": ["Marlon Brando"], "directors": ["Francis Ford Coppola"], "rating": 9.2},
    {"title": "Inception", "year": 2010, "genres": ["Action", "Sci-Fi"], "cast": ["Leonardo DiCaprio"], "directors": ["Christopher Nolan"], "rating": 8.8}
]
movies_col.insert_many(movies)

watch_col.insert_many([
    {"user_id": users[0]["_id"], "movie_id": movies[0]["_id"], "timestamp": datetime.now(), "watch_duration": "120 min", "completed": True},
    {"user_id": users[1]["_id"], "movie_id": movies[1]["_id"], "timestamp": datetime.now(), "watch_duration": "130 min", "completed": True},
])

reviews_col.insert_many([
    {"user_id": users[0]["_id"], "movie_id": movies[0]["_id"], "rating": 9, "text_review": "Amazing movie!", "created_at": datetime.now(), "helpful_count": 5},
    {"user_id": users[1]["_id"], "movie_id": movies[1]["_id"], "rating": 8.5, "text_review": "Mind-blowing!", "created_at": datetime.now(), "helpful_count": 3},
])

print("✅ Sample data inserted successfully!")
