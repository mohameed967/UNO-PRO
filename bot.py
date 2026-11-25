import os
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from database import store

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if u: store.register_user(u.id, u.username or '', u.first_name or '')
    if not WEBAPP_URL.startswith("https://"):
        await update.message.reply_text(
            "مرحباً بك في UNO PRO!\n"
            "اللعبة قيد التجهيز. يجب ضبط WEBAPP_URL برابط HTTPS بعد رفع الموقع للاستضافة."
        )
        return

    keyboard = [[InlineKeyboardButton(
        "🎮 افتح UNO PRO",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )]]
    await update.message.reply_text(
        "أهلاً بك في UNO PRO 🃏\nاضغط الزر لبدء اللعب!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Add it to your .env file.")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("UNO PRO bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
