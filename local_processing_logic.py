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
from video_processor import process_video


def process_local_video(app, progress_label, progress_bar):
    """
    Let user pick a local video file, process it, and save stems.
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
        # Calculate video length
        video_length_seconds = get_video_length(file_path)
        video_length_str = format_duration(video_length_seconds) if video_length_seconds else "Unknown"

        with tempfile.TemporaryDirectory() as temp_dir:
            # Process video to extract vocals and noise
            vocals_path, noise_path, _ = process_video(file_path, Path(temp_dir))

            # Prompt user to save the extracted files
            save_folder = filedialog.askdirectory(title="Choose folder to save extracted files")
            if not save_folder:
                progress_label.set("Save operation canceled by user.")
                append_to_log("Save operation canceled by user.")
                return

            # Save processed files
            vocals_dest = Path(save_folder) / f"clean_{original_stem}.wav"
            noise_dest = Path(save_folder) / f"bg_{original_stem}.wav"

            shutil.move(str(vocals_path), str(vocals_dest))
            append_to_log(f"Vocals file saved as: {vocals_dest}")

            shutil.move(str(noise_path), str(noise_dest))
            append_to_log(f"Background noise file saved as: {noise_dest}")

        end_time = datetime.now()
        file_size = os.path.getsize(file_path)

        # Construct log data
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
            "type": "local",
            "function_type": function_type,
            "status": "success",
        }
        append_to_log(f"Log data prepared: {log_data}")  # Debugging log
        send_log_to_server(log_data)

        # Update UI
        elapsed = log_data['processing_time']
        progress_label.set(f"Video processed successfully in {elapsed:.2f} seconds.")
        append_to_log(f"{function_type}: Successfully processed video.")

    except Exception as e:
        _handle_local_processing_error(app, e, file_path, start_time, progress_label, function_type)

def _handle_local_processing_error(app, error_obj, file_path, start_time, progress_label, function_type):
    """
    Handle errors during local video processing and log details.
    """
    try:
        error_message = f"{function_type}: Unexpected error during video processing: {error_obj}"
        append_to_log(error_message)
        progress_label.set("Processing failed.")

        # Construct error log data
        log_data = {
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
            "type": "local",
            "function_type": function_type,
            "status": "failure",
            "error_logs": str(error_obj),
        }

        # Ensure all required fields are included
        required_keys = [
            "ip", "machine_name", "machine_specs", "start_time", "end_time",
            "file_size", "video_length", "processing_time", "type",
            "function_type", "status", "error_logs",
        ]
        for key in required_keys:
            if key not in log_data or log_data[key] is None:
                raise ValueError(f"Missing required log field: {key}")

        send_log_to_server(log_data)
    except Exception as e:
        append_to_log(f"Failed to handle error properly: {e}")