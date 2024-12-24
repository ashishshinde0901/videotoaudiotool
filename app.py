import os
import tempfile
import sys
import subprocess
import requests
import platform
import socket
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
from moviepy.video.io.VideoFileClip import VideoFileClip
from video_processor import process_video, get_bundled_path


def send_log_to_server(log_data):
    """Send log data to the server."""
    try:
        server_url = "http://127.0.0.1:5175/log"  # The server endpoint
        response = requests.post(server_url, json=log_data, timeout=10)
        response.raise_for_status()
        print("Log sent successfully to the server.")
    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        messagebox.showerror("Server Error", f"Failed to send log to server: {http_err}")
    except requests.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        messagebox.showerror("Server Error", f"Failed to send log to server: {req_err}")


def download_youtube_video(link, temp_dir):
    """Download a YouTube video and store it in a temporary directory."""
    yt_dlp_path = get_bundled_path("yt-dlp.exe")
    output_path = Path(temp_dir) / "youtube_video.mp4"
    command = [
        yt_dlp_path,
        "-f", "best[ext=mp4]",
        "-o", str(output_path),
        link,
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_path


def get_video_length(video_path):
    """Calculate the length of a video in seconds."""
    try:
        with VideoFileClip(str(video_path)) as video:
            return round(video.duration, 2)
    except Exception as e:
        print(f"Error calculating video length: {e}")
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
        messagebox.showinfo("File Saved", f"Saved as: {save_path}")


def calculate_processing_time(start_time, end_time):
    """Calculate processing time in seconds."""
    return (end_time - start_time).total_seconds()


def run_in_thread(target, *args):
    """Run a function in a separate thread."""
    threading.Thread(target=target, args=args, daemon=True).start()


def process_local_video(progress_label, progress_bar):
    """Process a locally uploaded video file."""
    file_path = filedialog.askopenfilename(
        title="Select a Video File",
        filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")],
    )
    if not file_path:
        progress_label.set("No file selected.")
        return

    progress_label.set("Processing video... Please wait.")
    progress_bar.start()
    start_time = datetime.now()

    try:
        video_length = get_video_length(file_path)
        with tempfile.TemporaryDirectory() as temp_dir:
            vocals_path, noise_path, _ = process_video(file_path, Path(temp_dir))
            save_file(vocals_path, "Save Vocals as WAV")
            save_file(noise_path, "Save Background Noise as WAV")

        end_time = datetime.now()
        processing_time = calculate_processing_time(start_time, end_time)
        # Log successful processing
        send_log_to_server({
            "ip": socket.gethostbyname(socket.gethostname()),
            "machine_name": platform.node(),
            "machine_specs": {
                "os": platform.system(),
                "os_version": platform.version(),
                "machine": platform.machine(),
            },
            "file_size": os.path.getsize(file_path),
            "video_length": video_length,
            "status": "success",
            "type": "local",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "processing_time": processing_time,
        })
        progress_label.set("Video processed successfully.")
    except Exception as e:
        progress_label.set(f"Processing failed: {e}")
        messagebox.showerror("Error", f"Processing failed: {e}")
    finally:
        progress_bar.stop()


def process_youtube_video(youtube_link_var, progress_label, progress_bar):
    """Download and save a YouTube video."""
    link = youtube_link_var.get().strip()
    if not link:
        progress_label.set("YouTube link is empty.")
        return

    progress_label.set("Downloading video... Please wait.")
    progress_bar.start()
    start_time = datetime.now()

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = download_youtube_video(link, temp_dir)
            video_length = get_video_length(video_path)
            save_file(video_path, "Save Downloaded Video")

        end_time = datetime.now()
        processing_time = calculate_processing_time(start_time, end_time)
        # Log successful download
        send_log_to_server({
            "ip": socket.gethostbyname(socket.gethostname()),
            "machine_name": platform.node(),
            "machine_specs": {
                "os": platform.system(),
                "os_version": platform.version(),
                "machine": platform.machine(),
            },
            "youtube_link": link,
            "video_length": video_length,
            "status": "success",
            "type": "youtube",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "processing_time": processing_time,
        })
        progress_label.set("Video downloaded successfully.")
    except Exception as e:
        progress_label.set(f"Download failed: {e}")
        messagebox.showerror("Error", f"Failed to download video: {e}")
    finally:
        progress_bar.stop()


def main():
    ctk.set_appearance_mode("Light")  # Set light theme
    ctk.set_default_color_theme("blue")  # Set primary color theme

    app = ctk.CTk()
    app.title("Video Audio Processor")
    app.geometry("900x700")

    # Navigation bar
    nav_frame = ctk.CTkFrame(app)
    nav_frame.pack(fill="x")

    ctk.CTkButton(nav_frame, text="Local Video Processing", command=lambda: open_local_processing_window()).pack(side="left", padx=20)
    ctk.CTkButton(nav_frame, text="YouTube Download", command=lambda: open_youtube_download_window()).pack(side="left", padx=20)

    ctk.CTkLabel(app, text="Select a feature from the navigation above.", font=("Helvetica", 16)).pack(pady=20)
    app.mainloop()


def open_local_processing_window():
    app = ctk.CTk()
    app.title("Local Video Processing")
    app.geometry("900x700")

    progress_label = ctk.StringVar(value="Status: Ready")
    progress_bar = ttk.Progressbar(app, orient="horizontal", mode="indeterminate")

    ctk.CTkLabel(app, text="Process Local Video File", font=("Helvetica", 16)).pack(pady=10)
    ctk.CTkButton(app, text="Upload File", command=lambda: run_in_thread(process_local_video, progress_label, progress_bar)).pack(pady=10)
    ctk.CTkLabel(app, textvariable=progress_label, font=("Helvetica", 14)).pack(pady=10)
    progress_bar.pack(pady=10)

    app.mainloop()


def open_youtube_download_window():
    app = ctk.CTk()
    app.title("YouTube Video Download")
    app.geometry("900x700")

    youtube_link_var = ctk.StringVar()
    progress_label = ctk.StringVar(value="Status: Ready")
    progress_bar = ttk.Progressbar(app, orient="horizontal", mode="indeterminate")

    ctk.CTkLabel(app, text="Download Video from YouTube", font=("Helvetica", 16)).pack(pady=10)
    ctk.CTkEntry(app, textvariable=youtube_link_var, width=400).pack(pady=10)
    ctk.CTkButton(app, text="Download Video", command=lambda: run_in_thread(process_youtube_video, youtube_link_var, progress_label, progress_bar)).pack(pady=10)
    ctk.CTkLabel(app, textvariable=progress_label, font=("Helvetica", 14)).pack(pady=10)
    progress_bar.pack(pady=10)

    app.mainloop()


if __name__ == "__main__":
    main()
    