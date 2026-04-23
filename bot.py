import telebot
import yt_dlp
import os
import base64
import threading
import time
import requests
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import re

# ===================== CONFIGURATION =====================
# Replace with your actual bot token from @BotFather
BOT_TOKEN = "8089616190:AAF14HoE5yA_tm2RByJ6bLe_KOqJHBJb8mo"

# Decode secured links
YOUTUBE_LINK = base64.b64decode("aHR0cHM6Ly95b3V0dWJlLmNvbS9AYmxhY2trbm93bGVkZ2VfMTkwP3NpPTlFd2tNUEdiLWxIUnpaZHE=").decode('utf-8')
SUPPORT_LINK = base64.b64decode("aHR0cHM6Ly90Lm1lL0JMQU5LX0tub3dsZWRnZV8xOTA=").decode('utf-8')

# Branding
OWNER_USERNAME = "@SAKIB_BHAII"
POWERED_BY = "@SAKIB_BHAII"

# ===================== FLASK KEEP ALIVE =====================
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is Running! | Powered by @SAKIB_BHAII"

@app.route('/health')
def health():
    return {"status": "alive", "service": "Video Downloader Bot"}

def run_flask():
    app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False)

def keep_alive():
    """Start Flask server in a separate thread to prevent sleeping on Render"""
    server = threading.Thread(target=run_flask)
    server.daemon = True
    server.start()
    print("🚀 Flask server started on port 10000")

# ===================== BOT INITIALIZATION =====================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# Supported platforms regex patterns
SUPPORTED_PATTERNS = [
    r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+',
    r'(https?://)?(www\.)?instagram\.(com|reel)/.+',
    r'(https?://)?(www\.)?facebook\.com/.+',
    r'(https?://)?(www\.)?fb\.watch/.+',
    r'(https?://)?(www\.)?tiktok\.com/.+',
    r'(https?://)?(www\.)?vm\.tiktok\.com/.+',
    r'(https?://)?(www\.)?terabox\.com/.+',
    r'(https?://)?(www\.)?1024tera\.com/.+',
    r'(https?://)?(www\.)?twitter\.com/.+',
    r'(https?://)?(www\.)?x\.com/.+',
    r'(https?://)?(www\.)?reddit\.com/.+',
    r'(https?://)?(www\.)?pinterest\.com/.+',
    r'(https?://)?(www\.)?vimeo\.com/.+',
    r'(https?://)?(www\.)?dailymotion\.com/.+',
    r'(https?://)?(www\.)?soundcloud\.com/.+',
    r'(https?://)?(www\.)?twitch\.tv/.+',
    r'(https?://)?(www\.)?streamable\.com/.+',
]

# ===================== UI HELPERS =====================
def create_main_keyboard():
    """Create inline keyboard for /start command"""
    markup = InlineKeyboardMarkup(row_width=1)

    btn1 = InlineKeyboardButton("🔔 SUBSCRIBE CHANNEL", url=YOUTUBE_LINK)
    btn2 = InlineKeyboardButton("📚 ALL TUTORIALS", url=YOUTUBE_LINK)
    btn3 = InlineKeyboardButton("💬 CONTACT OWNER", url=SUPPORT_LINK)

    markup.add(btn1, btn2, btn3)
    return markup

def progress_bar(percentage, length=20):
    """Generate a visual progress bar"""
    filled = int(length * percentage / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percentage:.1f}%"

def upload_bar(step):
    """Upload progress steps with animation"""
    bars = {
        1: "[█░░░░░░░░░] 10%",
        2: "[███░░░░░░░] 30%",
        3: "[██████░░░░] 60%",
        4: "[██████████] 100%"
    }
    return bars.get(step, "[░░░░░░░░░░] 0%")

