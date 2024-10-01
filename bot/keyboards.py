from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

add_movie_button = KeyboardButton(text='🎥 Добавить фильм')
add_review_button = KeyboardButton(text='🗒️ Добавить рецензию')

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [add_movie_button, add_review_button]
    ],
    resize_keyboard=True
)