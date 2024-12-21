import tempfile
from pathlib import Path
import sys

def get_output_directory():
    """
    Returns a writable directory. If the default directory is read-only, it switches to a temporary directory.
    Handles both standalone and PyInstaller bundled environments gracefully.
    """
    try:
        # Determine base path
        if hasattr(sys, "_MEIPASS"):  # PyInstaller bundled app
            base_path = Path(sys._MEIPASS)
        else:  # Standalone Python script
            base_path = Path(__file__).parent.resolve()

        # Default output directory
        output_dir = base_path / "output_files"

        # Attempt to create the directory
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
            raise RuntimeError(f"Error creating directory: {e}")