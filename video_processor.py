import subprocess
import sys
import io
import shutil
from pathlib import Path

# We'll use a standard-library context manager to capture output
import contextlib

def get_bundled_path(executable_name):
    """
    Returns the full path to a bundled executable (e.g., ffmpeg, yt-dlp).
    Falls back to checking PATH for unbundled execution.
    """
    try:
        if hasattr(sys, "_MEIPASS"):  # PyInstaller-bundled environment
            base_path = Path(sys._MEIPASS) / "bin"
            binary_path = base_path / executable_name

            if not binary_path.exists():
                raise FileNotFoundError(f"Executable '{executable_name}' "
                                        f"not found in bundled environment: {binary_path}")
            return str(binary_path)
        else:
            binary_path = shutil.which(executable_name)
            if not binary_path:
                raise FileNotFoundError(f"Executable '{executable_name}' not found in PATH.")
            return str(binary_path)
    except Exception as e:
        raise RuntimeError(f"Error locating the binary '{executable_name}': {e}")


@contextlib.contextmanager
def capture_demucs_output():
    """
    Context manager to capture stdout/stderr into two StringIO buffers.
    This avoids the 'NoneType has no attribute write' issue in windowed mode,
    and lets us retrieve/inspect logs for debugging or display in the GUI.
    """
    original_stdout, original_stderr = sys.stdout, sys.stderr
    captured_out = io.StringIO()
    captured_err = io.StringIO()

    try:
        sys.stdout = captured_out
        sys.stderr = captured_err
        yield captured_out, captured_err
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr


def process_video(file_path, temp_dir):
    """
    Processes a video file to extract audio (with FFmpeg) and separate it
    into vocals/noise (with Demucs), returning paths to the two stems
    plus any Demucs logs captured along the way.
    """
    input_file = Path(file_path)
    if not input_file.is_file():
        raise FileNotFoundError(f"Input file does not exist or is not a valid file: {file_path}")

    try:
        # 1. Locate FFmpeg
        try:
            ffmpeg_path = get_bundled_path("ffmpeg.exe")
        except Exception as e:
            raise RuntimeError(f"Failed to locate FFmpeg: {e}")

        # 2. Extract audio from the video using FFmpeg
        audio_path = Path(temp_dir) / "extracted_audio.mp3"
        ffmpeg_command = [
            ffmpeg_path,
            "-i", str(file_path),
            "-q:a", "0",
            "-map", "a",
            str(audio_path),
        ]

        try:
            # Capture FFmpeg logs in case you want to debug them as well
            result = subprocess.run(
                ffmpeg_command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Optionally inspect FFmpeg logs here:
            # ffmpeg_stdout = result.stdout.decode(errors="ignore")
            # ffmpeg_stderr = result.stderr.decode(errors="ignore")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"FFmpeg command failed with error code {e.returncode}. "
                f"Output: {e.stderr.decode(errors='ignore')}"
            )

        if not audio_path.is_file():
            raise FileNotFoundError("Audio extraction failed; no audio file generated.")

        # 3. Run Demucs to separate audio
        #    We'll capture stdout/stderr so we can display them in our GUI
        try:
            from demucs.separate import main as demucs_main
        except ImportError:
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

        # Capture logs from Demucs
        with capture_demucs_output() as (demucs_out, demucs_err):
            try:
                demucs_main(demucs_args)
            except Exception as e:
                raise RuntimeError(f"Demucs separation process failed: {e}")

            # Extract the logs from StringIO
            demucs_stdout = demucs_out.getvalue()
            demucs_stderr = demucs_err.getvalue()

        # 4. Verify output files from Demucs
        demucs_output_dir = Path(temp_dir) / "mdx_extra_q" / audio_path.stem
        vocals_path = demucs_output_dir / "vocals.wav"
        noise_path = demucs_output_dir / "no_vocals.wav"

        if not vocals_path.is_file():
            raise FileNotFoundError("Demucs did not produce a 'vocals.wav' file.")
        if not noise_path.is_file():
            raise FileNotFoundError("Demucs did not produce a 'no_vocals.wav' file.")

        # Return paths + logs for debugging or display
        return vocals_path, noise_path, (demucs_stdout, demucs_stderr)

    except Exception as e:
        raise RuntimeError(f"Unexpected error during video processing: {e}")