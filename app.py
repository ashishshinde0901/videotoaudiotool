import os
import tempfile
import subprocess
import requests
import platform
import socket
import threading
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, ttk, Toplevel, Text
import customtkinter as ctk
from moviepy.video.io.VideoFileClip import VideoFileClip
from video_processor import process_video, get_bundled_path

LOG_FILE = os.path.join(tempfile.gettempdir(), "rian_tool_logs.txt")
log_lock = threading.Lock()

def initialize_log_file():
    """Initialize the log file if it doesn't exist."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as log_file:
            log_file.write(f"Log initialized at {datetime.now().isoformat()}\n")

def append_to_log(message):
    """Thread-safe method to append a message to the log file."""
    with log_lock:
        with open(LOG_FILE, "a") as log_file:
            log_file.write(f"{datetime.now().isoformat()} - {message}\n")

def format_duration(seconds):
    """Format duration in seconds to minutes:seconds."""
    return str(timedelta(seconds=round(seconds)))

def send_log_to_server(log_data):
    """Send log data to the server."""
    try:
        server_url = "http://127.0.0.1:5175/log"
        append_to_log(f"Preparing to send log to server: {log_data}")
        response = requests.post(server_url, json=log_data, timeout=10)
        response.raise_for_status()
        append_to_log(f"Log sent successfully: {response.status_code}, {response.text}")
    except Exception as e:
        append_to_log(f"Error sending log to server: {e}")

def download_youtube_video(link, temp_dir):
    """Download a YouTube video and store it in a temporary directory."""
    yt_dlp_path = get_bundled_path("yt-dlp.exe")
    if not os.path.exists(yt_dlp_path):
        raise FileNotFoundError(f"yt-dlp executable not found at {yt_dlp_path}")

    output_path = Path(temp_dir) / "youtube_video.mp4"
    command = [
        yt_dlp_path,
        "-f", "best[ext=mp4]",
        "-o", str(output_path),
        link,
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if not output_path.exists():
            raise FileNotFoundError(f"Video file not found at {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"yt-dlp failed: {e.stderr.decode('utf-8')}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error during video download: {e}")

def get_video_length(video_path):
    """Calculate the length of a video in seconds."""
    try:
        with VideoFileClip(str(video_path)) as video:
            return round(video.duration, 2)  # Duration in seconds
    except Exception as e:
        append_to_log(f"Error calculating video length: {e}")
        return None

def save_file(file_path, title):
    """Prompt the user to save a file."""
    save_path = filedialog.asksaveasfilename(
        title=title,
        defaultextension=file_path.suffix,
        filetypes=[("MP4 Files", "*.mp4"), ("WAV Files", "*.wav"), ("All Files", "*.*")],
    )
    if save_path:
        os.rename(file_path, save_path)
        append_to_log(f"File saved: {save_path}")
        messagebox.showinfo("File Saved", f"Saved as: {save_path}")
    else:
        append_to_log("Save operation canceled by user.")

def calculate_processing_time(start_time, end_time):
    """Calculate processing time in seconds."""
    return (end_time - start_time).total_seconds()

def run_in_thread(target, *args):
    """Run a function in a separate thread."""
    threading.Thread(target=target, args=args, daemon=True).start()

class RianVideoProcessingTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Rian Video Processing Tool")
        self.geometry("1000x750")
        self.resizable(False, False)
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")

        initialize_log_file()

        self.nav_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#1e3c72")
        self.nav_frame.pack(side="left", fill="y")

        self.content_frame = ctk.CTkFrame(self, corner_radius=10)
        self.content_frame.pack(side="right", expand=True, fill="both", padx=20, pady=20)

        self.init_navbar()
        self.init_homepage()

    def init_navbar(self):
        """Initialize the navigation bar."""
        ctk.CTkLabel(
            self.nav_frame,
            text="Rian Video Processing Tool",
            font=("Helvetica", 20, "bold"),
            fg_color="#142850",
            text_color="white",
            corner_radius=8,
        ).pack(pady=20)

        ctk.CTkButton(self.nav_frame, text="Home", command=self.init_homepage).pack(pady=10)
        ctk.CTkButton(self.nav_frame, text="Local Processing", command=self.init_local_processing).pack(pady=10)
        ctk.CTkButton(self.nav_frame, text="YouTube Download", command=self.init_youtube_download).pack(pady=10)

    def clear_content_frame(self):
        """Clear the content frame before loading new content."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def init_homepage(self):
        """Initialize the homepage."""
        self.clear_content_frame()
        ctk.CTkLabel(
            self.content_frame,
            text="Welcome to Rian Video Processing Tool",
            font=("Helvetica", 24, "bold"),
        ).pack(pady=40)
        ctk.CTkLabel(
            self.content_frame,
            text="This tool allows you to process videos locally or download YouTube videos with ease.",
            font=("Helvetica", 16),
        ).pack(pady=10)
    
    def init_youtube_download(self):
        """Initialize the YouTube video download page."""
        self.clear_content_frame()
        progress_label = ctk.StringVar(value="Status: Ready")
        progress_bar = ttk.Progressbar(self.content_frame, orient="horizontal", mode="determinate", length=600)
        youtube_link_var = ctk.StringVar()

        ctk.CTkLabel(
            self.content_frame,
            text="Download YouTube Video",
            font=("Helvetica", 18)
        ).pack(pady=20)

        ctk.CTkEntry(
            self.content_frame,
            textvariable=youtube_link_var,
            placeholder_text="Enter YouTube link"
        ).pack(pady=20)

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

        progress_bar.pack(pady=10)
        ctk.CTkLabel(
            self.content_frame,
            textvariable=progress_label,
            font=("Helvetica", 14)
        ).pack(pady=10)

    def process_youtube_video(self, youtube_link_var, progress_label, progress_bar):
        """Download and process a YouTube video."""
        link = youtube_link_var.get().strip()
        if not link:
            progress_label.set("YouTube link is empty.")
            append_to_log("YouTube link is empty.")
            return

        progress_label.set("Downloading video... Please wait.")
        start_time = datetime.now()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                video_path = download_youtube_video(link, temp_dir)
                save_file(video_path, "Save Downloaded Video")

            end_time = datetime.now()
            file_size = os.path.getsize(video_path)
            video_length_seconds = get_video_length(video_path)
            video_length = format_duration(video_length_seconds) if video_length_seconds else None

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
                "video_length": video_length,
                "processing_time": calculate_processing_time(start_time, end_time),
                "type": "youtube",
                "status": "success",
            }
            send_log_to_server(log_data)
            progress_label.set(f"Video downloaded successfully in {log_data['processing_time']:.2f} seconds.")
        except FileNotFoundError as fnf_err:
            error_message = f"File not found: {fnf_err}"
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
                "error_logs": str(fnf_err),
            })
        except RuntimeError as rt_err:
            error_message = f"Runtime error during download: {rt_err}"
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
                "error_logs": str(rt_err),
            })
        except Exception as e:
            error_message = f"Unexpected error: {e}"
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
                "error_logs": str(e),
            })

    def init_local_processing(self):
        """Initialize the local video processing page."""
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
        """Process a local video."""
        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")],
        )
        if not file_path:
            progress_label.set("No file selected.")
            return

        progress_label.set("Processing video... Please wait.")
        start_time = datetime.now()
        try:
            video_length_seconds = get_video_length(file_path)
            video_length = format_duration(video_length_seconds) if video_length_seconds else None

            with tempfile.TemporaryDirectory() as temp_dir:
                vocals_path, noise_path, _ = process_video(file_path, Path(temp_dir))
                save_file(vocals_path, "Save Vocals as WAV")
                save_file(noise_path, "Save Background Noise as WAV")

            end_time = datetime.now()
            file_size = os.path.getsize(file_path)

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
                "video_length": video_length,
                "processing_time": calculate_processing_time(start_time, end_time),
                "status": "success",
            }
            send_log_to_server(log_data)
            progress_label.set(f"Video processed successfully in {log_data['processing_time']:.2f} seconds.")
        except Exception as e:
            error_message = f"Unexpected error during video processing: {e}"
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
                "video_length": None,
                "processing_time": calculate_processing_time(start_time, datetime.now()),
                "status": "failure",
                "error_logs": error_message,
            })

if __name__ == "__main__":
    app = RianVideoProcessingTool()
    app.mainloop()