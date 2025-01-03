import requests
import json
from logger_utils import CONFIG, ENVIRONMENT, append_to_log

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

# Load config for development/production
load_config()

def fetch_promotions(license_key):
    """
    Fetch promotions from the backend using the provided license key.
    Returns:
      - A list of promotion messages if successful.
      - An empty list if there is an error or no promotions.
    """
    url = CONFIG.get("promotions_url", "http://127.0.0.1:3000/VOXTools/GetPromotion")
    params = {"lk": license_key}  # Query parameter as per the API in the image

    try:
        append_to_log(f"Fetching promotions from {url} with license key {license_key}")
        response = requests.get(url, params=params, timeout=10, verify=False)  # Use GET request as specified

        if response.status_code == 200:
            data = response.json()
            append_to_log(f"Promotions fetched successfully: {data}")
            return data.get("promotions", [])
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