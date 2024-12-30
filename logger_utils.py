import os
import threading
import tempfile
import requests
from datetime import datetime

# Global log file reference
LOG_FILE = os.path.join(tempfile.gettempdir(), "rian_tool_logs.txt")
log_lock = threading.Lock()

def initialize_log_file():
    """Initialize the log file if it doesn't exist."""
    try:
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w") as log_file:
                log_file.write(f"Log initialized at {datetime.now().isoformat()}\n")
        append_to_log("Log file initialized successfully.")
    except Exception as e:
        print(f"Error initializing log file: {e}")
        append_to_log(f"Error during log file initialization: {e}")

def append_to_log(message):
    """
    Thread-safe method to append a message to the log file.
    Logs include timestamps to help with debugging.
    """
    try:
        with log_lock:
            with open(LOG_FILE, "a") as log_file:
                log_file.write(f"{datetime.now().isoformat()} - {message}\n")
        # Print to console for immediate debugging (optional)
        print(f"Logged: {message}")
    except Exception as e:
        print(f"Error writing to log file: {e}")
        # If logging fails, fallback to console logging
        print(f"{datetime.now().isoformat()} - Fallback log: {message}")

def send_log_to_server(log_data):
    """
    Send log data to a remote server. 
    If it fails, log the exception locally using 'append_to_log'.
    """
    try:
        server_url = "http://127.0.0.1:3000/log"
        append_to_log(f"Preparing to send log to server: {log_data}")
        
        # Debug: Log the full server URL
        append_to_log(f"Server URL: {server_url}")
        
        # Send the request
        response = requests.post(server_url, json=log_data, timeout=10)
        
        # Debug: Log the response status and content
        append_to_log(f"Response received: Status Code = {response.status_code}")
        append_to_log(f"Response Content: {response.text}")
        
        # Raise exception for non-2xx responses
        response.raise_for_status()
        
        # Log success
        append_to_log(f"Log sent successfully: {response.status_code}, {response.text}")
    except requests.exceptions.Timeout:
        append_to_log("Error: Request timed out while sending log to server.")
    except requests.exceptions.ConnectionError:
        append_to_log("Error: Connection to the log server failed.")
    except requests.exceptions.RequestException as e:
        append_to_log(f"Error sending log to server: {e}")
    except Exception as e:
        # Log any other unexpected exceptions
        append_to_log(f"Unexpected error during server logging: {e}")

# Example Debugging Usage:
if __name__ == "__main__":
    initialize_log_file()
    append_to_log("Testing append_to_log function.")
    test_log_data = {"key": "value", "timestamp": datetime.now().isoformat()}
    send_log_to_server(test_log_data)