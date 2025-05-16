import subprocess
import os

def compress_video(input_path, output_path, target_size_mb=50):
    """
    Compresses video to be under target_size_mb (in MB) using ffmpeg.
    Tries to estimate bitrate based on video duration.
    """
    # Get video duration in seconds
    try:
        import ffmpeg
        probe = ffmpeg.probe(input_path)
        duration = float(probe['format']['duration'])
    except Exception:
        # fallback: set duration to 60s if can't detect
        duration = 60
    target_total_bitrate = (target_size_mb * 8192) / duration  # kbit/s
    command = [
        'ffmpeg', '-y', '-i', input_path,
        '-b:v', f'{int(target_total_bitrate)}k',
        '-maxrate', f'{int(target_total_bitrate)}k',
        '-bufsize', f'{2*int(target_total_bitrate)}k',
        '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '128k',
        output_path
    ]
    subprocess.run(command, check=True)
    return output_path
