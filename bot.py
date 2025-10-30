import asyncio
import hashlib
import logging
import yt_dlp
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from concurrent.futures import ThreadPoolExecutor
import os
from dotenv import load_dotenv

load_dotenv()
print(os.getenv("BOT_TOKEN"))

# Telegram bot tokenini to'g'ridan-to'g'ri belgilash
BOT_TOKEN = '7539307597:AAHL71GMS3RA72e_V1CNdaOEEyzpHgQPWco'  # Bu yerda o'z tokeningizni kiriting

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# 📌 SSD yoki RAM'da saqlash
DOWNLOAD_PATH = "/tmp/downloads/"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# ✅ FFmpeg yo'li (Siz bergan yo‘l)
FFMPEG_PATH = r'C:\Users\pc\ffmpeg-2025-02-13-git-19a2d26177-essentials_build\bin'

executor = ThreadPoolExecutor()

def get_video_filename(video_url):
    return os.path.join(DOWNLOAD_PATH, f"{hashlib.md5(video_url.encode()).hexdigest()}.mp4")

async def download_instagram_video(video_url):
    """ 📌 Instagramdan video yuklab olish (yt-dlp orqali) """
    file_path = get_video_filename(video_url)

    ydl_opts = {
        'ffmpeg_location': FFMPEG_PATH,  # FFmpeg yo'lini qo'shish
        'outtmpl': file_path,
        'format': 'bv+ba/b',
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'retries': 5,
        'fragment-retries': 10,
        'http-chunk-size': '50M',
        'progress_hooks': [lambda d: logging.info(f"Downloading: {d['_percent_str']}")],

    }

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(executor, lambda: yt_dlp.YoutubeDL(ydl_opts).download([video_url]))

        if os.path.exists(file_path):
            return file_path
        raise Exception("Video manzilini qabul qilaman.")
    except Exception as e:
        logging.error(f"🚨 Iltimos video fayl yuboring: {video_url} - {str(e)}")
        raise

@router.message(Command("start"))
async def start_command(message: Message):
    """ 🚀 /start buyrug‘i foydalanuvchini kutib oladi """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        #[InlineKeyboardButton(text="📥 Yangi video yuklash", callback_data="new_video")],
        [InlineKeyboardButton(text="ℹ️ start", callback_data="help")],
    ])

    await message.answer(
        "🎉 Assalomu alaykum! \n\n"
        "Bu bot Instagram videolarini yuklab berish uchun @Temurbek_T_H tomonidan yaratilgan. "
             "Pastdagi tugmani bosing. 🚀",
        reply_markup=keyboard
    )

# 📌 Tugmalarni ishlashini ta'minlash
@router.callback_query(F.data == "new_video")
async def new_video_handler(callback: CallbackQuery):
    await callback.message.answer("📥 Video yuklash uchun Instagram havolasini yuboring!")
    await callback.answer()

@router.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    await callback.message.answer("ℹ️ Instagram videolarini yuklab olish uchun videoning havolasini yuboring!")
    await callback.answer()

@router.message(F.text.contains("instagram.com"))
async def process_instagram_video(message: Message):
    video_url = message.text.strip()

    progress_msg = await message.answer("🔄 Yuklanmoqda.")

    try:
        file_path = await download_instagram_video(video_url)
        await progress_msg.delete()

        await message.answer_document(FSInputFile(file_path), caption="✅ Sizni videoingiz tayyor! "
                                                                      " Ushbu video @video_insta_yuklabot tomonidan yuklandi!")
    except Exception as e:
        await progress_msg.edit_text(f"❌ Xatolik yuz berdi: {str(e)}")

async def main():
    logging.info("Bot ishga tushdi...")

    # Router'ni faqat bir marta qo‘shamiz
    if not router.parent_router:
        dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())