import os
import sys
import threading
import tempfile
import requests
from datetime import datetime

# Global log file reference
LOG_FILE = os.path.join(tempfile.gettempdir(), "rian_tool_logs.txt")
log_lock = threading.Lock()

def initialize_log_file():
    """Initialize the log file if it doesn't exist."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as log_file:
            log_file.write(f"Log initialized at {datetime.now().isoformat()}\n")

def append_to_log(message):
    """
    Thread-safe method to append a message to the log file.
    Logs include timestamps to help with debugging.
    """
    with log_lock:
        with open(LOG_FILE, "a") as log_file:
            log_file.write(f"{datetime.now().isoformat()} - {message}\n")

def send_log_to_server(log_data):
    """
    Send log data to a remote server. 
    If it fails, log the exception locally using 'append_to_log'.
    """
    try:
        server_url = "http://127.0.0.1:5175/log"
        append_to_log(f"Preparing to send log to server: {log_data}")
        response = requests.post(server_url, json=log_data, timeout=10)
        response.raise_for_status()
        append_to_log(f"Log sent successfully: {response.status_code}, {response.text}")
    except Exception as e:
        append_to_log(f"Error sending log to server: {e}")