import os
import shutil
import tempfile
import socket
import platform
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

from logger_utils import append_to_log, send_log_to_server
from utils import (
    format_duration,
    calculate_processing_time,
    get_video_length,
)
from youtube_downloader import download_youtube_videos


def process_youtube_video(app, youtube_link_var, progress_label, progress_bar):
    """
    Download YouTube video(s) and subtitles in all available languages in a background thread.
    Then prompt the user to select a folder to save them.
    """
    link = youtube_link_var.get().strip()
    if not link:
        progress_label.set("YouTube link is empty.")
        append_to_log("YouTube link is empty.")
        return

    progress_label.set("Downloading video and subtitles... Please wait.")
    start_time = datetime.utcnow()  # Use UTC time

    file_size = None
    video_length_str = None

    try:
        # 1. Create a temporary directory for the download operation
        with tempfile.TemporaryDirectory() as temp_dir:
            # 2. Download videos + subtitles into temp_dir using youtube_downloader
            download_results = download_youtube_videos(link, temp_dir)

            video_paths = download_results.get("videos", [])
            subtitle_paths = download_results.get("subtitles", [])

            if not video_paths:
                raise FileNotFoundError("No videos downloaded.")
            if not subtitle_paths:
                append_to_log("No subtitles were found or available for download.")

            # 3. Prompt the user to select the final folder where files will be moved
            save_folder = filedialog.askdirectory(title="Choose folder to save the downloaded files")
            if not save_folder:
                progress_label.set("Save operation canceled by user.")
                append_to_log("Save operation canceled by user.")
                return

            # 4. Move .mp4 files and .srt subtitle files from temp_dir to the chosen folder
            total_size = 0
            max_duration = 0

            # Process videos
            for vp in video_paths:
                size = os.path.getsize(vp)
                total_size += size

                # Attempt to get video duration for logging
                length_seconds = get_video_length(vp)
                if length_seconds and length_seconds > max_duration:
                    max_duration = length_seconds

                # Move the video from temp_dir to the final destination
                dest_path = Path(save_folder) / vp.name
                shutil.move(str(vp), str(dest_path))
                append_to_log(f"Video saved: {dest_path}")

            # Process subtitles
            for sp in subtitle_paths:
                # Move each .srt file from temp_dir to the final destination
                dest_path = Path(save_folder) / sp.name
                shutil.move(str(sp), str(dest_path))
                append_to_log(f"Subtitle saved: {dest_path}")

            # 5. Prepare logging info
            file_size = total_size
            if max_duration > 0:
                video_length_str = format_duration(max_duration)

        # 6. After the with-block, temp_dir is automatically cleaned up
        end_time = datetime.utcnow()

        # 7. Create JSON log data
        log_data = {
            "ip": socket.gethostbyname(socket.gethostname()),
            "machine_name": platform.node(),
            "machine_specs": {
                "os": platform.system(),
                "os_version": platform.version(),
                "machine": platform.machine(),
            },
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "file_size": file_size,
            "video_length": video_length_str,
            "processing_time": calculate_processing_time(start_time, end_time),
            "type": "youtube",
            "function_type": "YouTube Download",
            "status": "success",
        }
        send_log_to_server(log_data)

        # 8. Update UI status
        progress_label.set(
            f"Video(s) and subtitles downloaded successfully in {log_data['processing_time']:.2f} seconds."
        )

    # --- Exception Handling ---
    except FileNotFoundError as fnf_err:
        _handle_download_error(app, progress_label, start_time, "file not found", fnf_err, "YouTube Download")
    except RuntimeError as rt_err:
        _handle_download_error(app, progress_label, start_time, "runtime", rt_err, "YouTube Download")
    except Exception as e:
        _handle_download_error(app, progress_label, start_time, "unexpected", e, "YouTube Download")


def _handle_download_error(app, progress_label, start_time, error_type, error_obj, function_type):
    """Common handler for download exceptions."""
    error_message = f"{error_type.capitalize()} error during download: {error_obj}"
    append_to_log(error_message)
    progress_label.set("Download failed.")

    end_time = datetime.utcnow()

    send_log_to_server({
        "ip": socket.gethostbyname(socket.gethostname()),
        "machine_name": platform.node(),
        "machine_specs": {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
        },
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "file_size": None,
        "video_length": None,
        "processing_time": calculate_processing_time(start_time, end_time),
        "type": "youtube",
        "function_type": function_type,
        "status": "failure",
        "error_logs": str(error_obj),
    })