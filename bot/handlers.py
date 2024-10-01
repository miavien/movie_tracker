from aiogram import types, Router, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import delete

from database.crud import *
from database.database import AsyncSessionLocal
from .keyboards import *

router = Router()


class MovieStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()


class ReviewStates(StatesGroup):
    waiting_for_movie = State()
    waiting_for_selected_movie = State()
    waiting_for_rating = State()
    waiting_for_comment = State()


class DeleteMovieStates(StatesGroup):
    waiting_for_movie_to_delete = State()
    waiting_for_confirmation = State()
    waiting_for_selected_movie = State()


class UpdateReviewStates(StatesGroup):
    waiting_for_movie_edit = State()
    waiting_for_new_rating = State()
    waiting_for_new_comment = State()
    waiting_for_selected_movie = State()


async def find_and_send_movies(session, message: types.Message, partial_title: str, state: FSMContext):
    movies = await session.scalars(select(Movie).filter(Movie.title.ilike(f'%{partial_title}%')))
    movie_titles = [movie.title for movie in movies]

    if movie_titles:
        movies_message = f'Найдены следующие фильмы:\n' + '\n'.join(
            movie_titles) + '\nПожалуйста, выберите фильм из списка:'
        await message.answer(movies_message)
        await state.update_data(movie_titles=movie_titles)
    else:
        await message.answer('Фильмы не найдены. Пожалуйста, попробуйте снова.',
                             reply_markup=main_menu_keyboard)


@router.message(lambda message: message.text == '⚙️ Ещё...')
async def show_additional_menu(message: types.Message):
    await message.answer('Выберите опцию:', reply_markup=additional_menu_keyboard)


@router.message(lambda message: message.text == '🔙 Назад')
async def go_back_to_main_menu(message: types.Message):
    await message.answer('Вы вернулись в основное меню:', reply_markup=main_menu_keyboard)


@router.message(Command(commands=['start']))
async def start(message: types.Message):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            user = await set_user(session, message.from_user.id, message.from_user.username,
                                  message.from_user.full_name)
    await message.answer(
        'Привет! Я помогу тебе хранить заметки о просмотренных фильмах и оставлять к ним отзывы',
        reply_markup=main_menu_keyboard
    )


@router.message(lambda message: message.text == '🎥 Добавить фильм')
async def add_movie_handler(message: types.Message, state: FSMContext):
    await message.answer('Введите название фильма:')
    await state.set_state(MovieStates.waiting_for_title)


