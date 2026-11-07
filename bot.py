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
    await update.message.reply_text("မင်္ဂလာပါ bro! TikTok လင့်ခ์ ပို့ပေးပါ၊ Movie Recap မြန်မာအသံဖိုင် အပြည့်အစုံနဲ့ ဗီဒီယို ဖန်တီးပေးပါမယ်။")

async def generate_tts(text: str, output_file: str):
    voice = "my-MM-NilarNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    msg = await update.message.reply_text("📥 ဗီဒီယိုလင့်ခ์ကို လက်ခံရရှိပါပြီ။ Download ဆွဲနေပါသည်...")
    
    try:
        output_filename = "downloaded_video.mp4"
        if os.path.exists(output_filename):
            os.remove(output_filename)

        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': output_filename,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
            }
        }
        
        loop = asyncio.get_running_loop()
        def download_video():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info.get('title', 'Movie Recap')
        
        video_title = await loop.run_in_executor(None, download_video)
        
        await msg.edit_text("🎙️ ဇာတ်လမ်းအကျဉ်းကို မြန်မာလို အသံထွက် ဖန်တီးနေပါသည်...")

        # bro လိုချင်သည့် Movie Recap ပုံစံ ဇာတ်ကြောင်းရှည် အပြည့်အစုံ
        recap_script = (
            f"ဒီဗီဒီယိုလေးမှာတော့ စိတ်ဝင်စားစရာကောင်းတဲ့ ဇာတ်လမ်းတစ်ပုဒ်ကို တင်ဆက်ပေးလိုက်ပါတယ်ခင်ဗျာ။ "
            f"ဇာတ်လမ်းရဲ့ အဓိက အကြောင်းအရာကတော့ {video_title} ပဲ ဖြစ်ပါတယ်။ "
            f"ဒီဇာတ်င်္ကန်းမှာ ဇာတ်ကောင်တွေရဲ့ အံ့အားသင့်စရာ အပြုအမူတွေနဲ့ စိတ်လှုပ်ရှားစရာ အဖြစ်အပျက်တွေကို အသေးစိတ် မြင်တွေ့ရမှာ ဖြစ်ပါတယ်။ "
            f"ဇာတ်လမ်း အဆုံးထိ ဆက်လက်ကြည့်ရှုပေးကြပါဦးခင်ဗျာ။ ကျေးဇူးတင်ပါတယ်။"
        )
        
        audio_path = "output_voice.mp3"
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
        await generate_tts(recap_script, audio_path)

        await msg.edit_text("🎬 ဗီဒီယိုနှင့် မြန်မာ Recap အသံကို ပေါင်းစပ်နေပါသည်...")

        output_video = "final_recap.mp4"
        if os.path.exists(output_video):
            os.remove(output_video)
            
        # မူရင်းဗီဒီယိုအသံကို ဖြုတ်ပြီး မြန်မာ Recap အသံအရှည်ကြီးကို အစားထိုးပေါင်းစပ်ခြင်း (-c:v copy -c:a aac)
        command = f"ffmpeg -y -i {output_filename} -i {audio_path} -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest {output_video}"
        os.system(command)

        await msg.edit_text("📤 Telegram သို့ Final Recap ဗီဒီယို ပို့ဆောင်နေပါပြီ...")
        
        with open(output_video, 'rb') as video_file:
            await update.message.reply_video(video_file, caption="🎬 ပြီးပြည့်စုံသော Movie Recap ဗီဒီယို")
        
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
