import os
import base64
import telebot
import yt_dlp
from yt_dlp.utils import DownloadError
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from keep_alive import keep_alive
import time
import threading
import math

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8089616190:AAF14HoE5yA_tm2RByJ6bLe_KOqJHBJb8mo")

# Secured Links (Base64 Encoded)
YOUTUBE_CHANNEL_B64 = "aHR0cHM6Ly95b3V0dWJlLmNvbS9Aenlyb3hfY2hlYXQ="
SUPPORT_LINK_B64 = "aHR0cHM6Ly90Lm1lL1NBS0lCX0JIQUlJ"

def decode_link(encoded):
    return base64.b64decode(encoded).decode('utf-8')

YOUTUBE_CHANNEL = decode_link(YOUTUBE_CHANNEL_B64)
SUPPORT_LINK = decode_link(SUPPORT_LINK_B64)

# ==================== PROGRESS BAR UTILITIES ====================
def progress_bar(percentage, length=20):
    """Create a visual progress bar with real percentage"""
    filled = math.floor(length * percentage / 100)
    bar = '█' * filled + '░' * (length - filled)
    return f"[{bar}] {percentage:.1f}%"

def upload_bar(step):
    """Animated upload progress steps"""
    bars = {
        1: "[█░░░░░░░░░] 10%",
        2: "[███░░░░░░░] 30%",
        3: "[██████░░░░] 60%",
        4: "[██████████] 100%"
    }
    return bars.get(step, "[░░░░░░░░░░] 0%")

# ==================== BOT INITIALIZATION ====================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# ==================== INLINE KEYBOARD ====================
def get_main_keyboard():
    """Create branded inline keyboard"""
    markup = InlineKeyboardMarkup(row_width=1)
    
    btn1 = InlineKeyboardButton("🔔 SUBSCRIBE CHANNEL", url=YOUTUBE_CHANNEL)
    btn2 = InlineKeyboardButton("📚 ALL TUTORIALS", url=YOUTUBE_CHANNEL + "/videos")
    btn3 = InlineKeyboardButton("📞 CONTACT OWNER", url=SUPPORT_LINK)
    
    markup.add(btn1, btn2, btn3)
    return markup

# ==================== START COMMAND ====================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Premium welcome message for @SAKIB_BHAII"""
    welcome_text = f"""
<b>🎬 Welcome to LINK TO VIDEO DOWNLOADER</b>

<i>Powered by @SAKIB_BHAII</i>

<b>✨ Supported Platforms:</b>
• YouTube (Videos & Shorts)
• Instagram Reels & Posts
• Facebook Videos
• TikTok (No Watermark)
• Twitter/X Videos
• Terabox Links
• And 1800+ other sites!

<b>📥 How to use:</b>
Just send any video link and I'll download it instantly!

<b>⚡ Features:</b>
• HD Quality Downloads
• Fast Processing
• No Watermark (TikTok)
• 24/7 Online

<b>👨‍💻 Developer:</b> @SAKIB_BHAII
    """
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=get_main_keyboard(),
        disable_web_page_preview=True
    )

# ==================== DOWNLOAD HANDLER ====================
class ProgressHook:
    """Custom progress tracker for yt-dlp"""
    def __init__(self, bot, chat_id, message_id):
        self.bot = bot
        self.chat_id = chat_id
        self.message_id = message_id
        self.last_update = 0
        self.download_percent = 0
        self.status_message = "⏳ Analyzing link..."
        
    def __call__(self, d):
        current_time = time.time()
        
        # Update every 2 seconds to avoid flood limits
        if current_time - self.last_update < 2:
            return
            
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            
            if total > 0:
                percent = (downloaded / total) * 100
                self.download_percent = min(percent, 99.9)
                
                status = f"""
🔄 <b>Downloading...</b>
{progress_bar(self.download_percent)}

📦 Size: {self._format_bytes(downloaded)} / {self._format_bytes(total)}
⏱ Speed: {d.get('speed', 'N/A') and self._format_bytes(d.get('speed', 0)) + '/s' or 'Calculating...'}
                """
                
                try:
                    self.bot.edit_message_text(
                        status,
                        self.chat_id,
                        self.message_id,
                        parse_mode='HTML'
                    )
                    self.last_update = current_time
                except Exception:
                    pass
                    
        elif d['status'] == 'finished':
            self.download_percent = 100
            status = f"""
✅ <b>Download Complete!</b>
{progress_bar(100.0)}

📦 Finalizing video...
            """
            try:
                self.bot.edit_message_text(
                    status,
                    self.chat_id,
                    self.message_id,
                    parse_mode='HTML'
                )
            except Exception:
                pass
    
    def _format_bytes(self, bytes_val):
        """Format bytes to human readable"""
        if bytes_val is None or bytes_val == 0:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if abs(bytes_val) < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} TB"

