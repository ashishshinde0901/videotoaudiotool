import subprocess
from pathlib import Path
import shutil
import sys


def get_bundled_path(executable_name):
    """
    Returns the full path to a bundled executable (e.g., ffmpeg or demucs).
    Falls back to checking PATH for unbundled execution.
    """
    if hasattr(sys, "_MEIPASS"):  # PyInstaller bundled app
        base_path = Path(sys._MEIPASS) / "bin"
        binary_path = base_path / executable_name
        if not binary_path.exists():
            raise RuntimeError(f"Executable '{executable_name}' not found in bundled environment.")
    else:  # Standalone script, look for the binary in the system PATH
        binary_path = shutil.which(executable_name)
        if not binary_path:
            raise RuntimeError(f"Executable '{executable_name}' not found in PATH.")
        binary_path = Path(binary_path)

    return str(binary_path)  # Ensure it's a string for subprocess


def process_video(file_path, temp_dir):
    """
    Processes a video file to extract audio and separate it into vocals and background noise.
    """
    try:
        # Paths to the ffmpeg and demucs binaries
        ffmpeg_path = get_bundled_path("ffmpeg")
        demucs_path = get_bundled_path("demucs")

        # Step 1: Extract audio from the video
        audio_path = temp_dir / "extracted_audio.mp3"
        ffmpeg_command = f'"{ffmpeg_path}" -i "{file_path}" -q:a 0 -map a "{audio_path}"'
        print(f"Running command: {ffmpeg_command}")  # Debugging
        result = subprocess.run(ffmpeg_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout.decode(), result.stderr.decode())

        # Step 2: Separate audio using Demucs
        demucs_command = f'"{demucs_path}" --two-stems=vocals "{audio_path}" -o "{temp_dir}"'
        print(f"Running command: {demucs_command}")  # Debugging
        result = subprocess.run(demucs_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout.decode(), result.stderr.decode())

        # Locate the separated files
        demucs_output_dir = temp_dir / "htdemucs" / audio_path.stem
        vocals_path = demucs_output_dir / "vocals.wav"
        noise_path = demucs_output_dir / "no_vocals.wav"

        # Return paths to the processed files
        return vocals_path, noise_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error during processing: {e}\nCommand output: {e.output.decode()}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {e}")