# ===================== PROGRESS CALLBACK =====================
class DownloadProgress:
    def __init__(self, bot, chat_id, message_id):
        self.bot = bot
        self.chat_id = chat_id
        self.message_id = message_id
        self.last_update = 0
        self.download_percent = 0

    def hook(self, d):
        """yt-dlp progress hook"""
        current_time = time.time()

        # Update every 3 seconds to avoid rate limits
        if current_time - self.last_update < 3:
            return

        self.last_update = current_time

        if d['status'] == 'downloading':
            if 'downloaded_bytes' in d and 'total_bytes' in d and d['total_bytes']:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                self.download_percent = min(percent, 99)

                text = f"""⏳ <b>Downloading Video...</b>

{progress_bar(self.download_percent)}

📥 Speed: {d.get('speed', 'N/A')}
📦 Size: {self._format_bytes(d.get('total_bytes', 0))}
⏱ ETA: {d.get('eta', 'N/A')}s

<i>Please wait, this may take a moment...</i>"""

                try:
                    self.bot.edit_message_text(
                        text, 
                        self.chat_id, 
                        self.message_id,
                        parse_mode='HTML'
                    )
                except:
                    pass

        elif d['status'] == 'finished':
            self.download_percent = 100
            text = f"""✅ <b>Download Complete!</b>

{progress_bar(100.0)}

📦 Download Complete
{progress_bar(100.0)}
⬆️ <b>Uploading to Telegram...</b>

<i>Almost done! Sending your video...</i>"""
            try:
                self.bot.edit_message_text(
                    text,
                    self.chat_id,
                    self.message_id,
                    parse_mode='HTML'
                )
            except:
                pass

    def _format_bytes(self, bytes_count):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} TB"

# ===================== VIDEO DOWNLOADER =====================
def get_ydl_opts(chat_id, message_id):
    """Get yt-dlp options with progress tracking"""
    progress = DownloadProgress(bot, chat_id, message_id)

    return {
        'format': 'best[filesize<50M]/best[filesize<100M]/best',
        'outtmpl': 'downloads/%(title)s_%(id)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'max_filesize': 52428800,  # 50MB Telegram limit
        'progress_hooks': [progress.hook],
        'quiet': True,
        'no_warnings': True,
        'cookiesfrombrowser': None,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        },
        # Fix for various platforms
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'player_skip': ['webpage', 'configs', 'js'],
            },
            'facebook': {
                'formats': ['dash', 'hd', 'sd'],
            }
        },
        # Fallback options
        'format_sort': ['filesize:50M'],
    }

def is_valid_url(url):
    """Check if URL is from supported platform"""
    for pattern in SUPPORTED_PATTERNS:
        if re.match(pattern, url):
            return True
    return False

def cleanup_file(filepath):
    """Safely remove downloaded file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"🗑️ Cleaned up: {filepath}")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

# ===================== COMMAND HANDLERS =====================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle /start command with premium branding"""
    welcome_text = f"""🎬 <b>Welcome to Premium Video Downloader</b>

👑 <b>Owner:</b> {OWNER_USERNAME}
⚡ <b>Powered by:</b> {POWERED_BY}

✨ <b>Features:</b>
• Download from YouTube, Instagram, Facebook
• TikTok, Twitter/X, Reddit, Pinterest
• Vimeo, Dailymotion, SoundCloud, Twitch
• TeraBox & 20+ platforms supported
• High Quality & Fast Speed
• No Ads, No Watermarks

📎 <b>How to use:</b>
Simply send any video link and I'll download it instantly!

🚀 <b>Bot Status:</b> <code>ONLINE ✅</b>"""

    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=create_main_keyboard(),
        parse_mode='HTML'
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    """Handle /help command"""
    help_text = f"""📖 <b>How to Use This Bot</b>

1️⃣ Copy video link from any supported platform
2️⃣ Paste it here in the chat
3️⃣ Wait for download & upload
4️⃣ Enjoy your video!

<b>Supported Platforms:</b>
• YouTube / YouTube Shorts
• Instagram Reels / Posts
• Facebook Videos
• TikTok (with/without watermark)
• Twitter / X
• Reddit
• Pinterest
• Vimeo
• Dailymotion
• SoundCloud
• Twitch
• TeraBox
• And more...

<b>Limitations:</b>
• Max file size: 50MB (Telegram limit)
• Some private videos may not work

💬 Need help? Contact: {POWERED_BY}"""

    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(commands=['about'])
