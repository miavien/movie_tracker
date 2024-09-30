from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, List, Text, func, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

class User(BaseModel):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    movies: Mapped[List['Movie']] = relationship('Movie', back_populates='user', cascade='all, delete-orphan')
    reviews: Mapped[List['Review']] = relationship('Review', back_populates='user', cascade='all, delete-orphan')

class Movie(BaseModel):
    __tablename__ = 'movies'

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    release_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)

    user: Mapped['User'] = relationship('User', back_populates='movies', cascade='all, delete-orphan')
    review: Mapped[Optional['Review']] = relationship('Review', back_populates='movie', cascade='all, delete-orphan')

class Review(BaseModel):
    __tablename__ = 'reviews'

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey('movies.id'), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped['User'] = relationship('User', back_populates='review')
    movie: Mapped['Movie'] = relationship('Movie', back_populates='review')