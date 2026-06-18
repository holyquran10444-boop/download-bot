import logging
import os
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "8813806903:AAFz1aF0sCnSlhExrNxoSLrtA7Ze2RwbHO8"
ADMIN_ID = 605635405

all_users  = set()
user_stats = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ─── مساعدات ──────────────────────────────────────────────────────────────────

def get_stats(user_id: int) -> dict:
    if user_id not in user_stats:
        user_stats[user_id] = {
            "downloads": 0,
            "joined": datetime.now().strftime("%Y-%m-%d")
        }
    return user_stats[user_id]

def users_today() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    return sum(1 for s in user_stats.values() if s.get("joined") == today)

def total_downloads() -> int:
    return sum(s["downloads"] for s in user_stats.values())

def detect_platform(url: str) -> str:
    if "tiktok.com" in url:
        return "tiktok"
    elif "snapchat.com" in url or "snap.com" in url:
        return "snapchat"
    elif "instagram.com" in url:
        return "instagram"
    elif "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return "other"

def platform_emoji(platform: str) -> str:
    return {
        "tiktok":    "🎵 TikTok",
        "snapchat":  "👻 Snapchat",
        "instagram": "📸 Instagram",
        "youtube":   "▶️ YouTube",
        "other":     "🌐 موقع آخر"
    }.get(platform, "🌐")

def clean_tmp():
    for f in os.listdir("/tmp"):
        if f.endswith((".mp4", ".mp3", ".webm", ".m4a", ".mov")):
            try:
                os.remove(f"/tmp/{f}")
            except Exception:
                pass

# ─── لوحات المفاتيح ───────────────────────────────────────────────────────────

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 تحميل فيديو",    callback_data="mode_video")],
        [InlineKeyboardButton("🎵 تحميل صوت MP3",  callback_data="mode_audio")],
        [InlineKeyboardButton("📊 إحصائياتي",       callback_data="my_stats")],
        [InlineKeyboardButton("ℹ️ المواقع المدعومة", callback_data="supported")],
        [InlineKeyboardButton("📢 شارك البوت",
            url="https://t.me/share/url?url=https://t.me/YourBot&text=بوت تحميل الفيديو 🎬")],
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 الرئيسية", callback_data="home")],
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء", callback_data="home")],
    ])

def quality_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 عالية  — 1080p", callback_data="quality_1080")],
        [InlineKeyboardButton("✅ متوسطة — 720p",  callback_data="quality_720")],
        [InlineKeyboardButton("📱 منخفضة — 480p",  callback_data="quality_480")],
        [InlineKeyboardButton("❌ إلغاء",           callback_data="home")],
    ])

# ─── المعالجات ────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    all_users.add(user.id)
    get_stats(user.id)
    await update.message.reply_text(
        "👋 أهلاً بك في بوت التحميل!\n\n"
        "📥 يمكنك التحميل من:\n\n"
        "🎵 TikTok\n"
        "👻 Snapchat\n"
        "📸 Instagram\n"
        "▶️ YouTube\n\n"
        "فيديو أو صوت MP3 — اختر من القائمة:",
        reply_markup=main_keyboard()
    )

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        f"📊 إحصائيات البوت:\n\n"
        f"👥 إجمالي المستخدمين : {len(all_users)}\n"
        f"📅 انضموا اليوم      : {users_today()}\n"
        f"📥 تحميلات كلية      : {total_downloads()}"
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    all_users.add(user_id)
    get_stats(user_id)

    if query.data == "home":
        context.user_data.clear()
        await query.edit_message_text(
            "🏠 القائمة الرئيسية:",
            reply_markup=main_keyboard()
        )

    elif query.data == "supported":
        await query.edit_message_text(
            "📋 المواقع المدعومة:\n\n"
            "🎵 TikTok — tiktok.com\n"
            "👻 Snapchat — snapchat.com\n"
            "📸 Instagram — instagram.com\n"
            "▶️ YouTube — youtube.com / youtu.be\n\n"
            "📌 فقط أرسل الرابط وسأتولى الباقي!",
            reply_markup=back_keyboard()
        )

    elif query.data == "my_stats":
        s = get_stats(user_id)
        await query.edit_message_text(
            f"📊 إحصائياتك:\n\n"
            f"📥 تحميلاتك : {s['downloads']}\n"
            f"📅 انضممت   : {s['joined']}",
            reply_markup=back_keyboard()
        )

    elif query.data == "mode_video":
        context.user_data["mode"] = "video"
        await query.edit_message_text(
            "🎬 تحميل فيديو\n\n"
            "📎 أرسل الرابط الآن:\n\n"
            "مثال:\n"
            "🎵 https://tiktok.com/...\n"
            "👻 https://snapchat.com/...\n"
            "📸 https://instagram.com/p/...\n"
            "▶️ https://youtube.com/watch?v=...",
            reply_markup=cancel_keyboard()
        )

    elif query.data == "mode_audio":
        context.user_data["mode"] = "audio"
        await query.edit_message_text(
            "🎵 تحميل صوت MP3\n\n"
            "📎 أرسل الرابط الآن وسأستخرج الصوت فقط:",
            reply_markup=cancel_keyboard()
        )

    elif query.data.startswith("quality_"):
        quality = query.data.split("_")[1]
        url     = context.user_data.get("url", "")

        if not url:
            await query.edit_message_text(
                "❌ انتهت الجلسة، أرسل الرابط مجدداً.",
                reply_markup=back_keyboard()
            )
            return

        platform = detect_platform(url)
        quality_label = {"1080": "1080p", "720": "720p", "480": "480p"}.get(quality, "720p")

        await query.edit_message_text(
            f"⏳ جاري تحميل {platform_emoji(platform)}\n"
            f"🎬 الجودة: {quality_label}\n\n"
            "يرجى الانتظار... 🙏"
        )

        await do_download(query, context, url, "video", quality, user_id)

