import tempfile
import os

def get_output_directory():
    try:
        # Default directory
        output_dir = Path("output_files")
        output_dir.mkdir(exist_ok=True)
        return output_dir
    except OSError as e:
        if e.errno == 30:  # Read-only file system
            print("Read-only file system detected for 'output_files'. Switching to temporary directory.")
            # Fallback to system's temporary directory
            temp_dir = Path(tempfile.mkdtemp())
            print(f"Using temporary directory: {temp_dir}")
            return temp_dir
        else:
            raise e

def process_video(file_path):
    try:
        # Get a writable output directory
        output_dir = get_output_directory()

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
    except OSError as e:
        raise RuntimeError(f"File system error: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {e}")