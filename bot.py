import os
import logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "9174538419:AAGV5mHqizy_Jr_ZGKu1LisXEV3DlCU_z8k"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_message = (
        f"မင်္ဂလာပါ bro {user_name}!\n\n"
        "🎬 **One-Click Movie Recap Bot** မှ ကြိုဆိုပါတယ်။\n"
        "ဤ Bot ဖြင့် English Recap ဗီဒီယိုများကို မြန်မာလို အလိုအလျောက် ပြောင်းလဲနိုင်ပါပြီ။\n\n"
        "ဗီဒီယိုလင့်ခ์ (သို့မဟုတ်) ဗီဒီယိုဖိုင်ကို ပေးပို့ပါ။"
    )
    
    keyboard = [
        [InlineKeyboardButton("⚙️ AI အသံ ရွေးရန် (Boy/Girl)", callback_data='set_voice')],
        [InlineKeyboardButton("🎵 BGM & Copyright Bypass", callback_data='set_bgm')],
        [InlineKeyboardButton("⚡ Speed & Pitch ချိန်ရန်", callback_data='set_speed')],
        [InlineKeyboardButton("🚀 စတင်ဖန်တီးမည် (Render)", callback_data='start_render')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

# Handle incoming Video links
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
        
        await msg.edit_text("✅ ဗီဒီယို Download ဆွဲခြင်း ပြီးဆုံးပါပြီ!\n\nဆက်လက်၍ အသံထုတ်ခြင်း (Whisper) နှင့် မြန်မာလို ဘာသာပြန်ခြင်း (Translation) သို့ ဆက်သွားပါမည်။")
    except Exception as e:
        await msg.edit_text(f"❌ Error ဖြစ်သွားပါသည် bro: {str(e)}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'set_voice':
        await query.edit_message_text(text="🎙️ ကျေးဇူးပြု၍ အသံအမျိုးအစားကို ရွေးချယ်ပါ (ကိုနေတိုး / မိုးသု)")
    elif query.data == 'start_render':
        await query.edit_message_text(text="⚙️ Auto-Generator စတင်နေပါပြီ... ခဏစောင့်ပေးပါ။")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_media))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 Bot အောင်မြင်စွာ စတင်လည်ပတ်နေပြီ (URL Handler ထည့်ပြီး)...")
    app.run_polling()

if __name__ == '__main__':
    main()
