import os
import logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "9174538419:AAGV5mHqizy_Jr_ZGKu1LisXEV3DlCU_z8k"

# Render အတွက် Dummy Web Server (Port ဖွင့်ပေးရန်)
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_message = (
        f"မင်္ဂလာပါ bro {user_name}!\n\n"
        "🎬 **One-Click Movie Recap Bot** မှ ကြိုဆိုပါတယ်။\n"
        "ဗီဒီယိုလင့်ခ์ (သို့မဟုတ်) ဗီဒီယိုဖိုင်ကို ပေးပို့ပါ။"
    )
    keyboard = [
        [InlineKeyboardButton("⚙️ AI အသံ ရွေးရန်", callback_data='set_voice')],
        [InlineKeyboardButton("🚀 စတင်ဖန်တီးမည်", callback_data='start_render')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    msg = await update.message.reply_text("📥 ဗီဒီယိုလင့်ခ์ကို လက်ခံရရှိပါပြီ။ `yt-dlp` ဖြင့် Download ဆွဲနေပါသည်...")
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'downloaded_video.mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        await msg.edit_text("✅ ဗီဒီယို Download ဆွဲခြင်း ပြီးဆုံးပါပြီ!")
    except Exception as e:
        await msg.edit_text(f"❌ Error ဖြစ်သွားပါသည် bro: {str(e)}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'set_voice':
        await query.edit_message_text(text="🎙️ အသံအမျိုးအစား ရွေးချယ်မှု အဆင်သင့်ဖြစ်ပါပြီ။")
    elif query.data == 'start_render':
        await query.edit_message_text(text="⚙️ စတင်ដំណើរការနေပါပြီ။")

def main():
    # Background မှာ Web Server ကို Run ပေးခြင်း (Render Port Error ကာကွယ်ရန်)
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_media))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 Bot အောင်မြင်စွာ စတင်လည်ပတ်နေပြီ...")
    app.run_polling()

if __name__ == '__main__':
    main()
