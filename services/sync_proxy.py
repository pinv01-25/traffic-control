import requests
import os
from dotenv import load_dotenv
from utils.time import unix_to_iso

load_dotenv()

SYNC_API_URL = os.getenv("SYNC_API_URL")

def send_to_sync(data: dict) -> dict:
    """Send data to traffic-sync service for optimization.
    
    Ensures timestamp is in ISO format for sync's compatibility.
    """
    try:
        # Make a copy to avoid modifying the original
        sync_data = data.copy()
        
        # Ensure timestamp is in ISO format for sync
        if "timestamp" in sync_data and isinstance(sync_data["timestamp"], int):
            sync_data["timestamp"] = unix_to_iso(sync_data["timestamp"])
        
        url = f"{SYNC_API_URL}/evaluate"
        response = requests.post(url, json=sync_data)
        response.raise_for_status()
        
        result = response.json()
        
        # Ensure the timestamp format is ISO for consistency
        if "timestamp" in result and isinstance(result["timestamp"], int):
            result["timestamp"] = unix_to_iso(result["timestamp"])
            
        return result
    except Exception as e:
        print(f"Error sending to sync: {str(e)}")
        raise