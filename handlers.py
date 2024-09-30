from aiogram import types, Router
from aiogram.filters import Command

router = Router()

@router.message(Command(commands=['start']))
async def start(message: types.Message):
    await message.reply('Hi')

def register_handlers(dp):
    dp.include_router(router)