def send_about(message):
    """Handle /about command"""
    about_text = f"""🤖 <b>About This Bot</b>

<b>Version:</b> 2.0 Premium
<b>Developer:</b> {OWNER_USERNAME}
<b>Powered by:</b> {POWERED_BY}

<b>Technologies:</b>
• Python 3.11+
• pyTelegramBotAPI
• yt-dlp (Latest)
• Flask Server
• Render Cloud Hosting

<b>Updates:</b> Regular updates for best performance

© 2024 All Rights Reserved"""

    bot.send_message(message.chat.id, about_text, parse_mode='HTML')

# ===================== VIDEO DOWNLOAD HANDLER =====================
@bot.message_handler(func=lambda message: message.text and is_valid_url(message.text))
def download_video(message):
    """Handle video download from supported URLs"""
    url = message.text.strip()
    chat_id = message.chat.id

    # Send initial analyzing message
    analyzing_msg = bot.send_message(
        chat_id,
        "🔍 <b>Analyzing link...</b>

<i>Please wait while I fetch video info...</i>",
        parse_mode='HTML'
    )

    try:
        # Create downloads directory if not exists
        os.makedirs('downloads', exist_ok=True)

        # Get options with progress tracking
        ydl_opts = get_ydl_opts(chat_id, analyzing_msg.message_id)

        # Extract info first
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise Exception("Could not extract video info")

                title = info.get('title', 'Unknown Video')
                duration = info.get('duration', 0)
                uploader = info.get('uploader', 'Unknown')

                # Update to downloading status
                bot.edit_message_text(
                    f"""📥 <b>Downloading Started</b>

🎬 <b>Title:</b> <code>{title[:50]}...</code>
👤 <b>Uploader:</b> {uploader}
⏱ <b>Duration:</b> {duration//60}:{duration%60:02d}

{progress_bar(0)}

<i>Downloading video, please wait...</i>""",
                    chat_id,
                    analyzing_msg.message_id,
                    parse_mode='HTML'
                )

            except Exception as info_error:
                print(f"Info extraction error: {info_error}")
                # Continue anyway, yt-dlp might still download
                title = "Video"

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if 'entries' in info:
                info = info['entries'][0]

            # Get downloaded file path
            filename = ydl.prepare_filename(info)

            # Check if file exists (yt-dlp might change extension)
            if not os.path.exists(filename):
                # Try common video extensions
                base = os.path.splitext(filename)[0]
                for ext in ['.mp4', '.webm', '.mkv', '.mov']:
                    if os.path.exists(base + ext):
                        filename = base + ext
                        break

            if not os.path.exists(filename):
                raise FileNotFoundError("Downloaded file not found")

            # Check file size
            file_size = os.path.getsize(filename)
            if file_size > 52428800:  # 50MB
                bot.edit_message_text(
                    "❌ <b>File too large!</b>

This video exceeds Telegram's 50MB limit.
Try a shorter video.",
                    chat_id,
                    analyzing_msg.message_id,
                    parse_mode='HTML'
                )
                cleanup_file(filename)
                return

            # Upload with progress animation
            upload_steps = [
                (1, "⬆️ <b>Uploading to Telegram...</b>

📦 Download Complete
[████████████████████] 100.0%
⬆️ Uploading...

" + upload_bar(1)),
                (2, "⬆️ <b>Uploading to Telegram...</b>

📦 Download Complete
[████████████████████] 100.0%
⬆️ Uploading...

" + upload_bar(2)),
                (3, "⬆️ <b>Uploading to Telegram...</b>

📦 Download Complete
[████████████████████] 100.0%
⬆️ Uploading...

" + upload_bar(3)),
            ]

            for step, text in upload_steps:
                bot.edit_message_text(
                    text + "
<i>Sending video...</i>",
                    chat_id,
                    analyzing_msg.message_id,
                    parse_mode='HTML'
                )
                time.sleep(0.5)

            # Send the video
            with open(filename, 'rb') as video_file:
                bot.send_video(
                    chat_id,
                    video_file,
                    caption=f"""✅ <b>Downloaded Successfully!</b>

🎬 <b>{title[:100]}</b>
💾 <b>Size:</b> {file_size/1024/1024:.1f} MB

<b>Power by:</b> {POWERED_BY}""",
                    parse_mode='HTML',
                    supports_streaming=True
                )

            # Final success message
            bot.edit_message_text(
                f"""✅ <b>Download Complete!</b>

📦 Download Complete
[████████████████████] 100.0%
⬆️ Upload Complete
{upload_bar(4)}

🎉 <b>Video sent successfully!</b>

<b>Power by:</b> {POWERED_BY}""",
                chat_id,
                analyzing_msg.message_id,
                parse_mode='HTML'
            )

            # Cleanup
            cleanup_file(filename)

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "Private video" in error_msg:
            bot.edit_message_text(
                "🔒 <b>Private Video!</b>

This video is private and cannot be downloaded.",
                chat_id,
                analyzing_msg.message_id
            )
        elif "Video unavailable" in error_msg:
            bot.edit_message_text(
                "❌ <b>Video Unavailable!</b>

This video may have been deleted or is region-restricted.",
                chat_id,
                analyzing_msg.message_id
            )
        elif "Sign in" in error_msg or "login" in error_msg.lower():
            bot.edit_message_text(
                "🔐 <b>Login Required!</b>

This content requires authentication.
Try a public video instead.",
                chat_id,
                analyzing_msg.message_id
            )
        else:
            bot.edit_message_text(
                f"""❌ <b>Download Failed!</b>

Error: <code>{error_msg[:200]}</code>

Please try:
• Check if the link is valid
• Try another video
• Contact support if issue persists

<b>Power by:</b> {POWERED_BY}""",
                chat_id,
                analyzing_msg.message_id,
                parse_mode='HTML'
            )

        # Cleanup any partial downloads
        for f in os.listdir('downloads'):
            if f.endswith(('.part', '.ytdl', '.tmp')):
                cleanup_file(os.path.join('downloads', f))

    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text(
            f"""❌ <b>An error occurred!</b>

<code>{str(e)[:200]}</code>

Please try again or contact {POWERED_BY}""",
            chat_id,
            analyzing_msg.message_id,
            parse_mode='HTML'
        )

# ===================== FALLBACK HANDLER =====================
@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    """Handle non-URL messages"""
    bot.send_message(
        message.chat.id,
        f"""⚠️ <b>Invalid Link!</b>

Please send a valid video URL from:
• YouTube
• Instagram
• Facebook
• TikTok
• Twitter/X
• And more...

💬 Need help? Use /help or contact {POWERED_BY}""",
        parse_mode='HTML',
        reply_markup=create_main_keyboard()
    )

# ===================== ERROR HANDLER =====================
@bot.error_handler
def handle_error(exception):
    """Global error handler"""
    print(f"Bot error: {exception}")

# ===================== MAIN =====================
if __name__ == "__main__":
    print("🤖 Starting Premium Video Downloader Bot...")
    print(f"👑 Owner: {OWNER_USERNAME}")
    print(f"⚡ Powered by: {POWERED_BY}")

    # Start keep-alive server
    keep_alive()

    # Create downloads directory
    os.makedirs('downloads', exist_ok=True)

    print("🔄 Bot is polling...")

    # Start bot with retry logic
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(10)
