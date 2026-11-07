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
    await update.message.reply_text("မင်္ဂလာပါ bro! TikTok လင့်ခ์ ပို့ပေးပါ၊ Movie Recap ဗီဒီယို အမြန်ဆုံး ဖန်တီးပေးပါမယ်။")

async def generate_tts(text: str, output_file: str):
    voice = "my-MM-NilarNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    msg = await update.message.reply_text("📥 ဗီဒီယိုလင့်ခ์ကို လက်ခံရရှိပါပြီ။ `yt-dlp` ဖြင့် Download ဆွဲနေပါသည်...")
    
    try:
        # 1. Video Download & Info extraction
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'downloaded_video.mp4',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'ဇာတ်လမ်းအကျဉ်း')

        await msg.edit_text("🎙️ ဗီဒီယို ဒေါင်းလုဒ်ပြီးပါပြီ။ မြန်မာ AI ဇာတ်လမ်းအသံ ဖန်တီးနေပါသည်...")

        # 2. Generate Burmese AI Voiceover based on video title/context
        recap_script = f"ဒီဗီဒီယိုလေးရဲ့ ဇာတ်လမ်းအကျဉ်းကတော့ {video_title} ပဲ ဖြစ်ပါတယ်။ ဆက်လက်ကြည့်ရှုပေးကြပါဦးခင်ဗျာ။"
        audio_path = "output_voice.mp3"
        await generate_tts(recap_script, audio_path)

        await msg.edit_text("🎬 ဗီဒီယိုနှင့် မြန်မာ AI အသံဖိုင်ကို FFmpeg ဖြင့် ပေါင်းစပ်နေပါသည်...")

        # 3. Merge Video and Audio using FFmpeg
        output_video = "final_recap.mp4"
        command = f"ffmpeg -y -i downloaded_video.mp4 -i {audio_path} -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest {output_video}"
        os.system(command)

        await msg.edit_text("📤 Telegram ထဲသို့ Final Recap ဗီဒီယို ပို့ဆောင်နေပါပြီ...")
        
        # 4. Send Final Video to Telegram
        with open(output_video, 'rb') as video_file:
            await update.message.reply_video(video_file, caption="🎬 ပြီးပြည့်စုံသော One-Click Movie Recap ဗီဒီယို")
        
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