@router.message(MovieStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    title = message.text
    await state.update_data(title=title)
    await message.answer('Введите описание фильма:')
    await state.set_state(MovieStates.waiting_for_description)


@router.message(MovieStates.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    description = message.text
    user_data = await state.get_data()
    title = user_data.get('title')

    async with AsyncSessionLocal() as session:
        async with session.begin():
            telegram_id = message.from_user.id
            movie = await add_movie(session, title, description, telegram_id)

    if movie:
        await message.answer(f"Фильм '{title}' успешно добавлен!", reply_markup=main_menu_keyboard)
    else:
        await message.answer('Произошла ошибка при добавлении фильма. Попробуйте снова.',
                             reply_markup=main_menu_keyboard)

    await state.clear()


@router.message(lambda message: message.text == '🗒️ Добавить рецензию')
async def add_review_handler(message: types.Message, state: FSMContext):
    await message.answer('Введите название фильма:')
    await state.set_state(ReviewStates.waiting_for_movie)


@router.message(ReviewStates.waiting_for_movie)
async def process_movie(message: types.Message, state: FSMContext):
    movie_title = message.text
    async with AsyncSessionLocal() as session:
        movies = await session.scalars(select(Movie).filter(Movie.title.ilike(f'%{movie_title}%')))
        movies_without_review = []
        for movie in movies:
            review = await session.scalar(select(Review).filter_by(movie_id=movie.id))
            if not review:
                movies_without_review.append(movie)

    if movies_without_review:
        movie_titles = [movie.title for movie in movies_without_review]
        await message.answer(
            f'Найдены следующие фильмы:\n' + '\n'.join(movie_titles) + '\nПожалуйста, выберите фильм из списка:')
        await state.update_data(movie_titles=movie_titles)
        await state.set_state(ReviewStates.waiting_for_selected_movie)
    else:
        await message.answer('Недоступный фильм для добавления рецензии.',
                             reply_markup=main_menu_keyboard)
        await state.clear()


@router.message(ReviewStates.waiting_for_selected_movie)
async def process_selected_movie(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    movie_titles = user_data.get('movie_titles', [])
    selected_title = message.text

    if selected_title in movie_titles:
        await state.update_data(selected_title=selected_title)
        await message.answer('Вы выбрали фильм. Пожалуйста, введите ваш рейтинг (от 1 до 5):')
        await state.set_state(ReviewStates.waiting_for_rating)
    else:
        await message.answer('Ошибка: выбранный фильм не найден в списке. Пожалуйста, попробуйте снова.',
                             reply_markup=main_menu_keyboard)
        await state.clear()


@router.message(ReviewStates.waiting_for_rating)
async def process_rating(message: types.Message, state: FSMContext):
    rating = message.text
    user_data = await state.get_data()
    selected_title = user_data.get('selected_title')

    if rating.isdigit() and 1 <= int(rating) <= 5:
        await state.update_data(rating=int(rating))
        await message.answer('Пожалуйста, введите ваш комментарий к фильму:')
        await state.set_state(ReviewStates.waiting_for_comment)
    else:
        await message.answer('Пожалуйста, введите корректный рейтинг (от 1 до 5).',
                             reply_markup=main_menu_keyboard)
    await state.clear()


@router.message(ReviewStates.waiting_for_comment)
async def process_comment(message: types.Message, state: FSMContext):
    comment = message.text
    user_data = await state.get_data()
    selected_title = user_data.get('selected_title')
    rating = user_data.get('rating')

    async with AsyncSessionLocal() as session:
        movie = await session.scalar(select(Movie).filter_by(title=selected_title))
        if movie:
            review = await add_review(session, message.from_user.id, movie.id, rating, comment)
            if review:
                await message.answer('Ваш отзыв успешно добавлен! 🎉',
                                     reply_markup=main_menu_keyboard)
            else:
                await message.answer('Произошла ошибка при добавлении отзыва. Попробуйте снова.',
                                     reply_markup=main_menu_keyboard)
        else:
            await message.answer('Ошибка: фильм не найден.',
                                 reply_markup=main_menu_keyboard)

    await state.clear()


@router.message(lambda message: message.text == '🧡 Просмотреть список фильмов')
async def get_my_movies_handler(message: types.Message):
    await message.answer('Получаю список ваших фильмов и отзывов...')
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        result, user = await get_movies_and_reviews(session, telegram_id)
    movies_info = await format_movies_info(result)
    await message.answer(movies_info, reply_markup=main_menu_keyboard)


@router.message(lambda message: message.text == '❌ Удалить фильм')
async def delete_movie_handler(message: types.Message, state: FSMContext):
    await message.answer('Введите название фильма для удаления:')
    await state.set_state(DeleteMovieStates.waiting_for_movie_to_delete)


@router.message(DeleteMovieStates.waiting_for_movie_to_delete)
async def process_movie_deletion(message: types.Message, state: FSMContext):
    movie_title = message.text
    async with AsyncSessionLocal() as session:
        await find_and_send_movies(session, message, movie_title, state)
        data = await state.get_data()
        movie_titles = data.get('movie_titles', [])
        if movie_titles:
            await state.set_state(DeleteMovieStates.waiting_for_selected_movie)
        else:
            await message.answer('Фильмы не найдены для удаления. Попробуйте снова.', reply_markup=main_menu_keyboard)
            await state.clear()
            return


@router.message(DeleteMovieStates.waiting_for_selected_movie)
async def process_movie_selected(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    movie_titles = user_data.get('movie_titles', [])

    if message.text in movie_titles:
        selected_movie_title = message.text
        await message.answer(f'Вы уверены, что хотите удалить фильм "{selected_movie_title}"? (Да/Нет)')
        await state.update_data(movie_title=selected_movie_title)
        await state.set_state(DeleteMovieStates.waiting_for_confirmation)
    else:
        await message.answer('Фильм не найден в списке. Пожалуйста, выберите фильм из предложенного списка.',
                             reply_markup=main_menu_keyboard)
        await state.clear()

@router.message(DeleteMovieStates.waiting_for_confirmation)
async def process_movie_confirmation(message: types.Message, state: FSMContext):
    answer = message.text
    user_data = await state.get_data()
    movie_title = user_data.get('movie_title')

    if answer.lower() == 'да':
        async with AsyncSessionLocal() as session:
            await session.execute(delete(Movie).where(Movie.title == movie_title))
            await session.commit()
        answer = 'Фильм успешно удален.'
        await state.clear()
    elif answer.lower() == 'нет':
        answer = 'Удаление отменено.'
        await state.clear()
    else:
        answer = 'Пожалуйста, ответьте "Да" или "Нет".'
    await message.answer(answer, reply_markup=main_menu_keyboard)

@router.message(lambda message: message.text == '✏️ Редактировать рецензию')
async def update_review_handler(message: types.Message, state: FSMContext):
    await message.answer('Введите название фильма для редактирования рецензии:')
    await state.set_state(UpdateReviewStates.waiting_for_movie_edit)


@router.message(UpdateReviewStates.waiting_for_movie_edit)
async def process_movie_updating(message: types.Message, state: FSMContext):
    movie_title = message.text
    async with AsyncSessionLocal() as session:
        await find_and_send_movies(session, message, movie_title, state)
        data = await state.get_data()
        movie_titles = data.get('movie_titles', [])
        if movie_titles:
            await state.set_state(UpdateReviewStates.waiting_for_selected_movie)
        else:
            await message.answer('Фильмы не найдены для редактирования рецензии. Попробуйте снова.')
            await state.clear()

@router.message(UpdateReviewStates.waiting_for_selected_movie)
async def process_selected_movie_updating(message: types.Message, state: FSMContext):
    selected_movie = message.text
    async with AsyncSessionLocal() as session:
        movie = await session.scalar(select(Movie).filter_by(title=selected_movie))
        if movie:
            review = await session.scalar(select(Review).filter_by(movie_id=movie.id))
            if review:
                await message.answer(
                    f'Ваш текущий рейтинг: {review.rating}\nВаш комментарий: {review.comment}\nВведите новый рейтинг:')
                await state.update_data(review_id=review.id)
                await state.set_state(UpdateReviewStates.waiting_for_new_rating)

def register_handlers(dp):
    dp.include_router(router)
