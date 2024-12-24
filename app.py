import os
import tempfile
import sys
import requests
import platform
import socket
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, Tk, Label, Button, Frame, StringVar, Entry
from moviepy.video.io.VideoFileClip import VideoFileClip
from video_processor import process_video, get_bundled_path


def send_log_to_server(log_data):
    """Send log data to the server."""
    try:
        server_url = "http://127.0.0.1:5175/log"  # Update this as necessary
        response = requests.post(server_url, json=log_data, timeout=10)
        response.raise_for_status()
        print("Log sent successfully to the server.")
    except requests.RequestException as e:
        print(f"Failed to send log to server: {e}")
        messagebox.showerror("Server Error", f"Failed to send log to server: {e}")


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
        defaultextension=".wav" if file_path.suffix == ".wav" else ".mp4",
        filetypes=[("Audio Files", "*.wav"), ("MP4 Files", "*.mp4"), ("All Files", "*.*")],
    )
    if save_path:
        os.rename(file_path, save_path)
        messagebox.showinfo("File Saved", f"Saved as: {save_path}")


def main():
    root = Tk()
    root.title("Video Audio Processor")
    root.geometry("900x700")
    root.resizable(False, False)
    root.configure(bg="#f8f9fa")

    youtube_link = StringVar(value="")
    status_label = StringVar(value="Status: Ready")

    def update_status(message, color="#007bff"):
        """Update the status label."""
        status_label.set(message)
        status_lbl.config(fg=color)
        root.update_idletasks()

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
        try:
            video_length = get_video_length(file_path)
            with tempfile.TemporaryDirectory() as temp_dir:
                vocals_path, noise_path, _ = process_video(file_path, Path(temp_dir))
                save_file(vocals_path, "Save Vocals")
                save_file(noise_path, "Save Background Noise")

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
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                video_path = download_youtube_video(link, temp_dir)
                video_length = get_video_length(video_path)
                save_file(video_path, "Save Downloaded Video")

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
            })
            update_status("Video downloaded successfully.", "#28a745")
        except Exception as e:
            update_status(f"Download failed: {e}", "#dc3545")
            messagebox.showerror("Error", f"Failed to download video: {e}")

    # UI Components
    Label(root, text="Video Audio Processor", font=("Helvetica", 20, "bold"), bg="#f8f9fa", fg="#212529").pack(pady=15)

    # Local Video Processing Section
    local_frame = Frame(root, bg="#ffffff", highlightbackground="#007bff", highlightthickness=2)
    local_frame.pack(pady=20, padx=20, fill="x")
    Label(local_frame, text="Process Local Video File", font=("Helvetica", 14, "bold"), bg="#ffffff").pack(pady=10)
    Label(local_frame, text="Upload a video to extract vocals and background noise.", bg="#ffffff", fg="#6c757d").pack(pady=5)
    Button(local_frame, text="Upload File", command=process_local_video, bg="#007bff", fg="#ffffff", font=("Helvetica", 12)).pack(pady=10)

    # YouTube Video Download Section
    youtube_frame = Frame(root, bg="#ffffff", highlightbackground="#007bff", highlightthickness=2)
    youtube_frame.pack(pady=20, padx=20, fill="x")
    Label(youtube_frame, text="Download Video from YouTube", font=("Helvetica", 14, "bold"), bg="#ffffff").pack(pady=10)
    Label(youtube_frame, text="Enter the YouTube link to download the video.", bg="#ffffff", fg="#6c757d").pack(pady=5)
    Entry(youtube_frame, textvariable=youtube_link, font=("Helvetica", 12), width=50).pack(pady=10)
    Button(youtube_frame, text="Download Video", command=process_youtube_video, bg="#007bff", fg="#ffffff", font=("Helvetica", 12)).pack(pady=10)

    # Status Label
    status_lbl = Label(root, textvariable=status_label, bg="#f8f9fa", fg="#007bff", font=("Helvetica", 12, "italic"))
    status_lbl.pack(pady=20)

    # Exit Button
    Button(root, text="Exit", command=root.quit, bg="#dc3545", fg="#ffffff", font=("Helvetica", 12)).pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()