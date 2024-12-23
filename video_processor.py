# video_processor.py

import subprocess
from pathlib import Path
import shutil
import sys

def get_bundled_path(executable_name):
    """
    Returns the full path to a bundled executable (e.g., ffmpeg).
    Falls back to checking PATH for unbundled execution.
    """
    # Check if running in PyInstaller bundled environment
    try:
        if hasattr(sys, "_MEIPASS"):  
            base_path = Path(sys._MEIPASS) / "bin"
            binary_path = base_path / executable_name

            if not binary_path.exists():
                raise FileNotFoundError(f"Executable '{executable_name}' not found in bundled environment: {binary_path}")
            return str(binary_path)
        else:
            # Fallback to the system PATH
            binary_path = shutil.which(executable_name)
            if not binary_path:
                raise FileNotFoundError(f"Executable '{executable_name}' not found in PATH.")
            return str(binary_path)
    except Exception as e:
        raise RuntimeError(f"Error locating the binary '{executable_name}': {e}")

def process_video(file_path, temp_dir):
    """
    Processes a video file to extract audio and separate it into vocals and background noise.
    """
    # First, check that the input video file actually exists
    input_file = Path(file_path)
    if not input_file.is_file():
        raise FileNotFoundError(f"Input file does not exist or is not a valid file: {file_path}")

    try:
        # Step 1: Get the path to ffmpeg
        try:
            ffmpeg_path = get_bundled_path("ffmpeg.exe")
        except Exception as e:
            raise RuntimeError(f"Failed to locate FFmpeg: {e}")

        # Step 2: Extract audio from the video using FFmpeg
        audio_path = Path(temp_dir) / "extracted_audio.mp3"
        ffmpeg_command = [
            ffmpeg_path,
            "-i", str(file_path),
            "-q:a", "0",
            "-map", "a",
            str(audio_path),
        ]

        try:
            print(f"Running FFmpeg command: {ffmpeg_command}")
            result = subprocess.run(
                ffmpeg_command, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            # Optionally, you can print FFmpeg stdout/stderr for debugging:
            # print("FFmpeg STDOUT:", result.stdout.decode(errors="ignore"))
            # print("FFmpeg STDERR:", result.stderr.decode(errors="ignore"))
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"FFmpeg command failed with error code {e.returncode}. "
                f"Output: {e.stderr.decode(errors='ignore')}"
            )

        if not audio_path.is_file():
            raise FileNotFoundError("Audio extraction failed; no audio file generated.")

        # Step 3: Run Demucs (Python package) to separate audio
        try:
            from demucs.separate import main as demucs_main
        except ImportError as e:
            raise RuntimeError(
                "Demucs is not installed or failed to import. "
                "Please ensure 'demucs' is installed in your environment."
            )

        demucs_args = [
            "--two-stems=vocals",
            "-n", "mdx_extra_q",
            str(audio_path),
            "-o", str(temp_dir),
        ]

        try:
            print(f"Running Demucs with arguments: {demucs_args}")
            demucs_main(demucs_args)
        except Exception as e:
            raise RuntimeError(f"Demucs separation process failed: {e}")

        # Locate separated files
        demucs_output_dir = Path(temp_dir) / "mdx_extra_q" / audio_path.stem
        vocals_path = demucs_output_dir / "vocals.wav"
        noise_path = demucs_output_dir / "no_vocals.wav"

        # Verify that Demucs actually produced the output files
        if not vocals_path.is_file():
            raise FileNotFoundError("Demucs did not produce a 'vocals.wav' file.")
        if not noise_path.is_file():
            raise FileNotFoundError("Demucs did not produce a 'no_vocals.wav' file.")

        return vocals_path, noise_path

    except Exception as e:
        raise RuntimeError(f"Unexpected error during video processing: {e}")


