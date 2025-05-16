import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from bot.handlers import start, help_command, handle_message, extract_audio, handle_quality_selection

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env file")

def main():
    from telegram.request import HTTPXRequest
    request = HTTPXRequest(read_timeout=300, connect_timeout=60)
    application = Application.builder() \
        .token(TOKEN) \
        .request(request) \
        .build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(extract_audio, pattern=r"^get_audio:"))
    application.add_handler(CallbackQueryHandler(handle_quality_selection, pattern=r"^quality:"))

    print("Bot started...")
    application.run_polling()

if __name__ == "__main__":
    main()
