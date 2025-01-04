import os
import json
import socket
import requests

LICENSE_FILE = "license_data.json" 


def get_stored_license_data():
    """
    Load previously stored license data from a JSON file if it exists.
    Returns a dict { "client_id": ..., "license_key": ... } or None if missing/invalid.
    """
    if not os.path.exists(LICENSE_FILE):
        return None

    try:
        with open(LICENSE_FILE, "r") as file:
            data = json.load(file)
            if "client_id" in data and "license_key" in data:
                return data
            else:
                return None
    except Exception as e:
        append_to_log(f"Error reading license data: {e}")
        return None

def store_license_data(client_id, license_key):
    """
    Store the client_id and license_key to a local file in JSON format.
    Overwrites any existing data.
    """
    data = {
        "client_id": client_id,
        "license_key": license_key
    }
    try:
        with open(LICENSE_FILE, "w") as file:
            json.dump(data, file)
        append_to_log("License data stored successfully.")
    except Exception as e:
        append_to_log(f"Error storing license data: {e}")