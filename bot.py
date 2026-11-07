async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    msg = await update.message.reply_text("📥 ဗီဒီယိုလင့်ခ์ကို လက်ခံရရှိပါပြီ။ `yt-dlp` ဖြင့် Download ဆွဲနေပါသည်...")
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'downloaded_video.mp4',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        await msg.edit_text("✅ ဗီဒီယို Download ဆွဲခြင်း ပြီးဆုံးပါပြီ!")
    except Exception as e:
        await msg.edit_text(f"❌ Error ဖြစ်သွားပါသည် bro: {str(e)}")
