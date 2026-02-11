import os
import yt_dlp
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = "8419374064:AAHcD9DAptVN5VlQI6dpQRbRIFLTkfBLH0Q"
ADMIN_ID = 6682960798  # ADMIN TELEGRAM ID

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_links = {}

# ===== DATABASE =====
conn = sqlite3.connect("bot.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY
)
""")
conn.commit()


def add_user(user_id):
    cur.execute("INSERT OR IGNORE INTO users VALUES(?)", (user_id,))
    conn.commit()


def get_users():
    cur.execute("SELECT user_id FROM users")
    return [x[0] for x in cur.fetchall()]


# ===== PLATFORM DETECT =====
def detect_platform(url):
    url = url.lower()
    if "instagram.com" in url:
        return "instagram"
    elif "tiktok.com" in url:
        return "tiktok"
    elif "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return "unknown"


# ===== DOWNLOAD =====
def download_video(url, mode="video"):

    if mode == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3'
            }]
        }
    else:
        ydl_opts = {
            'format': 'mp4/best',
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s'
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file = ydl.prepare_filename(info)

        if mode == "audio":
            file = os.path.splitext(file)[0] + ".mp3"

    return file


# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    add_user(user_id)

    keyboard = [[InlineKeyboardButton("📥 Download", callback_data="download")]]

    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙ Admin Panel", callback_data="admin")])

    await update.message.reply_text(
        "🔥 Universal Downloader Bot",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ===== BUTTON =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # DOWNLOAD MENU
    if query.data == "download":
        await query.message.reply_text("📎 Link yuboring")

    # ADMIN PANEL
    elif query.data == "admin" and user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("👥 User Count", callback_data="users")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")]
        ]
        await query.message.reply_text(
            "⚙ Admin Panel",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # USER COUNT
    elif query.data == "users" and user_id == ADMIN_ID:
        users = len(get_users())
        await query.message.reply_text(
            f"📊 Statistika\n\n👥 Foydalanuvchilar soni: {users}"
        )

    # BROADCAST
    elif query.data == "broadcast" and user_id == ADMIN_ID:
        context.user_data["broadcast"] = True
        await query.message.reply_text("📢 Yubormoqchi bo‘lgan xabarni yozing")

    # DOWNLOAD
    elif query.data in ["video", "audio"]:
        url = user_links.get(user_id)

        await query.message.reply_text("⏳ Yuklanmoqda...")

        try:
            file = download_video(url, query.data)

            if query.data == "audio":
                await query.message.reply_audio(audio=open(file, "rb"))
            else:
                await query.message.reply_video(video=open(file, "rb"))

            os.remove(file)

        except Exception as e:
            await query.message.reply_text(f"❌ Xatolik: {e}")


# ===== HANDLE MESSAGE =====
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    add_user(user_id)

    # BROADCAST MODE
    if context.user_data.get("broadcast") and user_id == ADMIN_ID:
        context.user_data["broadcast"] = False
        users = get_users()

        for u in users:
            try:
                await context.bot.send_message(u, update.message.text)
            except:
                pass

        await update.message.reply_text("✅ Broadcast yuborildi")
        return

    url = update.message.text
    user_links[user_id] = url

    platform = detect_platform(url)

    if platform == "youtube":
        keyboard = [[
            InlineKeyboardButton("🎬 Video", callback_data="video"),
            InlineKeyboardButton("🎵 Audio", callback_data="audio")
        ]]
    else:
        keyboard = [[InlineKeyboardButton("🎬 Video", callback_data="video")]]

    await update.message.reply_text(
        f"Platform: {platform.upper()}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("Bot ishga tushdi 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()



bot.polling(none_stop=True)
