from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from bot.downloader import download_video, DownloadError
import os
import re
import subprocess
from pathlib import Path

DOWNLOAD_DIR = "downloads"

URL_REGEX = re.compile(r"https?://[\w./?=&%-]+", re.IGNORECASE)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to VortexFetchBot!\nJust send me a video link from YouTube, Instagram, TikTok, or other social platforms, and I will fetch the video for you."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *How to use VortexFetchBot:*\n1. Send a video link from any major social network.\n2. Wait a moment while I fetch and send you the video.\n3. Use the audio button to extract audio from videos.\n\n_If you encounter any issues, make sure the link is correct and the video is public._",
        parse_mode="Markdown"
    )

async def extract_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Callback data formatini tekshirish
    if not query.data.startswith("get_audio:"):
        return
    
    unique_id = query.data.split(":")[1]
    await query.message.reply_text("⏳ Audio ajratilmoqda, iltimos kuting...")
    
    try:
        # Video faylini yuklab olish
        video_path = os.path.join(DOWNLOAD_DIR, f"video_{unique_id}.mp4")
        audio_path = os.path.join(DOWNLOAD_DIR, f"audio_{unique_id}.mp3")
        
        # Agar video fayli mavjud bo'lmasa, .part faylini ham tekshiramiz
        if not os.path.exists(video_path):
            part_path = video_path + ".part"
            if os.path.exists(part_path):
                await query.message.reply_text("❗ Video hali to‘liq yuklab olinmagan. Iltimos, biroz kuting va keyinroq urinib ko‘ring.")
                return
            # Vaqtinchalik video faylini yaratish
            original_message = query.message
            if original_message.video:
                video_file = await original_message.video.get_file()
                await video_file.download_to_drive(video_path)
            else:
                await query.message.reply_text("❌ Video topilmadi. Iltimos, qayta urinib ko'ring.")
                return
        
        # FFmpeg orqali videoni audioga aylantirish
        try:
            print(f"[DEBUG] ffmpeg command: ffmpeg -i {video_path} -q:a 0 -map a {audio_path}")
            ffmpeg_result = subprocess.run(
                ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path],
                capture_output=True
            )
            print(f"[DEBUG] ffmpeg returncode: {ffmpeg_result.returncode}")
            if ffmpeg_result.returncode != 0:
                await query.message.reply_text(f"❌ Audio ajratishda xatolik: {ffmpeg_result.stderr.decode()}")
                print(f"[DEBUG] ffmpeg stderr: {ffmpeg_result.stderr.decode()}")
                return
            if not os.path.exists(audio_path):
                await query.message.reply_text("❌ Audio fayli yaratilmagan. Ehtimol, videoda audio trek mavjud emas yoki ffmpeg noto‘g‘ri ishladi.")
                print(f"[DEBUG] Audio fayli mavjud emas: {audio_path}")
                return
            print(f"[DEBUG] Audio fayli yaratildi: {audio_path}")
            # Audio faylini yuborish
            with open(audio_path, "rb") as audio_file:
                await query.message.reply_audio(
                    audio_file,
                    title=f"Audio - {Path(video_path).stem}",
                    caption="🎵 Videoning audio versiyasi"
                )
        except subprocess.CalledProcessError as e:
            await query.message.reply_text(f"❌ Audio ajratishda xatolik: {e.stderr.decode()}")
        except Exception as e:
            await query.message.reply_text(f"❌ Audio ajratishda xatolik: {e}")
    except Exception as e:
        await query.message.reply_text(f"❌ Kutilmagan xatolik: {e}")
    finally:
        # Vaqtinchalik fayllarni tozalash
        for f in [video_path, audio_path]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass

