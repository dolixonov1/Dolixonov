from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from bot.downloader import download_video, DownloadError, get_video_formats
import os
import re
import subprocess
from pathlib import Path
import uuid

DOWNLOAD_DIR = "downloads"

URL_REGEX = re.compile(r"https?://[\w./?=&%-]+", re.IGNORECASE)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 DolixonovBot'ga xush kelibsiz!\nYouTube, Instagram, TikTok yoki boshqa ijtimoiy tarmoqlardan video havolasini yuboring, men sizga videoni yuklab beraman."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Qanday foydalanish mumkin:*\n1. Istalgan ijtimoiy tarmoqdan video havolasini yuboring.\n2. Biroz kutib turing, men videoni yuklab beraman.\n3. Audio tugmasini bosib, videoning audio versiyasini ham olishingiz mumkin.\n\n_Agar muammo bo'lsa, havola to'g'riligini va video ochiq ekanligini tekshiring._",
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
                await query.message.reply_text("❗ Video hali to'liq yuklab olinmagan. Iltimos, biroz kuting va keyinroq urinib ko'ring.")
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
                await query.message.reply_text("❌ Audio fayli yaratilmagan. Ehtimol, videoda audio trek mavjud emas yoki ffmpeg noto'g'ri ishladi.")
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

async def handle_quality_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("quality:"):
        return
        
    format_id = query.data.split(":")[1]
    url = context.user_data.get('last_url')
    if not url:
        await query.message.edit_text("❌ URL topilmadi. Iltimos, qaytadan urinib ko'ring.")
        return
        
    msg = await query.message.edit_text("⏳ Video yuklanmoqda. Iltimos, kuting...")
    try:
        unique_id = str(uuid.uuid4())
        video_path = os.path.join(DOWNLOAD_DIR, f"video_{unique_id}.mp4")
        compressed_path = os.path.join(DOWNLOAD_DIR, f"video_{unique_id}_compressed.mp4")
        
        try:
            video_path = download_video(url, DOWNLOAD_DIR, format_id=format_id)
            file_size = os.path.getsize(video_path)
            max_telegram_size = 2 * 1024 * 1024 * 1024
            
            network_name = get_network_name(url)
            caption = f"{network_name} video"
            
            if file_size <= max_telegram_size:
                with open(video_path, "rb") as file:
                    audio_button = InlineKeyboardMarkup([
                        [InlineKeyboardButton(text="🎵 Audio yuklab olish", callback_data=f"get_audio:{unique_id}")]
                    ])
                    await query.message.reply_video(file, caption=caption, reply_markup=audio_button)
                await msg.delete()
            else:
                await msg.edit_text("⚠️ Fayl 2 GB dan katta! Video siqilmoqda, kuting...")
                compress_video(video_path, compressed_path, target_size_mb=2000)
                with open(compressed_path, "rb") as file:
                    await query.message.reply_document(file, caption=caption)
                await msg.delete()
                
        except Exception as e:
            await msg.edit_text(f"❌ Video yuklab olishda xatolik: {e}")
            
        finally:
            for f in [video_path, compressed_path]:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    pass
                    
    except Exception as e:
        await msg.edit_text(f"❌ Kutilmagan xatolik: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    urls = URL_REGEX.findall(text)
    if not urls:
        await update.message.reply_text(
            "❗ Video havolasi topilmadi. Iltimos, to'g'ri havola yuboring."
        )
        return
        
    url = urls[0]
    msg = await update.message.reply_text("⏳ Video formatlari tekshirilmoqda...")
    
    try:
        # Save URL for quality selection callback
        context.user_data['last_url'] = url
        
        # Get available formats
        formats = get_video_formats(url)
        if not formats:
            # If no formats available, download with default quality
            await msg.edit_text("⏳ Video yuklanmoqda...")
            return await download_and_send_video(update, context, url, msg)
            
        # Create quality selection buttons
        buttons = []
        for fmt in formats:
            if fmt['resolution'] != 'unknown':
                btn_text = f"{fmt['resolution']} ({fmt['filesize']})"
                buttons.append([InlineKeyboardButton(
                    text=btn_text,
                    callback_data=f"quality:{fmt['format_id']}"
                )])
                
        # Add "Best Quality" button
        buttons.append([InlineKeyboardButton(
            text="🎯 Eng yuqori sifat",
            callback_data="quality:best"
        )])
        
        markup = InlineKeyboardMarkup(buttons)
        await msg.edit_text(
            "🎥 Video sifatini tanlang:",
            reply_markup=markup
        )
        
    except Exception as e:
        await msg.edit_text(f"❌ Xatolik yuz berdi: {e}")

async def download_and_send_video(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, msg):
    try:
        unique_id = str(uuid.uuid4())
        video_path = os.path.join(DOWNLOAD_DIR, f"video_{unique_id}.mp4")
        compressed_path = os.path.join(DOWNLOAD_DIR, f"video_{unique_id}_compressed.mp4")
        
        try:
            video_path = download_video(url, DOWNLOAD_DIR)
            file_size = os.path.getsize(video_path)
            max_telegram_size = 2 * 1024 * 1024 * 1024
            
            network_name = get_network_name(url)
            caption = f"{network_name} video"
            
            if file_size <= max_telegram_size:
                with open(video_path, "rb") as file:
                    audio_button = InlineKeyboardMarkup([
                        [InlineKeyboardButton(text="🎵 Audio yuklab olish", callback_data=f"get_audio:{unique_id}")]
                    ])
                    await update.message.reply_video(file, caption=caption, reply_markup=audio_button)
                await msg.delete()
            else:
                await msg.edit_text("⚠️ Fayl 2 GB dan katta! Video siqilmoqda, kuting...")
                compress_video(video_path, compressed_path, target_size_mb=2000)
                with open(compressed_path, "rb") as file:
                    await update.message.reply_document(file, caption=caption)
                await msg.delete()
                
        except Exception as e:
            await msg.edit_text(f"❌ Video yuklab olishda xatolik: {e}")
            
        finally:
            for f in [video_path, compressed_path]:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    pass
                    
    except Exception as e:
        await msg.edit_text(f"❌ Kutilmagan xatolik: {e}")

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
