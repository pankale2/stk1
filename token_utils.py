# Utility functions to save and load Upstox access token securely
import os
import json

def save_access_token(token, file_path="access_token.json"):
    with open(file_path, "w") as f:
        json.dump({"access_token": token}, f)

def load_access_token(file_path="access_token.json"):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                data = json.load(f)
                return data.get("access_token")
            except Exception:
                return None
    return None
