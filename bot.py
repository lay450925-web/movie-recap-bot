import os
import logging
import asyncio
import edge_tts
from faster_whisper import WhisperModel
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Bot Token ကို ထည့်ပါ
BOT_TOKEN = "9174538419:AAGV5mHqizy_Jr_ZGKu1LisXEV3DlCU_z8k"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Render Web Server (Uptime Robot ဖြင့် 24/7 ချိတ်ဆက်ရန်)
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Semi-Auto Movie Recap Bot is running 24/7!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# User တစ်ဦးချင်းစီအတွက် အချက်အလက်များကို သိမ်းဆည်းရန် (State Management)
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ bro! 🎬 Semi-Auto Movie Recap Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "လုပ်ဆောင်ပုံ အဆင့်ဆင့်:\n"
        "၁။ မူရင်း အင်္ဂလိပ်ဗီဒီယိုကို ပို့ပါ။ (Bot က အင်္ဂလိပ် Transcript ထုတ်ပေးပါမည်)\n"
        "၂။ အဲ့ဒီ Transcript ကို Gemini မှာ မြန်မာလို ဘာသာပြန်ပါ။\n"
        "၃။ ဘာသာပြန်ပြီးသား မြန်မာစာသားကို Bot ဆီသို့ ပြန်ပို့ပါ။ (Bot က အသံသွင်း၊ ဗီဒီယိုပေါင်း၊ SRT ဖိုင်ထုတ်ပေးပါမည်)"
    )

async def handle_video_or_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # အကယ်၍ User က ဗီဒီယို ပို့လာလျှင်
    if update.message.video:
        msg = await update.message.reply_text("📥 ဗီဒီယိုကို လက်ခံရရှိပါပြီ။ အသံဖိုင်ထုတ်ယူပြီး Whisper ဖြင့် စာသား (Transcript) ထုတ်နေပါပြီ...")
        
        try:
            video_file = await update.message.video.get_file()
            input_video = "uploaded_video.mp4"
            if os.path.exists(input_video):
                os.remove(input_video)
            await video_file.download_to_drive(input_video)
            
            # Extract Audio
            extracted_audio = "extracted_audio.mp3"
            if os.path.exists(extracted_audio):
                os.remove(extracted_audio)
            os.system(f"ffmpeg -y -i {input_video} -q:a 0 -map a {extracted_audio}")

            # Local Whisper ဖြင့် အင်္ဂလိပ် Transcript ထုတ်ခြင်း (Free & Local)
            # base model ကို သုံးထားပါသည် (Render RAM အတွက် အသင့်တော်ဆုံး)
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, info = model.transcribe(extracted_audio, beam_size=5)
            
            english_transcript = ""
            for segment in segments:
                english_transcript += f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n"

            # ဗီဒီယိုဖိုင် လမ်းကြောင်းကို user_states တွင် သိမ်းထားမည်
            user_states[user_id] = {
                "input_video": input_video
            }

            await msg.edit_text(
                "✅ **အင်္ဂလိပ် Transcript ထွက်လာပါပြီ။**\n\n"
                "အောက်ပါ စာသားများကို ကူးယူပြီး **Gemini** တွင် သဘာဝကျကျ မြန်မာလို ဘာသာပြန်ဆိုကာ၊ ပြီးလျှင် အဲ့ဒီမြန်မာစာသားကို ဤ Bot ဆီသို့ ပြန်လည် ပို့ပေးပါခင်ဗျာ။\n\n"
                f"{english_transcript[:4000]}"  # Telegram မက်ဆေ့ခ်ျ ကန့်သတ်ချက်အတွက် အပိုင်းလိုက်ပြခြင်း
            )
            
            if len(english_transcript) > 4000:
                # ကျန်စာသားများ ပို့ရန်
                await update.message.reply_text(english_transcript[4000:])

        except Exception as e:
            await msg.edit_text(f"❌ Error ဖြစ်သွားပါသည်: {str(e)}")

    # အကယ်၍ User က မြန်မာဘာသာပြန်စာသား ပို့လာလျှင် (Text Message)
    elif update.message.text:
        if user_id not in user_states or "input_video" not in user_states[user_id]:
            await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ ပထမဦးစွာ မူရင်း ဗီဒီယိုဖိုင်ကို ပို့ပေးပါခင်ဗျာ။")
            return

        burmese_text = update.message.text
        input_video = user_states[user_id]["input_video"]
        
        msg = await update.message.reply_text("🎙️ မြန်မာစာသားကို AI အသံ (Edge-TTS) ဖြင့် အသံသွင်းနေပါပြီ...")

        try:
            # 1. Generate Voice (Voice: my-MM-NilarNeural)
            audio_path = "output_voice.mp3"
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
            voice = "my-MM-NilarNeural"
            communicate = edge_tts.Communicate(burmese_text, voice)
            await communicate.save(audio_path)

            await msg.edit_text("🎬 မူရင်းအသံဖျောက်၊ အသံအသစ်ထည့်ကာ ဗီဒီယိုနှင့် SRT ဖိုင် တည်ဆောက်နေပါပြီ...")

            # 2. Merge Video and New Audio (Mute original audio, add new voice)
            output_video = "final_recap.mp4"
            if os.path.exists(output_video):
                os.remove(output_video)
                
            command = f"ffmpeg -y -i {input_video} -i {audio_path} -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest {output_video}"
            os.system(command)

            # 3. Generate SRT Subtitle file from the Burmese text/audio duration
            srt_path = "recap_subtitle.srt"
            if os.path.exists(srt_path):
                os.remove(srt_path)
                
            # ရိုးရှင်းသော SRT ဖိုင် တည်ဆောက်ပုံ (စာသားအပေါ်မူတည်၍ အချိန်ညှိခြင်း)
            with open(srt_path, "w", encoding="utf-8") as srt_file:
                srt_file.write("1\n00:00:00,000 --> 00:00:10,000\n" + burmese_text[:100] + "\n\n")
                srt_file.write("2\n00:00:10,000 --> 00:00:25,000\n" + burmese_text[100:300] + "\n\n")
                # လိုအပ်ပါက အရှည်အထွာအလိုက် အသေးစိတ် SRT ထပ်မံခွဲထုတ်နိုင်ပါသည်

            await msg.edit_text("📤 Final Recap ဗီဒီယိုနှင့် SRT ဖိုင်ကို ပို့ဆောင်နေပါပြီ...")

            # 4. Send Video and SRT File
            with open(output_video, 'rb') as f_video:
                await update.message.reply_video(f_video, caption="🎬 ပြီးပြည့်စုံသော မြန်မာ AI Movie Recap ဗီဒီယို")

            with open(srt_path, 'rb') as f_srt:
                await update.message.reply_document(f_srt, caption="📄 Recap SRT Subtitle ဖိုင်")

            await msg.delete()
            # ပြီးသွားလျှင် State များကို ရှင်းလင်းမည်
            del user_states[user_id]

        except Exception as e:
            await msg.edit_text(f"❌ Error ဖြစ်သွားပါသည် bro: {str(e)}")

def main():
    # 24/7 Web Server for Render Uptime
    threading.Thread(target=run_web_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    # ဗီဒီယိုဖိုင်ရော၊ စာသားမက်ဆေ့ခ်ျပါ နှစ်ခုစလုံးကို လက်ခံရန် Handler
    app.add_handler(MessageHandler(filters.VIDEO | filters.TEXT & ~filters.COMMAND, handle_video_or_text))
    
    print("🤖 Semi-Auto Movie Recap Bot စတင်လည်ပတ်နေပြီ...")
    app.run_polling()

if __name__ == '__main__':
    main()
