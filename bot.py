from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.filters import CommandStart
from config import TOKEN, WEBAPP_URL, t
from database import get_user_pref, set_user_pref

bot = Bot(token=TOKEN)
dp = Dispatcher()

def make_main_menu(lang="uz"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "bot.open_shop"), web_app=WebAppInfo(url=f"{WEBAPP_URL}/shop"))],
        [InlineKeyboardButton(text=t(lang, "bot.change_lang"), callback_data="change_lang")],
        [InlineKeyboardButton(text=t(lang, "bot.change_theme"), callback_data="change_theme")],
    ])

@dp.message(CommandStart())
async def start_cmd(message: Message):
    user = get_user_pref(message.from_user.id)
    await message.answer(t(user["lang"], "bot.start"), reply_markup=make_main_menu(user["lang"]))

@dp.callback_query(F.data == "change_lang")
async def change_lang(callback: types.CallbackQuery):
    user = get_user_pref(callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"),
        InlineKeyboardButton(text="🇺🇿 Oʻzbek", callback_data="set_lang_uz"),
    ]])
    await callback.message.edit_text(t(user["lang"], "bot.choose_lang"), reply_markup=kb)

@dp.callback_query(F.data.startswith("set_lang_"))
async def set_lang(callback: types.CallbackQuery):
    lang = "ru" if callback.data == "set_lang_ru" else "uz"
    set_user_pref(callback.from_user.id, lang=lang)
    await callback.message.edit_text(t(lang, "bot.lang_changed"), reply_markup=make_main_menu(lang))

@dp.callback_query(F.data == "change_theme")
async def change_theme(callback: types.CallbackQuery):
    user = get_user_pref(callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🌙 Тёмная / Qorong‘i", callback_data="set_theme_dark"),
        InlineKeyboardButton(text="☀️ Светлая / Yorug‘", callback_data="set_theme_light"),
    ]])
    await callback.message.edit_text(t(user["lang"], "bot.choose_theme"), reply_markup=kb)

@dp.callback_query(F.data.startswith("set_theme_"))
async def set_theme(callback: types.CallbackQuery):
    theme = "dark" if callback.data == "set_theme_dark" else "light"
    set_user_pref(callback.from_user.id, theme=theme)
    user = get_user_pref(callback.from_user.id)
    await callback.message.edit_text(t(user["lang"], "bot.theme_changed"), reply_markup=make_main_menu(user["lang"]))

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
