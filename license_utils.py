import os
import json
import socket
import requests
import customtkinter as ctk
from tkinter import messagebox

# Your logger imports (assuming these exist in your project)
from logger_utils import CONFIG, ENVIRONMENT, append_to_log
from stored_license_data import get_stored_license_data, store_license_data
import sys

CONFIG_FILE = "config.json"


def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and PyInstaller.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Development environment: Use the current directory
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def load_config():
    """
    Load configuration from config.json based on the current environment.
    Supports both development and bundled (PyInstaller) environments.
    """
    global CONFIG
    config_path = get_resource_path(CONFIG_FILE)

    try:
        with open(config_path, "r") as config_file:
            all_configs = json.load(config_file)
            CONFIG = all_configs.get(ENVIRONMENT, {})
            if not CONFIG:
                raise ValueError(f"No configuration found for environment: {ENVIRONMENT}")
        append_to_log(f"Configuration loaded for {ENVIRONMENT} environment: {CONFIG}")
    except FileNotFoundError:
        append_to_log(f"Error: Configuration file not found at path: {config_path}")
        raise
    except json.JSONDecodeError:
        append_to_log(f"Error: Invalid JSON in configuration file at path: {config_path}")
        raise
    except Exception as e:
        append_to_log(f"Error loading configuration: {e}")
        raise


# Load config for development/production
load_config()

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
        if app.winfo_exists():
            app.destroy()  # Close the entire app when the Cancel button is pressed
            
    popup.protocol("WM_DELETE_WINDOW", on_cancel)

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
    url = CONFIG.get("activate_license_url")
    payload = {"lk": license_key}

    try:
        response = requests.post(url, json=payload, timeout=10, verify=False)
        append_to_log(f"Activate License Response: Status Code = {response.status_code}, Body = {response.text}")

        if response.status_code == 200:
            try:
                response_json = response.json()
                append_to_log(f"Activation Response JSON: {response_json}")
                return True, ""
            except json.JSONDecodeError:
                append_to_log("Error: Server returned non-JSON response during activation.")
                return False, "Server returned invalid response. Please contact support."
        else:
            try:
                error_reason = response.json().get("error", "Unknown error")
                return False, error_reason
            except json.JSONDecodeError:
                return False, f"Unexpected server response: {response.text}"
    except requests.RequestException as e:
        append_to_log(f"Network error during license activation: {e}")
        return False, f"Network error: {e}"


def validate_license_with_server(client_id, license_key):
    """
    Validate the license key with the server.
    """
    url = CONFIG.get("validate_license_url")
    payload = {"lk": license_key}

    try:
        response = requests.post(url, json=payload, timeout=10, verify=False)
        append_to_log(f"Validate License Response: Status Code = {response.status_code}, Body = {response.text}")

        if response.status_code == 200:
            try:
                response_json = response.json()
                append_to_log(f"Validation Response JSON: {response_json}")
                return True, ""
            except json.JSONDecodeError:
                append_to_log("Error: Server returned non-JSON response during validation.")
                return False, "Server returned invalid response. Please contact support."
        else:
            try:
                error_reason = response.json().get("error", "Unknown error")
                return False, error_reason
            except json.JSONDecodeError:
                return False, f"Unexpected server response: {response.text}"
    except requests.RequestException as e:
        append_to_log(f"Network error during license validation: {e}")
        return False, f"Network error: {e}"


def ensure_valid_license_on_startup(app):
    """
    Validates the license every time the application is launched.
    Ensures that a valid license key is stored locally and verified by the server.
    Prompts the user for a new license key if validation fails without exiting the app.
    
    Behavior:
     - If stored_data exists, call validate:
         - If validate is good, break.
         - Else, prompt user to re-enter and call activate.
           If activate is successful, store immediately and break.
           Otherwise keep prompting.
     - If no stored_data, prompt user for ID/key, call activate:
         - If activate is successful, store immediately and break.
         - Otherwise keep prompting.
    """

    stored_data = get_stored_license_data()

    if stored_data:
        client_id = stored_data["client_id"]
        license_key = stored_data["license_key"]
    else:
        # Default client_id to machine hostname on first time
        client_id = socket.gethostname()
        license_key = ""

    while True:
        # If we already have something stored, attempt validation first
        if client_id and license_key:
            valid, reason = validate_license_with_server(client_id, license_key)
            if valid:
                append_to_log(f"License validated successfully for client: {client_id}")
                # Re-store to ensure any local updates are consistent
                store_license_data(client_id, license_key)
                break
            else:
                append_to_log(f"License validation failed: {reason}")
                msg = f"Your license key is invalid or revoked.\nReason: {reason}\nPlease re-enter."
                messagebox.showerror("Invalid License", msg)

        # Prompt the user for new license details (or first-time user)
        new_client_id, new_license_key = prompt_for_client_id_and_license_key(app, existing_client_id=client_id)
        if not new_client_id or not new_license_key:
            # Show a warning if the user cancels or enters nothing
            messagebox.showwarning(
                "License Required",
                "You must enter a valid Client ID and License Key to use the application."
            )
            continue  # Keep re-prompting

        # Try to activate with the newly provided info
        activation_success, activation_reason = activate_license_with_server(new_client_id, new_license_key)
        if activation_success:
            # If activation is successful, store data immediately, log success, and break out
            client_id, license_key = new_client_id, new_license_key
            store_license_data(client_id, license_key)
            append_to_log("License activated successfully.")
            break
        else:
            # Activation failed, show error and re-prompt
            append_to_log(f"License activation failed: {activation_reason}")
            messagebox.showerror(
                "License Activation Failed",
                f"Reason: {activation_reason}\nPlease re-enter your credentials."
            )
