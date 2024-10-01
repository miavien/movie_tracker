import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from .models import *

logger = logging.getLogger(__name__)


async def set_user(session: AsyncSession, tg_id: int, username: str, full_name: str) -> Optional[User]:
    try:
        user = await session.scalar(select(User).filter_by(telegram_id=tg_id))

        if not user:
            new_user = User(telegram_id=tg_id, username=username, full_name=full_name)
            session.add(new_user)
            await session.commit()
            logger.info(f'Зарегистрировал пользователя с ID {tg_id}!')
            return new_user
        else:
            logger.info(f'Пользователь с ID {tg_id} найден!')
    except SQLAlchemyError as e:
        logger.error(f'Ошибка при добавлении пользователя: {e}')
        await session.rollback()
        return None


async def add_movie(session: AsyncSession, title: str, description: str, telegram_id: int) -> Optional[Movie]:
    user = await session.scalar(select(User).filter_by(telegram_id=telegram_id))
    try:
        new_movie = Movie(title=title, description=description, user_id=user.id)
        session.add(new_movie)
        await session.commit()
        logger.info(f'Добавили фильм пользователю с Telegram ID {telegram_id}!')
        return new_movie
    except SQLAlchemyError as e:
        logger.error(f'Ошибка при добавлении фильма: {e}')
        await session.rollback()
        return None


async def add_review(session: AsyncSession, telegram_id: int, movie_id: int, rating: int, comment: str) -> Optional[Review]:
    user = await session.scalar(select(User).filter_by(telegram_id=telegram_id))
    movie = await session.get(Movie, movie_id)
    try:
        new_review = Review(user_id=user.id, movie_id=movie.id, rating=rating, comment=comment)
        session.add(new_review)
        await session.commit()
        logger.info(f'Добавили рецензию пользователю с Telegram ID {telegram_id}!')
        return new_review
    except SQLAlchemyError as e:
        logger.error(f'Ошибка при добавлении рецензии: {e}')
        await session.rollback()
        return None