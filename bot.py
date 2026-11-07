import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import edge_tts
import asyncio
import subprocess

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "745338419:AAHVk8eitszyJjr_Z6Ku1liX6V3D1CU_n8k")

# Dictionary to temporarily store user session states
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **Advanced Movie Recap Bot** မှ ကြိုဆိုပါတယ်ဗျ!\n\n"
        "၁။ ဗီဒီယိုဖိုင်ကို ပို့ပါ။\n"
        "၂။ ဗီဒီယိုထဲမှ အသံကို ထုတ်ယူပေးပါမည်။ (အသံဖိုင် သို့မဟုတ် ဇာတ်လမ်းအကျဉ်းကို Gemini တွင် ဘာသာပြန်ပါ)\n"
        "၃။ ဘာသာပြန်စာသားကို Bot ဆီသို့ ပြန်ပို့ပြီး အသံအမျိုးအစား ရွေးချယ်ပါ။"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    video = update.message.video or update.message.document
    
    if not video:
        return

    msg = await update.message.reply_text("📥 ဗီဒီယိုကို လက်ခံရရှိပါပြီ။ အသံဖိုင် (Audio) ထုတ်ယူနေပါပြီ...")
    
    # Download video file
    file = await context.bot.get_file(video.file_id)
    input_video_path = f"input_{user_id}.mp4"
    audio_path = f"audio_{user_id}.mp3"
    
    await file.download_to_drive(input_video_path)
    
    # Extract audio using ffmpeg
    subprocess.run(["ffmpeg", "-y", "-i", input_video_path, "-vn", "-acodec", "libmp3lame", audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    user_sessions[user_id] = {
        "video_path": input_video_path,
        "audio_path": audio_path
    }
    
    # Send extracted audio to user so they can transcribe/translate easily using Gemini
    with open(audio_path, "rb") as aud:
        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=aud, caption="🎧 ထုတ်ယူထားသော အသံဖိုင် (Audio) ဖြစ်ပါသည်။ ဤဖိုင် သို့မဟုတ် ဇာတ်လမ်းအကျဉ်းကို Gemini တွင် မြန်မာလို ဘာသာပြန်ပြီး ဤရုပ်သံချတ်ထဲသို့ ပြန်လည်ပေးပို့ပါခင်ဗျ။")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_sessions:
        await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ ပထမဦးစွာ ဗီဒီယိုဖိုင်တစ်ခုကို အရင်ပို့ပေးပါခင်ဗျ။")
        return

    # Store translated text from user
    user_sessions[user_id]["translated_text"] = text

    # Show voice and speed selection buttons
    keyboard = [
        [
            InlineKeyboardButton("♀️ Nilar (Female)", callback_data="voice_nilar"),
            InlineKeyboardButton("♂️ WinTun (Male)", callback_data="voice_wintun")
        ],
        [
            InlineKeyboardButton("⚡ 1.25x", callback_data="speed_1.25"),
            InlineKeyboardButton("⚡ 1.5x", callback_data="speed_1.5"),
            InlineKeyboardButton("⚡ 2.0x", callback_data="speed_2.0")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ မြန်မာဘာသာပြန်ချက်ကို လက်ခံရရှိပါပြီ။\n\n🎙️ အသံအမျိုးအစားနှင့် အမြန်နှုန်းကို ရွေးချယ်ပါ -",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await query.edit_message_text("⚠️ Session သက်တမ်းကုန်သွားပါပြီ။ ဗီဒီယိုကို အစကနေ ပြန်ပို့ပေးပါ။")
        return

    data = query.data
    if data.startswith("voice_"):
        user_sessions[user_id]["voice"] = "my-MM-NilarNeural" if data == "voice_nilar" else "my-MM-WinTunNeural"
        await query.edit_message_text(f"✅ အသံအမျိုးအစား ရွေးချယ်ပြီးပါပြီ: {'Nilar (အမျိုးသမီး)' if data == 'voice_nilar' else 'WinTun (အမျိုးသား)'}\n\nအမြန်နှုန်း (Speed) ကို ဆက်လက်ရွေးချယ်ပါ။")
        return
    
    elif data.startswith("speed_"):
        speed_val = float(data.split("_")[1])
        user_sessions[user_id]["speed"] = speed_val

        await query.edit_message_text("🔄 ဗီဒီယိုထုတ်လုပ်ခြင်း (Smart Audio Mixing) လုပ်ဆောင်နေပါပြီ... ခဏစောင့်ပေးပါ။")

        session = user_sessions[user_id]
        video_path = session["video_path"]
        translated_text = session["translated_text"]
        voice = session.get("voice", "my-MM-NilarNeural")
        
        tts_audio = f"tts_{user_id}.mp3"
        final_video = f"final_{user_id}.mp4"

        try:
            # Generate Edge-TTS audio
            communicate = edge_tts.Communicate(translated_text, voice)
            await communicate.save(tts_audio)

            # Process with ffmpeg (Audio Ducking & Mixing)
            cmd = [
                "ffmpeg", "-y", "-i", video_path, "-i", tts_audio,
                "-filter_complex", "[0:a]volume=0.2[a0];[1:a]atempo=1.0[a1];[a0][a1]amix=inputs=2:duration=first[a]",
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", final_video
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Send final video
            with open(final_video, "rb") as vid:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=vid, caption="🎬 သင့်ရဲ့ Movie Recap ဗီဒီယို အဆင်သင့်ဖြစ်ပါပြီ!")

        except Exception as e:
            logger.error(f"Processing error: {e}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ ဗီဒီယိုထုတ်လုပ်ရာတွင် အမှားအယွင်း ဖြစ်ပေါ်သွားပါသည်။")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling()

if __name__ == "__main__":
    main()
