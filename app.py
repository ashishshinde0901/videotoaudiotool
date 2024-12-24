import os
import stat
import tempfile
import sys
import subprocess
import requests
import platform
import socket
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, Tk, Label, Button, Frame, StringVar, Entry
from video_processor import process_video, get_bundled_path
from moviepy.video.io.VideoFileClip import VideoFileClip  # For video length calculation


def fix_permissions_in_meipass():
    if hasattr(sys, "_MEIPASS"):  
        bin_dir = Path(sys._MEIPASS) / "bin"
        for binary in bin_dir.iterdir():
            binary.chmod(binary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def send_log_to_server(log_data):
    try:
        server_url = "http://127.0.0.1:5175/log"
        response = requests.post(server_url, json=log_data, timeout=10)
        response.raise_for_status()
        print("Log sent successfully to the server.")
    except requests.RequestException as e:
        print(f"Failed to send log to server: {e}")
        messagebox.showerror("Server Error", f"Failed to send log to server: {e}")


def download_youtube_video(link, output_dir):
    try:
        yt_dlp_path = get_bundled_path("yt-dlp.exe")
        output_path = Path(output_dir) / "youtube_video.mp4"
        command = [
            yt_dlp_path,
            "-f", "best[ext=mp4]",
            "-o", str(output_path),
            link,
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"yt-dlp failed: {e.stderr.decode(errors='ignore')}")


def get_video_length(video_path):
    try:
        with VideoFileClip(str(video_path)) as video:
            return round(video.duration, 2)
    except Exception as e:
        print(f"Error calculating video length: {e}")
        return None


def main():
    fix_permissions_in_meipass()

    root = Tk()
    root.title("Video Audio Processor")
    root.geometry("800x600")
    root.resizable(False, False)
    root.configure(bg="#f8f9fa")

    selected_file_path = StringVar(value="No file selected")
    youtube_link = StringVar(value="")

    def select_file():
        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")],
        )
        if file_path:
            selected_file_path.set(file_path)
            video_length = get_video_length(file_path)
            start_processing(file_path, upload_type="local", video_length=video_length)

    def process_youtube_video():
        """Download and store a video from a YouTube link with user-specified name and location."""
        link = youtube_link.get().strip()
        if not link:
            messagebox.showerror("Error", "Please enter a YouTube link.")
            return

        try:
            # Prompt user to choose a filename and location
            save_path = filedialog.asksaveasfilename(
                title="Save YouTube Video As",
                defaultextension=".mp4",
                filetypes=[("MP4 Files", "*.mp4"), ("All Files", "*.*")],
            )
            if not save_path:
                messagebox.showinfo("Cancelled", "Download cancelled by user.")
                return

            status_label.config(text="Downloading video... Please wait.", fg="#007bff")
            root.update_idletasks()

            # Create a temporary directory for downloading the video
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = download_youtube_video(link, temp_dir)

                # Move the downloaded file to the chosen location
                os.rename(temp_file_path, save_path)
                video_length = get_video_length(save_path)

                status_label.config(text="Video downloaded successfully.", fg="green")
                root.update_idletasks()

                # Send logs for the download event
                log_data = {
                    "ip": socket.gethostbyname(socket.gethostname()),  # Local IP
                    "machine_name": socket.gethostname(),
                    "machine_specs": {
                        "os": platform.system(),
                        "os_version": platform.version(),
                        "machine": platform.machine(),
                    },
                    "start_time": datetime.now().isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "file_size": os.path.getsize(save_path),
                    "video_length": video_length,
                    "upload_type": "youtube",
                    "status": "success",
                    "error_logs": None,
                }
                send_log_to_server(log_data)

                messagebox.showinfo("Success", f"Video downloaded successfully!\nSaved as: {save_path}")

        except Exception as e:
            status_label.config(text="Download Failed", fg="red")
            messagebox.showerror("Error", f"Failed to download YouTube video: {e}")

    def start_processing(file_path, upload_type, video_length):
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                vocals_path, noise_path, _ = process_video(file_path, Path(temp_dir))
                send_log_to_server({
                    "ip": socket.gethostbyname(socket.gethostname()),
                    "machine_name": socket.gethostname(),
                    "machine_specs": {
                        "os": platform.system(),
                        "os_version": platform.version(),
                        "machine": platform.machine(),
                    },
                    "start_time": datetime.now().isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "file_size": os.path.getsize(file_path),
                    "video_length": video_length,
                    "upload_type": upload_type,
                    "status": "success",
                    "error_logs": None,
                })
                messagebox.showinfo("Success", "Audio separation completed!")
            except Exception as e:
                messagebox.showerror("Error", f"Processing failed: {e}")

    # UI Components
    Label(root, text="Video Audio Processor", font=("Helvetica", 20, "bold"), bg="#f8f9fa", fg="#212529").pack(pady=15)

    # Local File Section
    local_frame = Frame(root, bg="#ffffff", highlightbackground="#007bff", highlightthickness=2)
    local_frame.pack(pady=20, padx=10, fill="x")

    Label(local_frame, text="Process Local Video File", font=("Helvetica", 14, "bold"), bg="#ffffff").pack(pady=10)
    Label(local_frame, text="Upload a video file to extract vocals and background noise.", bg="#ffffff", fg="#6c757d").pack(pady=5)
    Button(local_frame, text="Upload File", command=select_file, bg="#007bff", fg="#ffffff", font=("Helvetica", 12)).pack(pady=10)

    # YouTube Video Section
    youtube_frame = Frame(root, bg="#ffffff", highlightbackground="#007bff", highlightthickness=2)
    youtube_frame.pack(pady=20, padx=10, fill="x")

    Label(youtube_frame, text="Download Video from YouTube", font=("Helvetica", 14, "bold"), bg="#ffffff").pack(pady=10)
    Label(youtube_frame, text="Enter the YouTube link to download the video.", bg="#ffffff", fg="#6c757d").pack(pady=5)
    Entry(youtube_frame, textvariable=youtube_link, font=("Helvetica", 12), width=50).pack(pady=10)
    Button(youtube_frame, text="Download Video", command=process_youtube_video, bg="#007bff", fg="#ffffff", font=("Helvetica", 12)).pack(pady=10)

    Button(root, text="Exit", command=root.quit, bg="#dc3545", fg="#ffffff", font=("Helvetica", 12)).pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    main()