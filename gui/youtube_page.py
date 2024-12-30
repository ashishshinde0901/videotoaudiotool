import os
import shutil
import tempfile
import socket
import platform
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, ttk

import customtkinter as ctk

from logger_utils import append_to_log, send_log_to_server
from utils import (
    format_duration,
    calculate_processing_time,
    run_in_thread,
    get_video_length,
)
from youtube_downloader import download_youtube_videos


def init_youtube_download(app):
    """
    UI for downloading from YouTube (video or playlist).
    """
    app.clear_content_frame()
    progress_label = ctk.StringVar(value="Status: Ready")
    progress_bar = ttk.Progressbar(app.content_frame, orient="horizontal", mode="determinate", length=600)
    youtube_link_var = ctk.StringVar()

    # Page Title
    ctk.CTkLabel(
        app.content_frame,
        text="Download YouTube Video or Playlist",
        font=("Helvetica", 18)
    ).pack(pady=20)

    # Wider Entry for YouTube link
    ctk.CTkEntry(
        app.content_frame,
        textvariable=youtube_link_var,
        placeholder_text="Enter your YouTube link here",
        width=600,  # Set width for the entry box
    ).pack(pady=20)

    # Download Button
    ctk.CTkButton(
        app.content_frame,
        text="Download",
        command=lambda: run_in_thread(
            process_youtube_video,
            app,
            youtube_link_var,
            progress_label,
            progress_bar
        )
    ).pack(pady=20)

    # Progress Bar and Label
    progress_bar.pack(pady=10)
    ctk.CTkLabel(
        app.content_frame,
        textvariable=progress_label,
        font=("Helvetica", 14)
    ).pack(pady=10)


def process_youtube_video(app, youtube_link_var, progress_label, progress_bar):
    """
    Download YouTube video(s) in a background thread.
    Then prompt the user to select a folder to save them.
    """
    link = youtube_link_var.get().strip()
    if not link:
        progress_label.set("YouTube link is empty.")
        append_to_log("YouTube link is empty.")
        return

    progress_label.set("Downloading video... Please wait.")
    start_time = datetime.now()

    file_size = None
    video_length_str = None

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download to temp_dir
            video_paths = download_youtube_videos(link, temp_dir)

            # Ask user for folder
            save_folder = filedialog.askdirectory(title="Choose folder to save the downloaded video(s)")
            if not save_folder:
                progress_label.set("Save operation canceled by user.")
                append_to_log("Save operation canceled by user.")
                return

            # Move .mp4 files to chosen folder
            total_size = 0
            max_duration = 0
            for vp in video_paths:
                size = os.path.getsize(vp)
                total_size += size
                length_seconds = get_video_length(vp)
                if length_seconds and length_seconds > max_duration:
                    max_duration = length_seconds

                dest_path = Path(save_folder) / vp.name
                shutil.move(str(vp), str(dest_path))

            file_size = total_size
            if max_duration > 0:
                video_length_str = format_duration(max_duration)

        end_time = datetime.now()

        # Log data with function type
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
            "function_type": "YouTube Download",  # Add function type here
            "status": "success",
        }
        send_log_to_server(log_data)

        # Update UI
        progress_label.set(f"Video(s) downloaded successfully in {log_data['processing_time']:.2f} seconds.")

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

    from datetime import datetime  # re-imported locally to keep the structure
    send_log_to_server({
        "ip": socket.gethostbyname(socket.gethostname()),
        "machine_name": platform.node(),
        "machine_specs": {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
        },
        "start_time": start_time.isoformat(),
        "end_time": datetime.now().isoformat(),
        "file_size": None,
        "video_length": None,
        "processing_time": calculate_processing_time(start_time, datetime.now()),
        "type": "youtube",
        "function_type": function_type,  # Include function type here
        "status": "failure",
        "error_logs": str(error_obj),
    })