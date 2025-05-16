import yt_dlp
import os
import uuid

class DownloadError(Exception):
    pass

def get_format_selection(url: str):
    """URL ga qarab format tanlash"""
    if 'tiktok.com' in url:
        return 'best[vcodec!=none][ext=mp4]'
    return 'best'

def download_video(url: str, download_dir: str, progress_callback=None) -> str:
    """
    Downloads video from the given URL using yt-dlp.
    Supports restricted videos by using cookies.json if present.
    Returns the path to the downloaded file.
    Raises DownloadError on failure.
    """
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    filename = f"video_{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(download_dir, filename)
    
    # Check for cookies.txt in the same directory as this file
    cookies_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    
    ydl_opts = {
        'outtmpl': output_path,
        'format': get_format_selection(url),
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'progress_hooks': [progress_callback] if progress_callback else [],
        # TikTok uchun qo'shimcha sozlamalar
        'extractor_args': {
            'tiktok': {
                'embed_thumbnail': False,
                'embed_metadata': False,
                'force_generic_extractor': False
            }
        }
    }
    
    if os.path.exists(cookies_path):
        ydl_opts['cookiefile'] = cookies_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        # Sometimes yt-dlp changes the filename
        if 'requested_downloads' in info and info['requested_downloads']:
            output_path = info['requested_downloads'][0]['filepath']
        elif 'filepath' in info:
            output_path = info['filepath']
        return output_path
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if 'cookies' in error_msg.lower() or 'sign in' in error_msg.lower():
            if not os.path.exists(cookies_path):
                raise DownloadError("This video requires authentication. Please provide a valid cookies.json file in the bot directory. See README for details.")
        raise DownloadError(error_msg)
    except Exception as e:
        raise DownloadError(str(e))

def download_video_with_info(url: str, download_dir: str):
    """
    Yuklab olingan video path va info dict (yt-dlp metadata) ni qaytaradi.
    """
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    filename = f"video_{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(download_dir, filename)
    cookies_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    
    ydl_opts = {
        'outtmpl': output_path,
        'format': get_format_selection(url),
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        # TikTok uchun qo'shimcha sozlamalar
        'extractor_args': {
            'tiktok': {
                'embed_thumbnail': False,
                'embed_metadata': False,
                'force_generic_extractor': False
            }
        }
    }
    
    if os.path.exists(cookies_path):
        ydl_opts['cookiefile'] = cookies_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        if 'requested_downloads' in info and info['requested_downloads']:
            output_path = info['requested_downloads'][0]['filepath']
        elif 'filepath' in info:
            output_path = info['filepath']
        return output_path, info
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if 'cookies' in error_msg.lower() or 'sign in' in error_msg.lower():
            if not os.path.exists(cookies_path):
                raise DownloadError("This video requires authentication. Please provide a valid cookies.json file in the bot directory. See README for details.")
        raise DownloadError(error_msg)
    except Exception as e:
        raise DownloadError(str(e))
