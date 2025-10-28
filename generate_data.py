from pymongo import MongoClient
from datetime import datetime, timedelta
import random

client = MongoClient("mongodb://localhost:27017")
db = client["movieDB"]

users_col = db["users"]
movies_col = db["movies"]
watch_col = db["watchHistory"]
reviews_col = db["reviews"]

users = list(users_col.find({}))
user_ids = [u["_id"] for u in users]

movies = list(movies_col.find({}, {"_id": 1, "title": 1}))
movie_ids = [m["_id"] for m in movies]

watch_history = []
reviews = []

sample_texts = [
    "Amazing movie!", "Really enjoyed it.", "Could be better.",
    "Loved the storyline.", "Not my type.", "Fantastic acting!",
    "Interesting plot.", "Would watch again.", "Too long for my taste.",
    "A classic!","too boring","nepo kids ruined this"
]

popular_movies = random.sample(movie_ids, k=min(5, len(movie_ids)))

movie_watch_counts = {}
for movie_id in movie_ids:
    if movie_id in popular_movies:
        movie_watch_counts[movie_id] = random.randint(15, 30)  
    else:
        movie_watch_counts[movie_id] = random.randint(1, 7)    
reviewed_pairs = set()

def generate_random_timestamp():
    day_offset = random.randint(0, 29)
    hour = random.randint(19, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    random_date = datetime.now() - timedelta(days=day_offset)
    random_date = random_date.replace(hour=hour, minute=minute, second=second, microsecond=0)
    return random_date

# Helper: generate watch duration in "X min Y sec"
def generate_watch_duration():
    minutes = random.randint(5, 180)
    seconds = random.randint(0, 59)
    return f"{minutes} min {seconds} sec"

for movie_id, count in movie_watch_counts.items():
    for _ in range(count):
        user_id = random.choice(user_ids)
        timestamp = generate_random_timestamp()
        duration_str = generate_watch_duration()

        watch_history.append({
            "user_id": user_id,
            "movie_id": movie_id,
            "timestamp": timestamp,
            "watch_duration": duration_str,
            "completed": random.choice([True, False])
        })

        if (user_id, movie_id) not in reviewed_pairs and random.random() > 0.5:
            rating = round(random.uniform(1, 10), 1)  # float rating 1-10
            text_review = random.choice(sample_texts)
            reviews.append({
                "user_id": user_id,
                "movie_id": movie_id,
                "rating": rating,
                "text_review": text_review,
                "created_at": timestamp,
                "helpful_count": random.randint(0, 20)
            })
            reviewed_pairs.add((user_id, movie_id))

if watch_history:
    watch_col.insert_many(watch_history)
if reviews:
    reviews_col.insert_many(reviews)

trending_titles = [m['title'] for m in movies if m['_id'] in popular_movies]

print(f"✅ Generated {len(watch_history)} watch history records")
print(f"✅ Generated {len(reviews)} reviews")
print("Watch history and reviews generated successfully!")
print(f"Trending movies: {trending_titles}")
