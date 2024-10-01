from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

add_movie_button = KeyboardButton(text='🎥 Добавить фильм')
add_review_button = KeyboardButton(text='🗒️ Добавить рецензию')
get_movies_button = KeyboardButton(text='🧡 Просмотреть список фильмов')
delete_movie_button = KeyboardButton(text='❌ Удалить фильм')
update_review_button = KeyboardButton(text='✏️ Редактировать рецензию')
other_button = KeyboardButton(text='⚙️ Ещё...')

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [add_movie_button, add_review_button],
        [get_movies_button, other_button]
    ],
    resize_keyboard=True,
    input_field_placeholder='Воспользуйся меню 👇'
)

additional_menu_keyboard = ReplyKeyboardMarkup(
keyboard=[
        [delete_movie_button, update_review_button],
        [KeyboardButton(text='🔙 Назад')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Воспользуйся меню 👇'
)