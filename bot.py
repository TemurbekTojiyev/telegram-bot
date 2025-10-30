import asyncio
import hashlib
import logging
import yt_dlp
import os
import base64
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# .env faylni o'qish (Render yoki lokal)
load_dotenv()

# Tokenni .env dan olish (xavfsiz!)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! .env faylga qo'shing.")

# === COOKIES SOZLASH (YANGI) ===
COOKIES_FILE = "/tmp/cookies.txt"  # Render'da /tmp ishlaydi

# Render'da base64 dan cookies.txt yaratish
cookies_base64 = os.getenv('INSTAGRAM_COOKIES_BASE64')
if cookies_base64 and not os.path.exists(COOKIES_FILE):
    try:
        with open(COOKIES_FILE, 'wb') as f:
            f.write(base64.b64decode(cookies_base64))
        logging.info("Cookies fayli yaratildi (Render'da).")
    except Exception as e:
        logging.error(f"Cookies yaratishda xato: {e}")

# === BOT ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# Yuklash papkasi
DOWNLOAD_PATH = "/tmp/downloads/"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# FFmpeg yo'li (Render'da kerak emas, chunki u o'rnatilgan)
FFMPEG_PATH = None  # Render'da None bo'lsin

executor = ThreadPoolExecutor()

def get_video_filename(video_url):
    return os.path.join(DOWNLOAD_PATH, f"{hashlib.md5(video_url.encode()).hexdigest()}.mp4")

async def download_instagram_video(video_url):
    """ Instagramdan video yuklash + COOKIES """
    file_path = get_video_filename(video_url)

    ydl_opts = {
        'outtmpl': file_path,
        'format': 'bv+ba/b',
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'retries': 5,
        'fragment_retries': 10,
        'http_chunk_size': '50M',
        'sleep_interval': 5,  # Rate-limit uchun
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'cookies': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,  # COOKIES QO‘SHILDI
    }

    # FFmpeg faqat lokalda kerak
    if FFMPEG_PATH and os.name == 'nt':  # Windows
        ydl_opts['ffmpeg_location'] = FFMPEG_PATH

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(executor, lambda: yt_dlp.YoutubeDL(ydl_opts).download([video_url]))

        if os.path.exists(file_path):
            return file_path
        raise Exception("Video yuklanmadi.")
    except Exception as e:
        logging.error(f"Yuklash xatosi: {video_url} - {str(e)}")
        raise

# === /start ===
@router.message(Command("start"))
async def start_command(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ℹ️ Yordam", callback_data="help")],
    ])
    await message.answer(
        "Assalomu alaykum! \n\n"
        "Instagram videolarini yuklab beraman. Havola yuboring! \n"
        "@Temurbek_T_H tomonidan yaratilgan.",
        reply_markup=keyboard
    )

# === Tugmalar ===
@router.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    await callback.message.answer("Instagram havolasini yuboring — video yuklab beraman!")
    await callback.answer()

# === Instagram havolasi ===
@router.message(F.text.contains("instagram.com"))
async def process_instagram_video(message: Message):
    video_url = message.text.strip()

    progress_msg = await message.answer("Yuklanmoqda... ⏳")

    try:
        file_path = await download_instagram_video(video_url)
        await progress_msg.delete()

        await message.answer_document(
            FSInputFile(file_path),
            caption="Sizning videoingiz tayyor! \n@video_insta_yuklabot"
        )
        os.remove(file_path)  # Joy tejash
    except Exception as e:
        await progress_msg.edit_text(f"Xatolik: {str(e)}\n\nCookies yangilang yoki rate-limit.")

# === Main ===
async def main():
    logging.info("Bot ishga tushdi...")

    if not router.parent_router:
        dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())