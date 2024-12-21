import os
import subprocess
from tkinter import filedialog, messagebox, Tk, Label, Button, Frame, StringVar
from pathlib import Path

# Function to process the video file
def process_video(file_path):
    try:
        # Create a temporary directory for processing
        output_dir = Path("output_files")
        output_dir.mkdir(exist_ok=True)

        # Step 1: Extract audio from the video
        audio_path = output_dir / "extracted_audio.mp3"
        ffmpeg_command = f'ffmpeg -i "{file_path}" -q:a 0 -map a "{audio_path}"'
        subprocess.run(ffmpeg_command, shell=True, check=True)

        # Step 2: Separate audio using Demucs
        demucs_command = f'demucs --two-stems=vocals "{audio_path}" -o "{output_dir}"'
        subprocess.run(demucs_command, shell=True, check=True)

        # Locate the separated files
        demucs_output_dir = output_dir / "htdemucs" / audio_path.stem
        vocals_path = demucs_output_dir / "vocals.wav"
        noise_path = demucs_output_dir / "no_vocals.wav"

        # Return paths to the processed files
        return vocals_path, noise_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error during processing: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {e}")

# Main application logic
def main():
    # Create a Tkinter window
    root = Tk()
    root.title("Video Audio Processor")
    root.geometry("500x300")
    root.resizable(False, False)
    root.configure(bg="#f4f4f9")

    # Initialize selected file path
    selected_file_path = StringVar(value="No file selected")

    # Select file function
    def select_file():
        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")]
        )
        if file_path:
            selected_file_path.set(f"Selected: {os.path.basename(file_path)}")
            start_processing(file_path)

    # Start processing function
    def start_processing(file_path):
        try:
            status_label.config(text="Processing... Please wait.", fg="#007bff")
            root.update_idletasks()

            # Run the processing logic
            vocals_path, noise_path = process_video(file_path)
            status_label.config(text="Processing Complete!", fg="green")
            messagebox.showinfo("Success", "Audio separation completed!")

            # Offer download options
            save_file(vocals_path, "Save Clean Audio (Vocals)")
            save_file(noise_path, "Save Background Noise")
        except RuntimeError as e:
            status_label.config(text="Processing Failed", fg="red")
            messagebox.showerror("Error", str(e))
        finally:
            status_label.config(text="Ready.")

    # Save file function
    def save_file(file_path, title):
        save_path = filedialog.asksaveasfilename(
            title=title,
            defaultextension=".wav",
            filetypes=[("Audio Files", "*.wav")]
        )
        if save_path:
            os.rename(file_path, save_path)
            messagebox.showinfo("Download Complete", f"File saved to: {save_path}")

    # UI Components
    Label(root, text="Video Audio Processor", font=("Helvetica", 20, "bold"), bg="#f4f4f9").pack(pady=15)

    file_frame = Frame(root, bg="#f4f4f9")
    file_frame.pack(pady=10)
    Label(file_frame, textvariable=selected_file_path, bg="#f4f4f9", fg="gray", font=("Helvetica", 12)).pack(pady=5)
    Button(file_frame, text="Select Video", command=select_file, bg="#007bff", fg="white", font=("Helvetica", 12), width=20).pack(pady=10)

    status_label = Label(root, text="Ready.", bg="#f4f4f9", fg="black", font=("Helvetica", 12))
    status_label.pack(pady=20)

    Button(root, text="Exit", command=root.quit, bg="#d9534f", fg="white", font=("Helvetica", 12), width=10).pack(pady=10)

    # Run the Tkinter loop
    root.mainloop()

if __name__ == "__main__":
    main()