# ─── التحميل ──────────────────────────────────────────────────────────────────

async def do_download(query_or_msg, context, url: str, mode: str, quality: str, user_id: int):
    try:
        clean_tmp()
        platform = detect_platform(url)

        if mode == "audio":
            cmd = [
                "yt-dlp",
                "-x", "--audio-format", "mp3",
                "--audio-quality", "0",
                "-o", "/tmp/%(title).50s.%(ext)s",
                url
            ]
        else:
            cmd = [
                "yt-dlp",
                "-f", f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best[height<={quality}]",
                "--merge-output-format", "mp4",
                "-o", "/tmp/%(title).50s.%(ext)s",
                url
            ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

        if proc.returncode != 0:
            raise Exception(stderr.decode()[-500:])

        ext   = "mp3" if mode == "audio" else "mp4"
        files = [f for f in os.listdir("/tmp") if f.endswith(f".{ext}")]

        if not files:
            raise Exception("لم يُعثر على الملف")

        filepath = f"/tmp/{files[0]}"
        filesize = os.path.getsize(filepath) / (1024 * 1024)

        if filesize > 50:
            await query_or_msg.edit_text(
                f"❌ حجم الملف كبير جداً ({filesize:.1f} MB)\n"
                "تيليجرام يسمح بحد أقصى 50MB\n\n"
                "💡 جرب جودة أقل!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 اختر جودة أقل", callback_data="mode_video")],
                    [InlineKeyboardButton("🏠 الرئيسية",       callback_data="home")],
                ])
            )
            os.remove(filepath)
            return

        await query_or_msg.edit_text("📤 جاري الرفع إلى تيليجرام...")

        quality_label = {"1080": "1080p", "720": "720p", "480": "480p"}.get(quality, "")
        caption = (
            f"✅ تم التحميل!\n"
            f"{platform_emoji(platform)}\n\n"
            "شارك البوت مع أصدقائك 🤝"
        )

        if mode == "audio":
            with open(filepath, "rb") as f:
                await context.bot.send_audio(
                    chat_id=user_id,
                    audio=f,
                    caption=caption
                )
        else:
            with open(filepath, "rb") as f:
                await context.bot.send_video(
                    chat_id=user_id,
                    video=f,
                    caption=caption
                )

        os.remove(filepath)
        get_stats(user_id)["downloads"] += 1

        await query_or_msg.edit_text(
            "✅ تم الإرسال! تحقق من رسائلك أعلاه 👆",
            reply_markup=main_keyboard()
        )

    except asyncio.TimeoutError:
        await query_or_msg.edit_text(
            "❌ انتهت المهلة!\nالفيديو طويل جداً أو الاتصال بطيء.",
            reply_markup=back_keyboard()
        )
    except Exception as e:
        logging.error(f"Download error: {e}")
        await query_or_msg.edit_text(
            "❌ فشل التحميل!\n\n"
            "الأسباب المحتملة:\n"
            "• الحساب خاص\n"
            "• الرابط غير صحيح\n"
            "• الفيديو محذوف\n\n"
            "جرب رابطاً آخر 🔄",
            reply_markup=back_keyboard()
        )

# ─── الرسائل ──────────────────────────────────────────────────────────────────

async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    user_id = user.id
    text    = update.message.text
    all_users.add(user_id)
    get_stats(user_id)

    mode = context.user_data.get("mode")

    if not mode:
        await update.message.reply_text(
            "اختر نوع التحميل أولاً:",
            reply_markup=main_keyboard()
        )
        return

    if not text.startswith("http"):
        await update.message.reply_text(
            "❌ أرسل رابطاً صحيحاً يبدأ بـ http",
            reply_markup=cancel_keyboard()
        )
        return

    context.user_data["url"] = text
    platform = detect_platform(text)

    if mode == "audio":
        msg_obj = await update.message.reply_text(
            f"⏳ جاري تحميل صوت {platform_emoji(platform)}...\n"
            "يرجى الانتظار 🙏"
        )
        await do_download(msg_obj, context, text, "audio", "0", user_id)

    else:
        await update.message.reply_text(
            f"✅ تم استلام رابط {platform_emoji(platform)}\n\n"
            "🎬 اختر جودة الفيديو:\n\n"
            "🔥 عالية  = أوضح صورة، حجم أكبر\n"
            "✅ متوسطة = توازن مثالي (موصى بها)\n"
            "📱 منخفضة = حجم صغير، سريعة",
            reply_markup=quality_keyboard()
        )

# ─── التشغيل ──────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
