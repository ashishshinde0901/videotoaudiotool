import os
import sys

# Example: main.py
from rian_gui import RianVideoProcessingTool

def set_environment_for_pyinstaller():
    """
    If running under PyInstaller (frozen), then set ENV=production.
    Otherwise, default to development unless already set externally.
    """
    if getattr(sys, 'frozen', False):
        # We are in a PyInstaller bundle
        os.environ["ENV"] = "production"
    else:
        # We are not bundled
        if "ENV" not in os.environ:
            os.environ["ENV"] = "development"

if __name__ == "__main__":
    set_environment_for_pyinstaller()
    app = RianVideoProcessingTool()
    app.mainloop()