from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

class Movie(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    title: str
    year: int
    genres: List[str]
    cast: List[str]
    directors: List[str]
    rating: float
    watchCount: int = 0

    class Config:
        orm_mode = True
        populate_by_name = True


class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    email: EmailStr
    subscriptionType: str

    class Config:
        orm_mode = True
        populate_by_name = True


class WatchHistory(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    movie_id: str
    timestamp: datetime
    watch_duration: str
    completed: bool

    class Config:
        orm_mode = True
        populate_by_name = True


class Review(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    movie_id: str
    rating: float
    text_review: str
    created_at: datetime
    helpful_count: int

    class Config:
        orm_mode = True
        populate_by_name = True