import requests

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    urls = URL_REGEX.findall(text)
    if not urls:
        await update.message.reply_text(
            "❗ No valid video link detected. Please send a correct video URL."
        )
        return
    url = urls[0]
    msg = await update.message.reply_text("⏳ Fayl yuklanmoqda. Iltimos, kuting...")
    try:

        import uuid
        unique_id = str(uuid.uuid4())
        video_path = os.path.join(DOWNLOAD_DIR, f"video_{unique_id}.mp4")
        compressed_path = os.path.join(DOWNLOAD_DIR, f"video_{unique_id}_compressed.mp4")
        try:
            # Video va info ni qaytaradigan yangi funksiya ishlatiladi
            from bot.downloader import download_video_with_info
            video_path, video_info = download_video_with_info(url, DOWNLOAD_DIR)
            file_size = os.path.getsize(video_path)
            max_telegram_size = 2 * 1024 * 1024 * 1024  # 2 GB (Telegram max file size)
            def get_network_name(url):
                if 'instagram.com' in url:
                    return 'Instagram'
                elif 'youtube.com' in url or 'youtu.be' in url:
                    return 'YouTube'
                elif 'tiktok.com' in url:
                    return 'TikTok'
                elif 'facebook.com' in url:
                    return 'Facebook'
                elif 'twitter.com' in url or 'x.com' in url:
                    return 'Twitter'
                elif 'vk.com' in url:
                    return 'VK'
                elif 'reddit.com' in url:
                    return 'Reddit'
                elif 'vimeo.com' in url:
                    return 'Vimeo'
                elif 'dailymotion.com' in url:
                    return 'Dailymotion'
                elif 'likee.video' in url:
                    return 'Likee'
                elif 'pinterest.com' in url:
                    return 'Pinterest'
                else:
                    return 'Video'
            network_name = get_network_name(url)
            # Video sarlavhasi (ijtimoiy tarmoqdagi nomi)
            video_title = video_info.get('title') or os.path.splitext(os.path.basename(video_path))[0]
            caption = f"{network_name}: {video_title}"
            ext = os.path.splitext(video_path)[1].lower()
            image_exts = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
            if file_size <= max_telegram_size:
                with open(video_path, "rb") as file:
                    if ext in image_exts:
                        await update.message.reply_photo(file, caption=caption)
                    else:
                        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                        audio_button = InlineKeyboardMarkup([
                            [InlineKeyboardButton(text="🎵 Audio yuklab olish", callback_data=f"get_audio:{unique_id}")]
                        ])
                        await update.message.reply_video(file, caption=caption, reply_markup=audio_button)
                await msg.delete()
            elif file_size <= 2 * 1024 * 1024 * 1024:  # 2 GB
                with open(video_path, "rb") as file:
                    if ext in image_exts:
                        await update.message.reply_photo(file, caption=caption)
                    else:
                        await update.message.reply_document(file, caption=caption)
                await msg.delete()
            else:
                # Video 2 GB dan katta bo‘lsa, siqiladi
                await msg.edit_text("⚠️ Fayl 2 GB dan katta! Video siqilmoqda, kuting...")
                from bot.video_compress import compress_video
                compress_video(video_path, compressed_path, target_size_mb=2000)  # 2 GB limit uchun
                compressed_size = os.path.getsize(compressed_path)
                if compressed_size > 2 * 1024 * 1024 * 1024:
                    # Fayl hamon katta bo‘lsa, foydalanuvchiga link orqali yuklab olishni taklif qilish
                    await msg.edit_text("❌ Siqilgan video ham 2 GB dan katta. Telegram orqali yuborib bo‘lmaydi. Faylni tashqi hostingga yuklab, link yuborilmoqda...")
                    try:
                        import requests
                        with open(compressed_path, 'rb') as f:
                            resp = requests.put('https://transfer.sh/video.mp4', data=f)
                        if resp.status_code == 200:
                            await msg.edit_text(f"🔗 Faylni bu link orqali yuklab olishingiz mumkin: {resp.text.strip()}")
                        else:
                            await msg.edit_text("❌ Faylni tashqi hostingga yuklab bo‘lmadi. Iltimos, kichikroq video yuboring.")
                    except Exception as e:
                        await msg.edit_text(f"❌ Faylni tashqi hostingga yuklashda xatolik: {e}")
                    return
                await msg.edit_text("⏳ Video siqildi. Endi Telegramga yuklanmoqda...")
                with open(compressed_path, "rb") as file:
                    await update.message.reply_document(file, caption=caption)
                await msg.delete()

        except Exception as e:
            err_msg = str(e)
            if 'There is no video in this post' in err_msg:
                # Instagram rasmli post uchun fallback
                try:
                    import requests
                    from bs4 import BeautifulSoup
                    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    og_image = soup.find('meta', property='og:image')
                    image_url = og_image['content'] if og_image else None
                    if image_url:
                        # Try to get higher resolution by replacing size in URL
                        highres_url = image_url.replace('s150x150', 's1080x1080').replace('p150x150', 'p1080x1080')
                        img_resp = requests.get(highres_url)
                        from io import BytesIO
                        img_bytes = BytesIO(img_resp.content)
                        img_bytes.name = 'instagram.jpg'
                        await update.message.reply_photo(img_bytes, caption="Instagram: Rasmli post")
                        await msg.delete()
                    else:
                        await msg.edit_text("❗ Bu postda video ham, rasm ham topilmadi.")
                except Exception as ex:
                    await msg.edit_text(f"❗ Video va rasm yuklanmadi: {ex}")
            else:
                await msg.edit_text(f"❌ Video jarayonida xatolik: {e}")
        finally:
            # Har doim vaqtinchalik fayllarni tozalash
            for f in [video_path, compressed_path]:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    pass

    except DownloadError as e:
        await msg.edit_text(f"❌ Error while downloading: {e}")
    except Exception as e:
        await msg.edit_text(f"❌ An unexpected error occurred: {e}")
