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
from tkinter import filedialog, messagebox, Tk, Label, Button, Frame, StringVar, Entry, Toplevel, Text, Scrollbar, RIGHT, Y, END
from video_processor import process_video


def fix_permissions_in_meipass():
    """
    Fix the permissions for binaries in the _MEIPASS/bin directory 
    in a PyInstaller-bundled environment.
    """
    if hasattr(sys, "_MEIPASS"):  
        bin_dir = Path(sys._MEIPASS) / "bin"
        for binary in bin_dir.iterdir():
            binary.chmod(binary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def send_log_to_server(log_data):
    """Send the JSON log data to the server."""
    try:
        server_url = "http://127.0.0.1:5175/log"  # Change to your server's IP/URL
        response = requests.post(server_url, json=log_data, timeout=10)
        response.raise_for_status()
        print("Log sent successfully to the server.")
    except requests.RequestException as e:
        print(f"Failed to send log to server: {e}")
        messagebox.showerror("Server Error", f"Failed to send log to server: {e}")


def download_youtube_video(link, output_dir):
    """
    Use yt-dlp to download a video from a YouTube link.
    """
    try:
        yt_dlp_path = get_bundled_path("yt-dlp.exe")  # Locate yt-dlp
        output_path = Path(output_dir) / "youtube_video.mp4"
        command = [
            yt_dlp_path,
            "-f", "best[ext=mp4]",  # Download the best MP4 quality
            "-o", str(output_path),  # Specify output file path
            link,
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"yt-dlp failed: {e.stderr.decode(errors='ignore')}")


def main():
    fix_permissions_in_meipass()

    root = Tk()
    root.title("Video Audio Processor")
    root.geometry("700x500")
    root.resizable(False, False)
    root.configure(bg="#f4f4f9")

    selected_file_path = StringVar(value="No file selected")
    youtube_link = StringVar(value="")
    demucs_logs = ["", ""]  # [stdout, stderr] placeholders

    def select_file():
        """Open file dialog to select a video file."""
        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")],
        )
        if file_path:
            selected_file_path.set(file_path)
            start_processing(file_path, upload_type="local")

    def process_youtube_video():
        """Download and process a video from a YouTube link."""
        link = youtube_link.get().strip()
        if not link:
            messagebox.showerror("Error", "Please enter a YouTube link.")
            return

        try:
            # Step 1: Download YouTube video
            status_label.config(text="Downloading video... Please wait.", fg="#007bff")
            root.update_idletasks()

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = download_youtube_video(link, temp_dir)
                status_label.config(text="Video downloaded. Processing...", fg="#007bff")
                root.update_idletasks()

                # Step 2: Process the downloaded video
                start_processing(temp_file_path, upload_type="youtube")
        except Exception as e:
            status_label.config(text="Processing Failed", fg="red")
            messagebox.showerror("Error", f"Failed to process YouTube video: {e}")

    def start_processing(file_path, upload_type):
        """Start video processing."""
        start_time = datetime.now()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            try:
                status_label.config(text="Processing... Please wait.", fg="#007bff")
                root.update_idletasks()

                # Call the processing function
                vocals_path, noise_path, logs = process_video(file_path, temp_dir_path)
                demucs_logs[0], demucs_logs[1] = logs  # Store logs for viewing later

                # Success
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()

                log_data = {
                    "ip": socket.gethostbyname(socket.gethostname()),  # Local IP
                    "machine_name": socket.gethostname(),
                    "machine_specs": {
                        "os": platform.system(),
                        "os_version": platform.version(),
                        "machine": platform.machine(),
                    },
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "file_size": os.path.getsize(file_path),
                    "video_length": None,  # Optionally extract with FFmpeg
                    "processing_time": processing_time,
                    "upload_type": upload_type,  # New: YouTube or Local
                    "status": "success",
                    "error_logs": None,
                }
                send_log_to_server(log_data)

                status_label.config(text="Processing Complete!", fg="green")
                messagebox.showinfo("Success", "Audio separation completed!")

                # Prompt user to save files
                save_file(vocals_path, "Save Clean Audio (Vocals)")
                save_file(noise_path, "Save Background Noise")

            except Exception as e:
                # Failure
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()

                log_data = {
                    "ip": socket.gethostbyname(socket.gethostname()),  # Local IP
                    "machine_name": socket.gethostname(),
                    "machine_specs": {
                        "os": platform.system(),
                        "os_version": platform.version(),
                        "machine": platform.machine(),
                    },
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else None,
                    "video_length": None,  # Optionally extract with FFmpeg
                    "processing_time": processing_time,
                    "upload_type": upload_type,  # New: YouTube or Local
                    "status": "failure",
                    "error_logs": str(e),
                }
                send_log_to_server(log_data)

                status_label.config(text="Processing Failed", fg="red")
                messagebox.showerror("Error", f"Processing failed: {e}")
            finally:
                status_label.config(text="Ready.")

    def save_file(file_path, title):
        """Save the processed file to a user-selected location."""
        if not Path(file_path).is_file():
            messagebox.showerror("Save Error", f"The file {file_path} does not exist or is not accessible.")
            return

        save_path = filedialog.asksaveasfilename(
            title=title,
            defaultextension=".wav",
            filetypes=[("Audio Files", "*.wav")],
        )
        if save_path:
            try:
                os.rename(file_path, save_path)
                messagebox.showinfo("Download Complete", f"File saved to: {save_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file: {e}")

    # UI Components
    Label(
        root,
        text="Video Audio Processor",
        font=("Helvetica", 24, "bold"),
        bg="#f4f4f9",
    ).pack(pady=10)

    Label(
        root,
        text="Easily extract vocals and background noise from your video files.",
        font=("Helvetica", 12),
        bg="#f4f4f9",
        fg="gray",
    ).pack(pady=5)

    file_frame = Frame(root, bg="#f4f4f9")
    file_frame.pack(pady=10)

    Button(
        file_frame,
        text="Upload Your File Here",
        command=select_file,
        bg="#007bff",
        fg="white",
        font=("Helvetica", 12),
        width=20,
    ).pack(pady=10)

    Label(
        root,
        text="Or Enter YouTube Link Below:",
        bg="#f4f4f9",
        fg="gray",
        font=("Helvetica", 12),
    ).pack(pady=5)

    Entry(root, textvariable=youtube_link, font=("Helvetica", 12), width=50).pack(pady=5)

    Button(
        root,
        text="Process YouTube Video",
        command=process_youtube_video,
        bg="#007bff",
        fg="white",
        font=("Helvetica", 12),
        width=20,
    ).pack(pady=10)

    status_label = Label(root, text="Ready.", bg="#f4f4f9", fg="black", font=("Helvetica", 12))
    status_label.pack(pady=10)

    Button(
        root,
        text="Exit",
        command=root.quit,
        bg="#d9534f",
        fg="white",
        font=("Helvetica", 12),
        width=10,
    ).pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()