from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import TOKEN, WEBAPP_URL
from database import get_user_pref, set_user_pref

bot = Bot(token=TOKEN)
dp = Dispatcher()


def make_main_menu(lang="uz"):
    if lang == "ru":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Открыть магазин", web_app=WebAppInfo(url=f"{WEBAPP_URL}/shop"))],
            [InlineKeyboardButton(text="🌐 Изменить язык", callback_data="change_lang")],
            [InlineKeyboardButton(text="🎨 Изменить тему", callback_data="change_theme")],
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Do‘konni ochish", web_app=WebAppInfo(url=f"{WEBAPP_URL}/shop"))],
            [InlineKeyboardButton(text="🌐 Tilni o‘zgartirish", callback_data="change_lang")],
            [InlineKeyboardButton(text="🎨 Mavzuni o‘zgartirish", callback_data="change_theme")],
        ])


@dp.message(CommandStart())
async def start_cmd(message: Message):
    user = get_user_pref(message.from_user.id)
    text = "🛒 Do‘konimizga xush kelibsiz!" if user["lang"] == "uz" else "🛒 Добро пожаловать в наш магазин!"
    await message.answer(text, reply_markup=make_main_menu(user["lang"]))


@dp.callback_query(F.data == "change_lang")
async def change_lang(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"),
            InlineKeyboardButton(text="🇺🇿 Oʻzbek", callback_data="set_lang_uz"),
        ]
    ])
    await callback.message.edit_text("Выберите язык / Tilni tanlang:", reply_markup=kb)


@dp.callback_query(F.data.startswith("set_lang_"))
async def set_lang(callback: types.CallbackQuery):
    lang = "ru" if callback.data == "set_lang_ru" else "uz"
    set_user_pref(callback.from_user.id, lang=lang)
    await callback.message.edit_text(
        "Язык успешно изменён!" if lang == "ru" else "Til muvaffaqiyatli o‘zgartirildi!",
        reply_markup=make_main_menu(lang)
    )


@dp.callback_query(F.data == "change_theme")
async def change_theme(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌙 Тёмная / Qorong‘i", callback_data="set_theme_dark"),
            InlineKeyboardButton(text="☀️ Светлая / Yorug‘", callback_data="set_theme_light"),
        ]
    ])
    await callback.message.edit_text("Выберите тему / Mavzuni tanlang:", reply_markup=kb)


@dp.callback_query(F.data.startswith("set_theme_"))
async def set_theme(callback: types.CallbackQuery):
    theme = "dark" if callback.data == "set_theme_dark" else "light"
    set_user_pref(callback.from_user.id, theme=theme)
    user = get_user_pref(callback.from_user.id)
    await callback.message.edit_text(
        "Тема успешно изменена!" if user["lang"] == "ru" else "Mavzu muvaffaqiyatli o‘zgartirildi!",
        reply_markup=make_main_menu(user["lang"])
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
