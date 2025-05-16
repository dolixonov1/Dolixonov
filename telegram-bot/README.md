# VortexFetchBot

A universal Telegram bot to fetch and download videos from social networks (YouTube, Instagram, TikTok, and more) directly to your chat.

## 🚀 Features
- Download videos from YouTube, Instagram, TikTok, and many other platforms
- Fast, reliable, and easy to use
- Friendly user experience with clear feedback and error messages
- Designed for free hosting (Railway, Heroku, etc.)

## 🛠 Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/xamidullayevI/VortexFetchBot.git
   cd VortexFetchBot
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your Telegram bot token:
   ```env
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
   ```

## 🚦 Deploy on Railway
1. Push this repo to your Railway project.
2. Set the `TELEGRAM_BOT_TOKEN` environment variable in Railway dashboard.
3. Deploy and enjoy!

## 💡 Usage
- Start the bot on Telegram
- Send any video link (YouTube, Instagram, TikTok, etc.)
- The bot will download and send the video directly to your chat

## 📁 Project Structure
```
VortexFetchBot/
├── bot/
│   ├── __init__.py
│   ├── handlers.py
│   ├── downloader.py
│   └── utils.py
├── main.py
├── requirements.txt
├── .env.example
├── Procfile
└── README.md
```

---

Made with ❤️ by @xamidullayevI
