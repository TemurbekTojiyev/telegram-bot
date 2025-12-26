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

# .env yuklash
load_dotenv()

# Token
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylda topilmadi!")

# === COOKIES SOZLASH (ISHONCHLI ISHLASH UCHUN) ===
COOKIES_FILE = "/tmp/instagram_cookies.txt"  # /tmp Render'da ishlaydi

cookies_base64 = os.getenv('INSTAGRAM_COOKIES_BASE64')
if cookies_base64 and not os.path.exists(COOKIES_FILE):
    try:
        with open(COOKIES_FILE, 'wb') as f:
            f.write(base64.b64decode(cookies_base64))
        logging.info("Cookies fayli yaratildi.")
    except Exception as e:
        logging.error(f"Cookies yaratishda xato: {e}")

# Bot va dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Logging
logging.basicConfig(level=logging.INFO)

# Yuklash papkasi
DOWNLOAD_PATH = "/tmp/downloads/"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# Executor
executor = ThreadPoolExecutor(max_workers=4)

def get_video_filename(video_url: str) -> str:
    filename = hashlib.md5(video_url.encode()).hexdigest() + ".mp4"
    return os.path.join(DOWNLOAD_PATH, filename)

async def download_instagram_video(video_url: str) -> str:
    file_path = get_video_filename(video_url)
# Yangi variant
async def download_instagram_video(video_url: str) -> str:
    file_path = get_video_filename(video_url)

    ydl_opts = {
        'outtmpl': file_path,  # .mp4 bilan to'liq yo'l
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'retries': 15,
        'fragment_retries': 15,
        'concurrent_fragment_downloads': 5,  # 16 juda yuqori bo'lishi mumkin
        'sleep_interval': 2,
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)...',
        'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,  # cookiefile emas, cookies emas
    }

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(executor, lambda: yt_dlp.YoutubeDL(ydl_opts).download([video_url]))

        if os.path.exists(file_path):
            return file_path
        else:
            raise Exception("Fayl yaratilmadi")

    except Exception as e:
        logging.error(f"Yuklash xatosi: {video_url} | {e}")
        raise Exception("Video yuklanmadi. Havola private bo'lishi yoki cookies eskirgan.")

# /start
@router.message(Command("start"))
async def start_command(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ℹ️ Yordam", callback_data="help")]
    ])
    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "Instagram Reels, Post va IGTV videolarini yuklab beraman.\n"
        "Havolani yuboring!\n\n",
        reply_markup=keyboard
    )

# Yordam
@router.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    await callback.message.answer(
        "📹 Instagram havolasini yuboring (reel, p, tv).\n"
        "• Public videolar yuklanadi\n"
        "• @tima_tojiyev 👮‍♀️ admin bilan bog'laning)\n"
        "• Stories yuklanmaydi"
    )
    await callback.answer()

# Instagram havolasi
@router.message(F.text.regexp(r"https?://(www\.)?instagram\.com/(p|reel|tv)/"))
async def process_instagram_video(message: Message):
    video_url = message.text.strip()

    progress = await message.answer("⏳ Yuklanmoqda👀... Kuting🙂...")

    try:
        file_path = await download_instagram_video(video_url)

        await progress.delete()

        await message.answer_video(
            FSInputFile(file_path),
            caption="✅ Video tayyor!\n\n@video_insta_yuklabot",
            supports_streaming=True,  # Muhim: bu tezroq yuklash va o‘ynatish imkonini beradi
            width=1080,               # ixtiyoriy: agar bilasangiz
            height=1920,              # ixtiyoriy: Reels uchun odatda 1080x1920
            duration=None             # avto aniqlaydi
        )

        # Fayl o'chirish
        try:
            os.remove(file_path)
        except:
            pass

    except Exception as e:
        await progress.edit_text(f"❌ Xato: {str(e)}\n\nCookiesni yangilang yoki public havola yuboring.")

# Main
async def main():
    logging.info("Bot ishga tushdi...")
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    