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
from video_processor import process_video

def init_local_processing(app):
    """
    UI for local video processing.
    """
    app.clear_content_frame()
    progress_label = ctk.StringVar(value="Status: Ready")
    progress_bar = ttk.Progressbar(app.content_frame, orient="horizontal", mode="determinate", length=600)

    ctk.CTkLabel(app.content_frame, text="Process Local Video File", font=("Helvetica", 18)).pack(pady=20)

    ctk.CTkButton(
        app.content_frame,
        text="Upload File",
        command=lambda: run_in_thread(process_local_video, app, progress_label, progress_bar),
    ).pack(pady=20)

    progress_bar.pack(pady=10)
    ctk.CTkLabel(app.content_frame, textvariable=progress_label, font=("Helvetica", 14)).pack(pady=10)


def process_local_video(app, progress_label, progress_bar):
    """
    Let user pick a local video file, process it, then prompt for saving stems.
    """
    file_path = filedialog.askopenfilename(
        title="Select a Video File",
        filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")],
    )
    if not file_path:
        progress_label.set("No file selected.")
        append_to_log("No file selected for Local Video Upload.")
        return

    progress_label.set("Processing video... Please wait.")
    start_time = datetime.now()
    original_stem = Path(file_path).stem
    function_type = "Local Video Upload"  # Define function type

    try:
        video_length_seconds = get_video_length(file_path)
        video_length_str = format_duration(video_length_seconds) if video_length_seconds else "Unknown"

        with tempfile.TemporaryDirectory() as temp_dir:
            # Separate audio (vocals/noise)
            vocals_path, noise_path, _ = process_video(file_path, Path(temp_dir))

            # Choose folder to save the .wav files
            save_folder = filedialog.askdirectory(title="Choose folder to save extracted files")
            if not save_folder:
                progress_label.set("Save operation canceled by user.")
                append_to_log("Save operation canceled by user.")
                return

            # Move/rename
            vocals_dest = Path(save_folder) / f"clean_{original_stem}.wav"
            noise_dest = Path(save_folder) / f"bg_{original_stem}.wav"

            shutil.move(str(vocals_path), str(vocals_dest))
            append_to_log(f"Vocals file saved as: {vocals_dest}")

            shutil.move(str(noise_path), str(noise_dest))
            append_to_log(f"Background noise file saved as: {noise_dest}")

        end_time = datetime.now()
        file_size = os.path.getsize(file_path)

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
            "type": "local",  # Correct type field
            "function_type": function_type,  # Ensure function type is included
            "status": "success",
        }
        append_to_log(f"Sending log: {log_data}")  # Debugging log
        send_log_to_server(log_data)

        # Update UI
        elapsed = log_data['processing_time']
        progress_label.set(f"Video processed successfully in {elapsed:.2f} seconds.")
        append_to_log(f"{function_type}: Successfully processed video.")

    except Exception as e:
        _handle_local_processing_error(app, e, file_path, start_time, progress_label, function_type)


def _handle_local_processing_error(app, error_obj, file_path, start_time, progress_label, function_type):
    """Handle errors for local video processing."""
    error_message = f"{function_type}: Unexpected error during video processing: {error_obj}"
    append_to_log(error_message)
    progress_label.set("Processing failed.")

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
        "file_size": os.path.getsize(file_path) if file_path else None,
        "video_length": "Unknown",
        "processing_time": calculate_processing_time(start_time, datetime.now()),
        "type": "local",  # Correct type field
        "function_type": function_type,  # Include function type
        "status": "failure",
        "error_logs": str(error_obj),
    })