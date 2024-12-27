import threading
from datetime import datetime, timedelta
from pathlib import Path

from logger_utils import append_to_log
from moviepy.video.io.VideoFileClip import VideoFileClip

def format_duration(seconds):
    """Format duration (float/seconds) to a mm:ss string."""
    try:
        return str(timedelta(seconds=round(seconds)))
    except:
        return "00:00"

def calculate_processing_time(start_time, end_time):
    """
    Calculate the difference in seconds between 'start_time' and 'end_time'.
    """
    return (end_time - start_time).total_seconds()

def run_in_thread(target, *args):
    """
    Utility to run a function in a separate daemon thread.
    This keeps the UI responsive.
    """
    threading.Thread(target=target, args=args, daemon=True).start()

def get_video_length(video_path):
    """
    Calculate the length of a video (in seconds) using moviepy.
    Returns None on failure.
    """
    try:
        with VideoFileClip(str(video_path)) as video:
            return round(video.duration, 2)  # Duration in seconds
    except Exception as e:
        append_to_log(f"Error calculating video length: {e}")
        return None