def upload_with_progress(bot, chat_id, message_id, file_path, caption):
    """Upload video with animated progress"""
    file_size = os.path.getsize(file_path)
    
    # Simulate upload steps for visual feedback
    upload_steps = [
        (1, "⬆️ <b>Uploading...</b>\n📦 Upload Complete\n" + upload_bar(1) + "\nInitializing upload..."),
        (2, "⬆️ <b>Uploading...</b>\n📦 Upload Complete\n" + upload_bar(2) + "\nSending video data..."),
        (3, "⬆️ <b>Uploading...</b>\n📦 Upload Complete\n" + upload_bar(3) + "\nAlmost there..."),
        (4, "⬆️ <b>Upload Complete!</b>\n📦 Upload Complete\n" + upload_bar(4) + "\nFinalizing...")
    ]
    
    # Show upload animation
    for step, text in upload_steps:
        try:
            bot.edit_message_text(
                text,
                chat_id,
                message_id,
                parse_mode='HTML'
            )
            time.sleep(0.8)  # Animation delay
        except Exception:
            pass
    
    # Actual upload
    try:
        with open(file_path, 'rb') as video_file:
            bot.send_video(
                chat_id,
                video_file,
                caption=caption,
                supports_streaming=True,
                width=1280,
                height=720
            )
        return True
    except Exception as e:
        print(f"Upload error: {e}")
        return False

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_video_request(message):
    """Handle video download requests"""
    url = message.text.strip()
    chat_id = message.chat.id
    
    # Validate URL
    supported_patterns = [
        'youtube.com', 'youtu.be', 'youtube.com/shorts',
        'instagram.com', 'facebook.com', 'fb.watch',
        'tiktok.com', 'twitter.com', 'x.com',
        'terabox.com', 'terabox.link', '1024tera.com'
    ]
    
    if not any(pattern in url.lower() for pattern in supported_patterns):
        bot.reply_to(
            message,
            "❌ <b>Invalid or unsupported link!</b>\n\nPlease send a valid video URL from:\n• YouTube\n• Instagram\n• Facebook\n• TikTok\n• Twitter/X\n• Terabox\n• Other supported sites",
            parse_mode='HTML'
        )
        return
    
    # Send initial status
    status_msg = bot.reply_to(
        message,
        "⏳ <b>Analyzing link...</b>\n🔍 Fetching video information...",
        parse_mode='HTML'
    )
    
    # Create temp directory
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = int(time.time())
    output_template = os.path.join(temp_dir, f"{chat_id}_{timestamp}_%(title).50s.%(ext)s")
    final_file = os.path.join(temp_dir, f"{chat_id}_{timestamp}_video.mp4")
    
    try:
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'progress_hooks': [ProgressHook(bot, chat_id, status_msg.message_id)],
            'quiet': True,
            'no_warnings': True,
            'cookiesfrombrowser': None,  # Set to ('chrome',) if you have cookies
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }
        
        # Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            if info is None:
                raise Exception("Could not extract video information")
            
            # Find downloaded file
            downloaded_files = [
                f for f in os.listdir(temp_dir) 
                if f.startswith(f"{chat_id}_{timestamp}")
            ]
            
            if not downloaded_files:
                raise Exception("Download failed - file not found")
            
            actual_file = os.path.join(temp_dir, downloaded_files[0])
            
            # Rename to consistent name if needed
            if actual_file != final_file and os.path.exists(actual_file):
                os.rename(actual_file, final_file)
                actual_file = final_file
            
            # Prepare caption
            title = info.get('title', 'Unknown Video')
            uploader = info.get('uploader', 'Unknown')
            duration = info.get('duration', 0)
            
            caption = f"""✅ <b>Downloaded Successfully!</b>

📹 <b>{title[:100]}{'...' if len(title) > 100 else ''}</b>
👤 <b>Channel:</b> {uploader}
⏱ <b>Duration:</b> {time.strftime('%H:%M:%S', time.gmtime(duration)) if duration else 'N/A'}

<b>⚡ Power by:</b> @SAKIB_BHAII
<b>🔰 Bot:</b> @link_mp4_bot
            """
            
            # Update status for upload
            try:
                bot.edit_message_text(
                    f"📦 <b>Download Complete</b>\n{progress_bar(100.0)}\n⬆️ Preparing upload...",
                    chat_id,
                    status_msg.message_id,
                    parse_mode='HTML'
                )
            except Exception:
                pass
            
            # Upload with progress animation
            success = upload_with_progress(
                bot, chat_id, status_msg.message_id, 
                actual_file, caption
            )
            
            if success:
                # Delete status message after successful upload
                try:
                    bot.delete_message(chat_id, status_msg.message_id)
                except Exception:
                    pass
            else:
                bot.edit_message_text(
                    "❌ <b>Upload failed!</b>\nPlease try again later.",
                    chat_id,
                    status_msg.message_id,
                    parse_mode='HTML'
                )
            
            # Cleanup - Delete file immediately after sending
            if os.path.exists(actual_file):
                os.remove(actual_file)
                print(f"Cleaned up: {actual_file}")
                
    except DownloadError as e:
        error_msg = str(e)
        if "login required" in error_msg.lower() or "rate-limit" in error_msg.lower():
            bot.edit_message_text(
                "❌ <b>This content requires authentication or is rate-limited!</b>\n\nFor Instagram/Facebook private content, cookies may be needed.",
                chat_id,
                status_msg.message_id,
                parse_mode='HTML'
            )
        elif "unsupported url" in error_msg.lower():
            bot.edit_message_text(
                "❌ <b>Unsupported URL format!</b>\nPlease check the link and try again.",
                chat_id,
                status_msg.message_id,
                parse_mode='HTML'
            )
        else:
            bot.edit_message_text(
                f"❌ <b>Download Error:</b>\n<code>{error_msg[:200]}</code>",
                chat_id,
                status_msg.message_id,
                parse_mode='HTML'
            )
            
    except Exception as e:
        print(f"Error: {e}")
        try:
            bot.edit_message_text(
                "❌ <b>An error occurred!</b>\nPlease try again with a different link.",
                chat_id,
                status_msg.message_id,
                parse_mode='HTML'
            )
        except Exception:
            bot.reply_to(message, "❌ An error occurred while processing your request.")
    
    finally:
        # Ensure cleanup happens even if upload fails
        if os.path.exists(final_file):
            try:
                os.remove(final_file)
                print(f"Final cleanup: {final_file}")
            except Exception as e:
                print(f"Cleanup error: {e}")

# ==================== ERROR HANDLER ====================
@bot.message_handler(content_types=['photo', 'video', 'document', 'audio'])
def handle_media(message):
    bot.reply_to(
        message,
        "❌ Please send a <b>text link</b> only!\n\nI can download videos from URLs, not uploaded files.",
        parse_mode='HTML'
    )

# ==================== MAIN ====================
if __name__ == "__main__":
    print("🤖 Starting SAKIB DOWNLOADER BOT...")
    print(f"📺 YouTube: {YOUTUBE_CHANNEL}")
    print(f"📞 Support: {SUPPORT_LINK}")
    
    # Start keep-alive server
    keep_alive()
    
    # Start bot with infinity polling
    print("✅ Bot is running 24/7!")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
