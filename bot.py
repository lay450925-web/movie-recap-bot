import os
import logging
import asyncio
import edge_tts
import whisper
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

BOT_TOKEN = "9174538419:AAGV5mHqizy_Jr_ZGKu1LisXEV3DlCU_z8k"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Advanced Movie Recap Bot is running 24/7!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ bro! 🎬 Advanced Movie Recap Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "လုပ်ဆောင်ပုံ:\n"
        "၁။ မူရင်းဗီဒီယို ပို့ပါ။ (Whisper ဖြင့် Transcript ထုတ်ပေးပါမည်)\n"
        "၂။ Gemini တွင် မြန်မာလို ဘာသာပြန်ပြီး Bot ဆီသို့ ပြန်ပို့ပါ။\n"
        "၃။ အသံအမျိုးအစားနှင့် အမြန်နှုန်းကို ရွေးချယ်နိုင်သော ခလုတ်များ ပေါ်လာပါမည်။"
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if update.message.video:
        msg = await update.message.reply_text("📥 ဗီဒီယိုကို လက်ခံရရှိပါပြီ။ Whisper ဖြင့် အင်္ဂလိပ် Transcript ထုတ်နေပါပြီ...")
        
        try:
            video_file = await update.message.video.get_file()
            input_video = f"video_{user_id}.mp4"
            if os.path.exists(input_video):
                os.remove(input_video)
            await video_file.download_to_drive(input_video)
            
            extracted_audio = f"audio_{user_id}.mp3"
            if os.path.exists(extracted_audio):
                os.remove(extracted_audio)
            os.system(f"ffmpeg -y -i {input_video} -q:a 0 -map a {extracted_audio}")

            model = whisper.load_model("base")
            result = model.transcribe(extracted_audio)
            
            english_transcript = ""
            for segment in result["segments"]:
                english_transcript += f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}\n"

            user_states[user_id] = {
                "input_video": input_video,
                "voice": "my-MM-NilarNeural",
                "rate": "+0%"
            }

            await msg.edit_text(
                "✅ **Transcript ထွက်လာပါပြီ။**\n\n"
                "အောက်ပါ စာသားများကို ကူးယူပြီး **Gemini** တွင် မြန်မာလို ဘာသာပြန်ကာ၊ ပြီးလျှင် အဲ့ဒီမြန်မာစာသားကို ဤ Bot ဆီသို့ ပြန်ပို့ပေးပါခင်ဗျာ။\n\n"
                f"{english_transcript[:4000]}"
            )
            
            if len(english_transcript) > 4000:
                await update.message.reply_text(english_transcript[4000:])

        except Exception as e:
            await msg.edit_text(f"❌ Error ဖြစ်သွားပါသည်: {str(e)}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if update.message.text:
        if user_id not in user_states or "input_video" not in user_states[user_id]:
            await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ ပထမဦးစွာ မူရင်း ဗီဒီယိုဖိုင်ကို ပို့ပေးပါခင်ဗျာ။")
            return

        user_states[user_id]["burmese_text"] = update.message.text

        keyboard = [
            [
                InlineKeyboardButton("👩‍🦰 Nilar (မိန်းကလေးသံ)", callback_data="voice_nilar"),
                InlineKeyboardButton("👨‍💼 WinTun (ယောကျ်ားလေးသံ)", callback_data="voice_wintun")
            ],
            [
                InlineKeyboardButton("⏩ ပုံမှန် (1.0x)", callback_data="speed_normal"),
                InlineKeyboardButton("🚀 အမြန် (1.15x)", callback_data="speed_fast")
            ],
            [
                InlineKeyboardButton("🎬 ✅ အသံသွင်းပြီး ဗီဒီယိုထုတ်မည်", callback_data="process_video")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🎛️ **အသံ ဆက်တင်များ ရွေးချယ်ပါ:**\n\n"
            f"• လက်ရှိ အသံ: {user_states[user_id]['voice']}\n"
            f"• လက်ရှိ အမြန်နှုန်း: {user_states[user_id]['rate']}\n\n"
            "ကြိုက်နှစ်သက်ရာကို ရွေးချယ်ပြီးပါက 'အသံသွင်းပြီး ဗီဒီယိုထုတ်မည်' ကို နှိပ်ပါ။",
            reply_markup=reply_markup
        )

def get_settings_keyboard(state):
    keyboard = [
        [
            InlineKeyboardButton("👩‍🦰 Nilar", callback_data="voice_nilar"),
            InlineKeyboardButton("👨‍💼 WinTun", callback_data="voice_wintun")
        ],
        [
            InlineKeyboardButton("⏩ ပုံမှန် (1.0x)", callback_data="speed_normal"),
            InlineKeyboardButton("🚀 အမြန် (1.15x)", callback_data="speed_fast")
        ],
        [
            InlineKeyboardButton("🎬 ✅ အသံသွင်းပြီး ဗီဒီယိုထုတ်မည်", callback_data="process_video")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_states:
        await query.edit_message_text("⚠️ အချက်အလက်များ သက်တမ်းကုန်သွားပါပြီ။ ဗီဒီယိုအသစ် ပြန်စပါ။")
        return

    data = query.data

    if data == "voice_nilar":
        user_states[user_id]["voice"] = "my-MM-NilarNeural"
        await query.edit_message_text("✅ အသံကို Nilar (မိန်းကလေးသံ) သို့ ပြောင်းပြီးပါပြီ။", reply_markup=get_settings_keyboard(user_states[user_id]))
    elif data == "voice_wintun":
        user_states[user_id]["voice"] = "my-MM-WinTunNeural"
        await query.edit_message_text("✅ အသံကို WinTun (ယောကျ်ားလေးသံ) သို့ ပြောင်းပြီးပါပြီ။", reply_markup=get_settings_keyboard(user_states[user_id]))
    elif data == "speed_normal":
        user_states[user_id]["rate"] = "+0%"
        await query.edit_message_text("✅ အမြန်နှုန်း: ပုံမှန် (1.0x)", reply_markup=get_settings_keyboard(user_states[user_id]))
    elif data == "speed_fast":
        user_states[user_id]["rate"] = "+15%"
        await query.edit_message_text("✅ အမြန်နှုန်း: အနည်းငယ်မြန် (1.15x)", reply_markup=get_settings_keyboard(user_states[user_id]))
    elif data == "process_video":
        await query.edit_message_text("🎙️ ရွေးချယ်ထားသော ဆက်တင်များဖြင့် အသံသွင်းခြင်းနှင့် ဗီဒီယို ပေါင်းစပ်ခြင်း စတင်နေပါပြီ...")
        await generate_final_video(query.message, user_id)

async def generate_final_video(message, user_id):
    state = user_states[user_id]
    input_video = state["input_video"]
    burmese_text = state["burmese_text"]
    voice = state.get("voice", "my-MM-NilarNeural")
    rate = state.get("rate", "+0%")

    audio_path = f"output_voice_{user_id}.mp3"
    output_video = f"final_recap_{user_id}.mp4"
    srt_path = f"subtitle_{user_id}.srt"

    try:
        communicate = edge_tts.Communicate(burmese_text, voice, rate=rate)
        await communicate.save(audio_path)

        mix_command = (
            f"ffmpeg -y -i {input_video} -i {audio_path} "
            f"-filter_complex \"[0:a]volume=0.1[orig];[1:a]volume=1.2[voice];"
            f"[orig][voice]amix=inputs=2:duration=first:dropout_transition=2[aout]\" "
            f"-map 0:v:0 -map \"[aout]\" -shortest {output_video}"
        )
        os.system(mix_command)

        with open(srt_path, "w", encoding="utf-8") as srt_file:
            srt_file.write("1\n00:00:00,000 --> 00:00:15,000\n" + burmese_text[:150] + "\n\n")
            srt_file.write("2\n00:00:15,000 --> 00:00:35,000\n" + burmese_text[150:400] + "\n\n")

        await message.reply_video(open(output_video, 'rb'), caption="🎬 ပြီးပြည့်စုံသော Smart Audio Movie Recap ဗီဒီယို")
        await message.reply_document(open(srt_path, 'rb'), caption="📄 Recap SRT Subtitle ဖိုင်")

        del user_states[user_id]

    except Exception as e:
        await message.reply_text(f"❌ Error ဖြစ်သွားပါသည် bro: {str(e)}")

def main():
    threading.Thread(target=run_web_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("🤖 Advanced Movie Recap Bot စတင်လည်ပတ်နေပြီ...")
    app.run_polling()

if __name__ == '__main__':
    main()
