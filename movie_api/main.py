from fastapi import FastAPI,Query
from movie_api.db import users_col, movies_col, watch_col, reviews_col
from fuzzywuzzy import fuzz
from rapidfuzz import process,fuzz
from datetime import datetime, timedelta
from bson import ObjectId, errors
from fastapi import HTTPException


app = FastAPI()





# ✅ Helper: Convert ObjectId to string
def serialize_doc(doc):
    doc["_id"] = str(doc["_id"])
    return doc


# ✅ 1. Keyword search (title, director, cast)
@app.get("/movies/search/keyword")
def keyword_search(keyword: str = Query(..., description="Search movies by title, director, or cast"), limit: int = 10):
    try:
        query = {
            "$or": [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"directors": {"$elemMatch": {"$regex": keyword, "$options": "i"}}},
                {"cast": {"$elemMatch": {"$regex": keyword, "$options": "i"}}}
            ]
        }
        results = list(movies_col.find(query).limit(limit))
        return {"results": [serialize_doc(r) for r in results]}
    except Exception as e:
        print("ERROR in /movies/search/keyword:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/movies/search/fuzzy")
def fuzzy_search(query: str, limit: int = 10):
    try:
        # First, use MongoDB text search to narrow results
        text_results = list(movies_col.find(
            {"$text": {"$search": query}},
            {"title": 1, "rating": 1, "watchCount": 1}
        ).limit(100))  # Get top 100 candidates first

        if not text_results:
            # Fallback: fetch all only if text search returns nothing
            text_results = list(movies_col.find({}, {"title": 1, "rating": 1, "watchCount": 1}))

        titles = [m["title"] for m in text_results]
        matches = process.extract(query, titles, scorer=fuzz.token_sort_ratio, limit=limit)

        results = []
        for title, score, _ in matches:
            movie = next((m for m in text_results if m["title"] == title), None)
            if movie:
                movie["similarity"] = round(score / 100, 2)
                results.append(serialize_doc(movie))

        return {"results": results}
    except Exception as e:
        print("ERROR in /movies/search/fuzzy:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/movies/search/hybrid")
def hybrid_search(query: str, limit: int = 10):
    try:
        # Use keyword search first to reduce dataset
        keyword_query = {
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"directors": {"$elemMatch": {"$regex": query, "$options": "i"}}},
                {"cast": {"$elemMatch": {"$regex": query, "$options": "i"}}}
            ]
        }
        movies = list(movies_col.find(keyword_query).limit(100))

        if not movies:
            return {"results": []}

        max_watch = max([m.get("watchCount", 0) for m in movies], default=1)
        results = []

        for m in movies:
            title = m.get("title", "")
            rating = float(m.get("rating", 0) or 0)
            watch_count = int(m.get("watchCount", 0) or 0)

            title_score = fuzz.partial_ratio(query.lower(), title.lower()) / 100
            rating_score = rating / 10
            popularity_score = watch_count / max_watch if max_watch > 0 else 0

            total_score = (0.5 * title_score) + (0.3 * rating_score) + (0.2 * popularity_score)
            m["hybrid_score"] = round(total_score, 3)
            results.append(serialize_doc(m))

        results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return {"results": results[:limit]}
    except Exception as e:
        print("ERROR in /movies/search/hybrid:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# ✅ 4. User watch history
@app.get("/users/{user_id}/history")
def user_history(user_id: str):
    try:
        obj_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    try:
        history = list(watch_col.find({"user_id": obj_id}))
        if not history:
            return {"message": "No watch history available for this user."}

        result = []
        for h in history:
            movie = movies_col.find_one({"_id": h.get("movie_id")})
            result.append({
                "movie_id": str(h.get("movie_id")),
                "title": movie.get("title") if movie else "Unknown",
                "watch_duration": h.get("watch_duration", 0),
                "completed": h.get("completed", False),
                "timestamp": h.get("timestamp")
            })
        return result
    except Exception as e:
        print("ERROR in /users/{user_id}/history:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/movies/{movie_id}/reviews")
def movie_reviews(movie_id: str):
    try:
        try:
            obj_id = ObjectId(movie_id)
        except (errors.InvalidId, TypeError):
            raise HTTPException(status_code=400, detail="Invalid movie ID format")

        review_docs = list(reviews_col.find({"movie_id": obj_id}))

        if not review_docs:
            return {"message": "No reviews found for this movie."}

        result = []
        for r in review_docs:
            user = users_col.find_one({"_id": r.get("user_id")})
            rating = float(r.get("rating", 0) or 0)
            result.append({
                "review_id": str(r["_id"]),
                "user_id": str(r.get("user_id")),
                "user_name": user.get("name") if user else "Unknown",
                "rating": rating,
                "text_review": r.get("text_review", ""),
                "created_at": r.get("created_at"),
                "helpful_count": r.get("helpful_count", 0)
            })
        return result

    except Exception as e:
        print("ERROR in /movies/{movie_id}/reviews:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/movies/top-monthly")
def top_movies_last_month(limit: int = 5):
    try:
        one_month_ago = datetime.now() - timedelta(days=30)

        pipeline = [
            {"$match": {"timestamp": {"$gte": one_month_ago}}},
            {"$group": {"_id": "$movie_id", "watchCount": {"$sum": 1}}},
            {"$sort": {"watchCount": -1}},
            {"$limit": limit},
            {"$lookup": {
                "from": "movies",
                "localField": "_id",
                "foreignField": "_id",
                "as": "movie"
            }},
            {"$unwind": "$movie"},
            {"$project": {
                "_id": 0,
                "movie_id": {"$toString": "$movie._id"},
                "title": "$movie.title",
                "watchCount": 1
            }}
        ]

        top_movies = list(watch_col.aggregate(pipeline))
        return {"results": top_movies}

    except Exception as e:
        print("ERROR in /movies/top-monthly:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/movies/watch-counts")
def all_movies_watch_counts():
    try:
        one_month_ago = datetime.now() - timedelta(days=30)

        # Aggregation: count watches per movie in last month
        pipeline = [
            {"$match": {"timestamp": {"$gte": one_month_ago}}},
            {"$group": {"_id": "$movie_id", "watchCount": {"$sum": 1}}},
            {"$lookup": {
                "from": "movies",
                "localField": "_id",
                "foreignField": "_id",
                "as": "movie"
            }},
            {"$unwind": "$movie"},
            {"$project": {
                "_id": 0,
                "movie_id": {"$toString": "$movie._id"},
                "title": "$movie.title",
                "watchCount": 1
            }},
            {"$sort": {"watchCount": -1}}  # descending order
        ]

        results = list(watch_col.aggregate(pipeline))
        return {"results": results}

    except Exception as e:
        print("ERROR in /movies/watch-counts:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# ✅ Fetch all users
@app.get("/users")
def get_all_users():
    try:
        users = list(users_col.find({}, {"name": 1, "email": 1, "subscription": 1}))
        return {"results": [serialize_doc(u) for u in users]}
    except Exception as e:
        print("ERROR in /users:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

