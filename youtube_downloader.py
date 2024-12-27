import os
import subprocess
from pathlib import Path

from logger_utils import append_to_log
from video_processor import get_bundled_path  # Assuming you have this in video_processor
# OR place 'get_bundled_path' in another file if you prefer

def download_youtube_videos(link, temp_dir):
    """
    Download a YouTube video or playlist into 'temp_dir'.
    The resulting files will be named via yt-dlp's %(title)s.%(ext)s template.
    Return a list of all downloaded .mp4 paths.
    """
    yt_dlp_path = get_bundled_path("yt-dlp.exe")
    if not os.path.exists(yt_dlp_path):
        raise FileNotFoundError(f"yt-dlp executable not found at {yt_dlp_path}")

    # If you want to guarantee MP4, even if the best is not an MP4, consider:
    # command = [
    #     yt_dlp_path,
    #     "-f", "bestvideo+bestaudio/best",
    #     "--merge-output-format", "mp4",
    #     "-o", f"{temp_dir}/%(title)s.%(ext)s",
    #     link,
    # ]
    
    command = [
        yt_dlp_path,
        "-f", "best[ext=mp4]",
        "-o", f"{temp_dir}/%(title)s.%(ext)s",
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
        downloaded_files = list(Path(temp_dir).glob("*.mp4"))
        if not downloaded_files:
            raise FileNotFoundError("No MP4 files found after download.")
        return downloaded_files

    except subprocess.CalledProcessError as e:
        # If yt-dlp returned a non-zero exit code
        err_msg = e.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"yt-dlp failed: {err_msg}")

    except Exception as e:
        raise RuntimeError(f"Unexpected error during video download: {e}")