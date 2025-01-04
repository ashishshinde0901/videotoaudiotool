import os
import subprocess
from pathlib import Path

from logger_utils import append_to_log
from video_processor import get_bundled_path  # Assuming you have this in video_processor

def download_youtube_videos(link, temp_dir):
    """
    Download a YouTube video or playlist into 'temp_dir', along with all available subtitles 
    (including auto-generated). The resulting files will be named via yt-dlp's %(title)s.%(ext)s template.
    
    Return a dictionary of downloaded videos and subtitle files.
    """
    yt_dlp_path = get_bundled_path("yt-dlp.exe")
    if not os.path.exists(yt_dlp_path):
        raise FileNotFoundError(f"yt-dlp executable not found at {yt_dlp_path}")

    # Use --write-auto-subs + --all-subs + --write-subs to ensure we get any available subtitles
    command = [
        yt_dlp_path,
        "-f", "best[ext=mp4]",          # Best quality with .mp4 extension
        "--write-subs",                 # Download normal subtitles if available
        "--write-auto-subs",            # Also download auto-generated subtitles if no "real" subs exist
        "--all-subs",                   # Download all available subtitles
        "--convert-subs", "srt",        # Convert subtitles to SRT format
        "-o", f"{temp_dir}/%(title)s.%(ext)s",  # Output template
        link,
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Gather all downloaded MP4 files
        downloaded_videos = list(Path(temp_dir).glob("*.mp4"))

        # Gather all downloaded subtitle files (now including auto-subs)
        downloaded_subtitles = list(Path(temp_dir).glob("*.srt"))

        if not downloaded_videos:
            raise FileNotFoundError("No MP4 files found after download.")
        
        return {
            "videos": downloaded_videos,
            "subtitles": downloaded_subtitles,
        }

    except subprocess.CalledProcessError as e:
        # If yt-dlp returned a non-zero exit code
        err_msg = e.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"yt-dlp failed: {err_msg}")

    except Exception as e:
        raise RuntimeError(f"Unexpected error during video download: {e}")