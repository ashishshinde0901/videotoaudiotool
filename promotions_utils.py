import requests
import json
from logger_utils import CONFIG, ENVIRONMENT, append_to_log
from stored_license_data import get_stored_license_data

CONFIG_FILE = "config.json"


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


def fetch_promotions(license_key):
    """
    Fetch promotions from the backend using the provided license key.
    Returns:
      - A list of promotion messages if successful.
      - An empty list if there is an error or no promotions.
    """
    load_config()

    url = CONFIG.get("promotions_url")
    append_to_log(f"Promotions URL: {url}")

    # If there's locally stored license data, use that license key
    stored_data = get_stored_license_data()
    final_license_key = stored_data.get("license_key") if stored_data else license_key

    # Request parameters
    params = {"lk": final_license_key}

    # Log the request being sent
    append_to_log(f"Request being sent to server:")
    append_to_log(f"URL: {url}")
    append_to_log(f"Query Params: {params}")
    append_to_log(f"HTTP Method: GET")

    try:
        append_to_log(f"Fetching promotions from {url} with license key {final_license_key}")
        response = requests.get(url, params=params, timeout=10, verify=False)  # Use GET request as specified

        # Log the raw response text so we see exactly what the server returned
        append_to_log(f"Raw server response (status={response.status_code}): {response.text}")

        # If status code is 200, attempt to parse JSON
        if response.status_code == 200:
            try:
                data = response.json()
                append_to_log(f"Promotions fetched successfully (JSON parsed): {data}")
                return data.get("promotions", [])
            except json.JSONDecodeError:
                # The server responded with non-JSON or an empty body
                append_to_log("Error: The server response was not valid JSON.")
                return []
        else:
            append_to_log(f"Error fetching promotions: {response.status_code} - {response.text}")
            return []
    except requests.RequestException as e:
        append_to_log(f"Request error while fetching promotions: {e}")
        return []


# Example usage
if __name__ == "__main__":
    license_key = "YOUR_LICENSE_KEY_HERE"  # Replace with actual license key
    promotions = fetch_promotions(license_key)
    print(promotions)