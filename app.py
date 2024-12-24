import os
import tempfile
import sys
import subprocess
import requests
import platform
import socket
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
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
        messagebox.showerror("Server Error", f"Failed to send log to server: {http_err}")
    except requests.RequestException as req_err:
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


def main():
    ctk.set_appearance_mode("Dark")  # Set dark theme
    ctk.set_default_color_theme("blue")  # Set primary color theme

    app = ctk.CTk()
    app.title("Video Audio Processor")
    app.geometry("900x700")
    app.resizable(False, False)

    youtube_link = ctk.StringVar(value="")
    status_label = ctk.StringVar(value="Status: Ready")

    def update_status(message, color="#007bff"):
        """Update the status label."""
        status_label.set(message)
        status_lbl.configure(fg_color=color)
        app.update_idletasks()

    def process_local_video():
        """Process a locally uploaded video file."""
        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")],
        )
        if not file_path:
            update_status("No file selected.", "#dc3545")
            return

        update_status("Processing video... Please wait.")
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
            update_status("Video processed successfully.", "#28a745")
        except Exception as e:
            update_status(f"Processing failed: {e}", "#dc3545")
            messagebox.showerror("Error", f"Processing failed: {e}")

    def process_youtube_video():
        """Download and save a YouTube video."""
        link = youtube_link.get().strip()
        if not link:
            update_status("YouTube link is empty.", "#dc3545")
            return

        update_status("Downloading video... Please wait.")
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
            update_status("Video downloaded successfully.", "#28a745")
        except Exception as e:
            update_status(f"Download failed: {e}", "#dc3545")
            messagebox.showerror("Error", f"Failed to download video: {e}")

    # UI Components
    ctk.CTkLabel(app, text="Video Audio Processor", font=("Helvetica", 28)).pack(pady=20)

    # Local Video Processing Section
    local_frame = ctk.CTkFrame(app)
    local_frame.pack(pady=20, padx=20, fill="x")
    ctk.CTkLabel(local_frame, text="Process Local Video File", font=("Helvetica", 16)).pack(pady=10)
    ctk.CTkLabel(local_frame, text="Upload a video to extract vocals and background noise.").pack(pady=5)
    ctk.CTkButton(local_frame, text="Upload File", command=process_local_video).pack(pady=10)

    # YouTube Video Download Section
    youtube_frame = ctk.CTkFrame(app)
    youtube_frame.pack(pady=20, padx=20, fill="x")
    ctk.CTkLabel(youtube_frame, text="Download Video from YouTube", font=("Helvetica", 16)).pack(pady=10)
    ctk.CTkLabel(youtube_frame, text="Enter the YouTube link to download the video.").pack(pady=5)
    ctk.CTkEntry(youtube_frame, textvariable=youtube_link, width=400).pack(pady=10)
    ctk.CTkButton(youtube_frame, text="Download Video", command=process_youtube_video).pack(pady=10)

    # Status Label
    status_lbl = ctk.CTkLabel(app, textvariable=status_label, font=("Helvetica", 14))
    status_lbl.pack(pady=20)

    # Exit Button
    ctk.CTkButton(app, text="Exit", command=app.quit, fg_color="red").pack(pady=10)

    app.mainloop()


if __name__ == "__main__":
    main()