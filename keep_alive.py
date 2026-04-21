from flask import Flask, render_template_string
from threading import Thread
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>BLACK KNOWLEDGE DOWNLOADER</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            max-width: 600px;
            width: 90%;
        }
        .status {
            display: inline-block;
            width: 15px;
            height: 15px;
            background: #00ff88;
            border-radius: 50%;
            margin-right: 10px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        h1 { color: #00ff88; margin-bottom: 10px; }
        .info { color: #aaa; margin: 20px 0; }
        .platforms {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
        }
        .platform {
            background: rgba(0,255,136,0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            border: 1px solid #00ff88;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1><span class="status"></span>Bot is Online</h1>
        <div class="info">BLACK KNOWLEDGE VIDEO DOWNLOADER</div>
        <div class="platforms">
            <span class="platform">YouTube</span>
            <span class="platform">Instagram</span>
            <span class="platform">Facebook</span>
            <span class="platform">TikTok</span>
            <span class="platform">Twitter/X</span>
            <span class="platform">Terabox</span>
        </div>
        <div class="info">Powered by @BLACK_KNOWLEDGE_190</div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return {"status": "alive", "service": "telegram-bot"}, 200

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()
    print(f"🌐 Keep-alive server running on port {os.environ.get('PORT', 10000)}")
