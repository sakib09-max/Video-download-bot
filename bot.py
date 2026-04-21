import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import base64
import threading
from flask import Flask

BOT_TOKEN = "8089616190:AAF14HoE5yA_tm2RByJ6bLe_KOqJHBJb8mo"
bot = telebot.TeleBot(BOT_TOKEN)

# ================= LINKS =================
youtube_link = base64.b64decode("aHR0cHM6Ly95b3V0dWJlLmNvbS9Aenlyb3hfY2hlYXQ=").decode()
support_link = base64.b64decode("aHR0cHM6Ly90Lm1lL1NBS0lCX0JIQUlJ").decode()

# ================= FLASK =================
app = Flask('')

@app.route('/')
def home():
    return "Bot Running"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    threading.Thread(target=run).start()

# ================= PROGRESS BAR =================
def progress_bar(percent):
    try:
        percent = float(percent)
    except:
        percent = 0.0

    total = 20
    filled = int(total * percent / 100)

    bar = "█" * filled
    if filled < total:
        bar += "▓"
    bar += "░" * (total - len(bar))

    return f"[{bar}] {percent:.1f}%"

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("📢 SUBSCRIBE", url=youtube_link),
        InlineKeyboardButton("📚 TUTORIALS", url=youtube_link),
        InlineKeyboardButton("👤 OWNER", url=support_link)
    )

    bot.send_message(
        message.chat.id,
        "🔥 MULTI VIDEO DOWNLOADER BOT\n\nYouTube / Facebook / Instagram / TikTok / Terabox 🎬",
        reply_markup=kb
    )

# ================= SMART DOWNLOADER =================
def download_video(url, chat_id, msg_id, ydl_opts):

    last_text = ""

    def hook(d):
        nonlocal last_text

        try:
            if d['status'] == 'downloading':

                percent = d.get('_percent_str', '0%').strip().replace('%', '')
                speed = d.get('_speed_str', '')
                eta = d.get('_eta_str', '')

                try:
                    p = float(percent)
                except:
                    p = 0

                bar = progress_bar(p)

                text = f"""⬇️ Downloading...
{bar}
⚡ {speed}
⏳ ETA: {eta}"""

                if text != last_text:
                    bot.edit_message_text(text, chat_id, msg_id)
                    last_text = text

            elif d['status'] == 'finished':
                bar = progress_bar(100)
                bot.edit_message_text(
                    f"📦 Processing Complete\n{bar}\n⬆️ Uploading...",
                    chat_id,
                    msg_id
                )

        except:
            pass

    ydl_opts['progress_hooks'] = [hook]

    # 🔥 FIX ALL PLATFORM SUPPORT
    ydl_opts['extractor_args'] = {
        'youtube': {'player_client': ['android', 'web']},
        'tiktok': {'api': 'web'},
        'facebook': {'api': 'web'}
    }

    ydl_opts['noplaylist'] = True
    ydl_opts['quiet'] = True
    ydl_opts['retries'] = 10

    # 🔥 fallback if 720p not available
    if 'format' in ydl_opts and '720' in ydl_opts['format']:
        ydl_opts['format'] += '/best'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# ================= LINK HANDLER =================
user_links = {}

@bot.message_handler(func=lambda m: m.text and "http" in m.text)
def get_link(message):
    user_links[message.chat.id] = message.text.strip()

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🎥 720p", callback_data="720"),
        InlineKeyboardButton("📱 360p", callback_data="360"),
        InlineKeyboardButton("🎵 MP3", callback_data="mp3")
    )

    bot.reply_to(message, "🎯 Choose Quality:", reply_markup=kb)

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    choice = call.data
    url = user_links.get(chat_id)

    msg = bot.send_message(chat_id, "⏳ Starting...")

    try:

        # ================= OPTIONS =================
        if choice == "720":
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'outtmpl': '%(id)s.%(ext)s'
            }

        elif choice == "360":
            ydl_opts = {
                'format': 'best[height<=360]/best',
                'merge_output_format': 'mp4',
                'outtmpl': '%(id)s.%(ext)s'
            }

        elif choice == "mp3":
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': '%(id)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
            }

        # ================= DOWNLOAD =================
        file_name = download_video(url, chat_id, msg.message_id, ydl_opts)

        # ================= SEND =================
        if choice == "mp3":
            audio = file_name.rsplit(".", 1)[0] + ".mp3"
            with open(audio, "rb") as f:
                bot.send_audio(chat_id, f, caption="Downloaded Successfully!\nPower by: @SAKIB_BHAII")
            os.remove(audio)

        else:
            with open(file_name, "rb") as f:
                bot.send_video(chat_id, f, caption="Downloaded Successfully!\nPower by: @SAKIB_BHAII")
            os.remove(file_name)

        bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Error:\n{str(e)}", chat_id, msg.message_id)

# ================= RUN =================
if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
