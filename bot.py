import os
import logging
import asyncio
import yt_dlp
import edge_tts
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "9174538419:AAGV5mHqizy_Jr_ZGKu1LisXEV3DlCU_z8k"

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("မင်္ဂလာပါ bro! ဗီဒီယိုလင့်ခ์ ပို့ပေးပါ၊ AI အသံဖိုင်ပါ တစ်ခါတည်း ဖန်တီးပေးပါမယ်။")

async def generate_tts(text: str, output_file: str):
    voice = "my-MM-NilarNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    msg = await update.message.reply_text("📥 ဗီဒီယိုလင့်ခ์ကို လက်ခံရရှိပါပြီ။ `yt-dlp` ဖြင့် Download ဆွဲနေပါသည်...")
    
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'downloaded_video.mp4',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        await msg.edit_text("🎙️ ဗီဒီယို ဒေါင်းလုဒ်ပြီးပါပြီ။ AI အသံဖိုင် ဆက်လက် ဖန်တီးနေပါသည်...")

        # AI Voiceover Text (နောက်ပိုင်း လိုသလို ပြင်လို့ရပါတယ်)
        recap_script = "ဒီဗီဒီယိုလေးကတော့ One-Click Movie Recap Bot ရဲ့ အလိုအလျောက် ထုတ်လုပ်ထားတဲ့ ဇာတ်လမ်းအကျဉ်းပဲ ဖြစ်ပါတယ်။"
        audio_path = "output_voice.mp3"
        await generate_tts(recap_script, audio_path)

        await msg.edit_text("📤 Telegram ထဲသို့ ဗီဒီယိုနှင့် AI အသံဖိုင် ပို့ဆောင်နေပါပြီ...")
        
        with open('downloaded_video.mp4', 'rb') as video_file:
            await update.message.reply_video(video_file, caption="🎬 ဒေါင်းလုဒ်ဆွဲထားသော ဗီဒီယို")
        
        with open(audio_path, 'rb') as audio_file:
            await update.message.reply_audio(audio_file, caption="🎙️ AI အသံဖိုင် (Voiceover)")
        
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Error ဖြစ်သွားပါသည် bro: {str(e)}")

def main():
    threading.Thread(target=run_web_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_media))
    
    print("🤖 Bot အောင်မြင်စွာ စတင်လည်ပတ်နေပြီ...")
    app.run_polling()

if __name__ == '__main__':
    main()
