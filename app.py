# app.py (or your main GUI script)

import os
import stat
import tempfile
from pathlib import Path
from tkinter import filedialog, messagebox, Tk, Label, Button, Frame, StringVar
import sys

# Import the process_video function from video_processor.py
from video_processor import process_video

def fix_permissions_in_meipass():
    """
    Fix the permissions for binaries in the _MEIPASS/bin directory 
    in a PyInstaller-bundled environment.
    """
    if hasattr(sys, "_MEIPASS"):  
        bin_dir = Path(sys._MEIPASS) / "bin"
        for binary in bin_dir.iterdir():
            # Make sure it's executable by user/group/others
            binary.chmod(binary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def main():
    """Main application logic."""
    # Fix binary permissions for bundled environment
    fix_permissions_in_meipass()

    root = Tk()
    root.title("Video Audio Processor")
    root.geometry("600x400")
    root.resizable(False, False)
    root.configure(bg="#f4f4f9")

    selected_file_path = StringVar(value="No file selected")

    def select_file():
        """Open file dialog to select a video file."""
        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")],
        )
        if file_path:
            selected_file_path.set(file_path)
            start_processing(file_path)

    def start_processing(file_path):
        """Start video processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            try:
                status_label.config(text="Processing... Please wait.", fg="#007bff")
                root.update_idletasks()

                # Call the processing function
                vocals_path, noise_path = process_video(file_path, temp_dir_path)

                status_label.config(text="Processing Complete!", fg="green")
                messagebox.showinfo("Success", "Audio separation completed!")

                # Prompt user to save files
                save_file(vocals_path, "Save Clean Audio (Vocals)")
                save_file(noise_path, "Save Background Noise")

            except FileNotFoundError as e:
                status_label.config(text="Processing Failed", fg="red")
                messagebox.showerror("File Not Found", str(e))
            except RuntimeError as e:
                status_label.config(text="Processing Failed", fg="red")
                messagebox.showerror("Error", str(e))
            except Exception as e:
                # Catch any unexpected error
                status_label.config(text="Processing Failed", fg="red")
                messagebox.showerror("Unexpected Error", str(e))
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
                # Using rename can cause issues if saving across different drives; consider shutil.move if needed
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
    file_frame.pack(pady=20)

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
        textvariable=selected_file_path,
        bg="#f4f4f9",
        fg="gray",
        font=("Helvetica", 12),
    ).pack(pady=5)

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

# IMPORTANT: Fix the __name__ check here
if __name__ == "__main__":
    main()