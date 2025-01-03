import os
import json
import socket
import requests
import customtkinter as ctk
from tkinter import messagebox
from logger_utils import load_config, CONFIG, ENVIRONMENT, append_to_log

LICENSE_FILE = "license_data.json"  # Name of local JSON file to store license info

# Load config for development/production
load_config()

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

def prompt_for_client_id_and_license_key(app, existing_client_id=""):
    """
    Prompt the user to enter (or re-enter) their Client ID and License Key in a modal popup.
    Blocks the main window until the user enters data or closes the popup.
    Returns (client_id, license_key) or (None, None) if canceled.
    """
    popup = ctk.CTkToplevel(app)
    popup.title("Enter License Details")
    popup.geometry("400x300")
    popup.resizable(False, False)

    ctk.CTkLabel(
        popup,
        text="Please enter your Client ID:",
        font=("Helvetica", 14)
    ).pack(pady=(20, 5))

    client_id_var = ctk.StringVar(value=existing_client_id)
    client_id_entry = ctk.CTkEntry(popup, textvariable=client_id_var, width=250)
    client_id_entry.pack(pady=5)

    ctk.CTkLabel(
        popup,
        text="Please enter your License Key:",
        font=("Helvetica", 14)
    ).pack(pady=(20, 5))

    license_var = ctk.StringVar()
    license_entry = ctk.CTkEntry(popup, textvariable=license_var, width=250)
    license_entry.pack(pady=5)

    # Focus on client ID first if it's empty, else license field
    if existing_client_id:
        license_entry.focus()
    else:
        client_id_entry.focus()

    result = {
        "client_id": None,
        "license_key": None
    }

    def on_submit():
        cid = client_id_var.get().strip()
        lkey = license_var.get().strip()
        if cid and lkey:
            result["client_id"] = cid
            result["license_key"] = lkey
        popup.destroy()

    def on_cancel():
        popup.destroy()

    ctk.CTkButton(popup, text="Submit", command=on_submit).pack(pady=(15, 5))
    ctk.CTkButton(popup, text="Cancel", command=on_cancel).pack()

    # Make the popup modal
    popup.grab_set()
    app.wait_window(popup)

    return result["client_id"], result["license_key"]

def activate_license_with_server(client_id, license_key):
    """
    Activate the license key with the server.
    """
    url = CONFIG.get("activate_license_url", "http://127.0.0.1:3000/VOXTools/ActivateLicense")
    payload = {"lk": license_key}

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            append_to_log("License activated successfully.")
            return True, ""
        else:
            error_reason = response.json().get("error", "Unknown error")
            append_to_log(f"License activation failed: {error_reason}")
            return False, error_reason
    except requests.RequestException as e:
        append_to_log(f"Network error during license activation: {e}")
        return False, f"Network error: {e}"

def validate_license_with_server(client_id, license_key):
    """
    Validate the license key with the server.
    """
    url = CONFIG.get("validate_license_url", "http://127.0.0.1:3000/VOXTools/ValidateLicense")
    payload = {"lk": license_key}

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            append_to_log("License validated successfully.")
            return True, ""
        else:
            error_reason = response.json().get("error", "Unknown error")
            append_to_log(f"License validation failed: {error_reason}")
            return False, error_reason
    except requests.RequestException as e:
        append_to_log(f"Network error during license validation: {e}")
        return False, f"Network error: {e}"

def ensure_valid_license(app):
    """
    Ensures that a valid license key is present locally and verified by the server.
    If no license is stored or it's invalid, activates or prompts user to re-enter a valid key.
    """
    stored_data = get_stored_license_data()

    if stored_data:
        client_id = stored_data["client_id"]
        license_key = stored_data["license_key"]
    else:
        # Default client_id to machine hostname
        client_id = socket.gethostname()
        license_key = ""

    while True:
        if client_id and license_key:
            valid, reason = validate_license_with_server(client_id, license_key)
            if valid:
                store_license_data(client_id, license_key)
                return  # License verified
            else:
                append_to_log(f"License validation failed: {reason}")
                msg = f"Your license key is invalid or revoked.\nReason: {reason}\nPlease re-enter."
                messagebox.showwarning("Invalid License", msg)

                new_client_id, new_license_key = prompt_for_client_id_and_license_key(app, existing_client_id=client_id)
                if not new_client_id or not new_license_key:
                    app.destroy()
                    return
                activate_license_with_server(new_client_id, new_license_key)
                client_id, license_key = new_client_id, new_license_key
        else:
            new_client_id, new_license_key = prompt_for_client_id_and_license_key(app, existing_client_id=client_id)
            if not new_client_id or not new_license_key:
                app.destroy()
                return
            activate_license_with_server(new_client_id, new_license_key)
            client_id, license_key = new_client_id, new_license_key