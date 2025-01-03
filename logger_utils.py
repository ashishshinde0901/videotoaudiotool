import os
import threading
import tempfile
import requests
import json
from datetime import datetime, timezone

from project.license_utils import get_stored_license_data

# Global variables
CONFIG_FILE = "config.json"
LOG_FILE = os.path.join(tempfile.gettempdir(), "rian_tool_logs.txt")
log_lock = threading.Lock()

# Detect environment
ENVIRONMENT = os.getenv("ENV", "development")
CONFIG = {}

def get_current_utc_time():
    """
    Utility function to get the current UTC time in ISO 8601 format.
    """
    return datetime.now(timezone.utc).isoformat()

def load_config():
    """
    Load configuration from config.json based on the current environment (ENVIRONMENT).
    """
    global CONFIG
    try:
        with open(CONFIG_FILE, "r") as config_file:
            all_configs = json.load(config_file)
            CONFIG = all_configs.get(ENVIRONMENT, {})
            if not CONFIG:
                raise ValueError(f"No configuration found for environment: {ENVIRONMENT}")
        append_to_log(f"Configuration loaded for {ENVIRONMENT} environment: {CONFIG}")
    except FileNotFoundError:
        append_to_log("Error: Configuration file not found.")
        raise
    except json.JSONDecodeError:
        append_to_log("Error: Invalid JSON in configuration file.")
        raise
    except Exception as e:
        append_to_log(f"Error loading configuration: {e}")
        raise



def initialize_log_file():
    """
    Initialize the log file if it doesn't exist.
    """
    try:
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w") as log_file:
                log_file.write(f"Log initialized at {get_current_utc_time()}\n")
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
                log_file.write(f"{get_current_utc_time()} - {message}\n")
        print(f"Logged: {message}")  # Optional console output for immediate feedback
    except Exception as e:
        print(f"Error writing to log file: {e}")
        print(f"{get_current_utc_time()} - Fallback log: {message}")

def send_log_to_server(log_data):
    """
    Send log data to a remote server in the specified format.
    """
    try:
        server_url = CONFIG.get("server_url")
        if not server_url:
            raise ValueError("Server URL is not configured.")

        # Retrieve the license key from stored data if not provided in log_data
        stored_license_data = get_stored_license_data()
        license_key = log_data.get("license_key") or (stored_license_data.get("license_key") if stored_license_data else "unknown")

        # Format logs as per server requirements
        formatted_log = {
            "lk": license_key,
            "logs": [
                {
                    "fnm": log_data.get("function_type", "string"),
                    "ip": log_data.get("ip", "string"),
                    "mnm": log_data.get("machine_name", "string"),
                    "os": log_data.get("machine_specs", {}).get("os", "string"),
                    "osv": log_data.get("machine_specs", {}).get("os_version", "string"),
                    "st": log_data.get("start_time", "string"),
                    "et": log_data.get("end_time", "string"),
                    "fi": str(log_data.get("file_size", "string")),
                    "el": log_data.get("processing_time", "string"),
                    "isf": 1 if log_data.get("status") == "failure" else 0,
                }
            ],
        }

        append_to_log(f"Preparing to send log to server: {formatted_log}")
        response = requests.post(server_url, json=formatted_log, timeout=10, verify=False)
        append_to_log(f"Response received: Status Code = {response.status_code}")

        if response.status_code == 200:
            append_to_log("Log sent successfully.")
        else:
            append_to_log(f"Failed to send log. Server responded with: {response.status_code} - {response.text}")
    except requests.exceptions.Timeout:
        append_to_log("Error: Request timed out while sending log to server.")
    except requests.exceptions.ConnectionError:
        append_to_log("Error: Connection to the log server failed.")
    except requests.exceptions.RequestException as e:
        append_to_log(f"Error sending log to server: {e}")
    except Exception as e:
        append_to_log(f"Unexpected error during server logging: {e}")
        
# Example Debugging Usage
if __name__ == "__main__":
    try:
        # Load configuration
        load_config()

        # Initialize logging
        initialize_log_file()
        append_to_log("Testing append_to_log function.")

        # Test sending log to the server
        test_log_data = {
            "license_key": "ABC123",
            "function_type": "TestFunction",
            "ip": "127.0.0.1",
            "machine_name": "TestMachine",
            "machine_specs": {
                "os": "Windows",
                "os_version": "10.0.19044",
            },
            "start_time": get_current_utc_time(),
            "end_time": get_current_utc_time(),
            "file_size": 123456,
            "processing_time": "2.5",
            "status": "success",
        }
        send_log_to_server(test_log_data)
    except Exception as e:
        append_to_log(f"Error occurred: {e}")