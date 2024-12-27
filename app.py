import os
import shutil
import tempfile
import socket
import platform
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, ttk

import customtkinter as ctk
from logger_utils import (
    initialize_log_file,
    append_to_log,
    send_log_to_server,
)
from utils import (
    format_duration,
    calculate_processing_time,
    run_in_thread,
    get_video_length,
)
from youtube_downloader import download_youtube_videos
from video_processor import process_video  # existing module with your logic

###############################################################################
#                      MAIN GUI APPLICATION CLASS
###############################################################################

class RianVideoProcessingTool(ctk.CTk):
    """
    Main application class for the Rian Video Processing Tool.
    """
    def __init__(self):
        super().__init__()
        self.title("Rian Video Processing Tool")
        self.geometry("1000x750")
        self.resizable(False, False)

        # CustomTkInter appearance settings
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")

        # Initialize local log file
        initialize_log_file()

        # Layout: Left nav + main content
        self.nav_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#1e3c72")
        self.nav_frame.pack(side="left", fill="y")

        self.content_frame = ctk.CTkFrame(self, corner_radius=10)
        self.content_frame.pack(side="right", expand=True, fill="both", padx=20, pady=20)

        self.init_navbar()
        self.init_homepage()

    ############################################################################
    #                          NAVIGATION / LAYOUT
    ############################################################################

    def init_navbar(self):
        """Create buttons and labels for the navigation menu."""
        ctk.CTkLabel(
            self.nav_frame,
            text="Rian Video Processing Tool",
            font=("Helvetica", 20, "bold"),
            fg_color="#142850",
            text_color="white",
            corner_radius=8,
        ).pack(pady=20)

        ctk.CTkButton(self.nav_frame, text="Home", command=self.init_homepage).pack(pady=10)
        ctk.CTkButton(self.nav_frame, text="Video To Clean Audio", command=self.init_local_processing).pack(pady=10)
        ctk.CTkButton(self.nav_frame, text="YouTube Download", command=self.init_youtube_download).pack(pady=10)

    def clear_content_frame(self):
        """Clear any widgets from the content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    ############################################################################
    #                                HOME PAGE
    ############################################################################

    def init_homepage(self):
        """Load the home/welcome page."""
        self.clear_content_frame()

        # Adjust text layout to ensure proper wrapping
        ctk.CTkLabel(
            self.content_frame,
            text="Welcome to Rian Video Processing Tool",
            font=("Helvetica", 24, "bold"),
            wraplength=800,  # Add wrap length
            justify="center",  # Center-align the text
        ).pack(pady=40)

        ctk.CTkLabel(
            self.content_frame,
            text=(
                "This tool allows you to process videos locally or "
                "download YouTube videos (including playlists) with ease."
            ),
            font=("Helvetica", 16),
            wraplength=800,  # Add wrap length
            justify="center",  # Center-align the text
        ).pack(pady=10)

    ############################################################################
    #                       YOUTUBE DOWNLOAD PAGE
    ############################################################################

    def init_youtube_download(self):
        """UI for downloading from YouTube (video or playlist)."""
        self.clear_content_frame()
        progress_label = ctk.StringVar(value="Status: Ready")
        progress_bar = ttk.Progressbar(self.content_frame, orient="horizontal", mode="determinate", length=600)
        youtube_link_var = ctk.StringVar()

        # Page Title
        ctk.CTkLabel(
            self.content_frame,
            text="Download YouTube Video or Playlist",
            font=("Helvetica", 18)
        ).pack(pady=20)

        # Wider Entry for YouTube link
        ctk.CTkEntry(
            self.content_frame,
            textvariable=youtube_link_var,
            placeholder_text="Enter your YouTube link here",
            width=600,  # Set width for the entry box
        ).pack(pady=20)

        # Download Button
        ctk.CTkButton(
            self.content_frame,
            text="Download",
            command=lambda: run_in_thread(
                self.process_youtube_video,
                youtube_link_var,
                progress_label,
                progress_bar
            )
        ).pack(pady=20)

        # Progress Bar and Label
        progress_bar.pack(pady=10)
        ctk.CTkLabel(
            self.content_frame,
            textvariable=progress_label,
            font=("Helvetica", 14)
        ).pack(pady=10)

    def process_youtube_video(self, youtube_link_var, progress_label, progress_bar):
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
            self._handle_download_error(progress_label, start_time, "file not found", fnf_err, "YouTube Download")
        except RuntimeError as rt_err:
            self._handle_download_error(progress_label, start_time, "runtime", rt_err, "YouTube Download")
        except Exception as e:
            self._handle_download_error(progress_label, start_time, "unexpected", e, "YouTube Download")

    def _handle_download_error(self, progress_label, start_time, error_type, error_obj):
        """Common handler for download exceptions."""
        error_message = f"{error_type.capitalize()} error during download: {error_obj}"
        append_to_log(error_message)
        progress_label.set("Download failed.")

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
            "status": "failure",
            "error_logs": str(error_obj),
        })

    ############################################################################
    #                     LOCAL VIDEO PROCESSING PAGE
    ############################################################################

    def init_local_processing(self):
        """UI for local video processing."""
        self.clear_content_frame()
        progress_label = ctk.StringVar(value="Status: Ready")
        progress_bar = ttk.Progressbar(self.content_frame, orient="horizontal", mode="determinate", length=600)

        ctk.CTkLabel(self.content_frame, text="Process Local Video File", font=("Helvetica", 18)).pack(pady=20)

        ctk.CTkButton(
            self.content_frame,
            text="Upload File",
            command=lambda: run_in_thread(self.process_local_video, progress_label, progress_bar),
        ).pack(pady=20)

        progress_bar.pack(pady=10)
        ctk.CTkLabel(self.content_frame, textvariable=progress_label, font=("Helvetica", 14)).pack(pady=10)

    def process_local_video(self, progress_label, progress_bar):
        """
        Let user pick a local video file, process it, then prompt for saving stems.
        """
        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")],
        )
        if not file_path:
            progress_label.set("No file selected.")
            return

        progress_label.set("Processing video... Please wait.")
        start_time = datetime.now()
        original_stem = Path(file_path).stem

        try:
            video_length_seconds = get_video_length(file_path)
            video_length_str = format_duration(video_length_seconds) if video_length_seconds else None

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
                "status": "success",
                "function_type": "Local Video Upload",  # Add function type here
            }
            send_log_to_server(log_data)

            # Update UI
            elapsed = log_data['processing_time']
            progress_label.set(f"Video processed successfully in {elapsed:.2f} seconds.")

        except Exception as e:
            self._handle_local_processing_error(e, file_path, start_time, progress_label, "Local Video Upload")

    def _handle_download_error(self, progress_label, start_time, error_type, error_obj, function_type):
        """Common handler for download exceptions."""
        error_message = f"{error_type.capitalize()} error during download: {error_obj}"
        append_to_log(error_message)
        progress_label.set("Download failed.")

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
        
    def _handle_local_processing_error(self, error_obj, file_path, start_time, progress_label):
        """Handle errors for local video processing."""
        error_message = f"Unexpected error during video processing: {error_obj}"
        progress_label.set("Processing failed.")
        append_to_log(error_message)

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
            "video_length": None,
            "processing_time": calculate_processing_time(start_time, datetime.now()),
            "status": "failure",
            "error_logs": error_message,
        })

###############################################################################
#                             MAIN ENTRY POINT
###############################################################################
if __name__ == "__main__":
    app = RianVideoProcessingTool()
    app.mainloop()