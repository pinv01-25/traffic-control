import copy
import requests
import os
from dotenv import load_dotenv
from models.schemas import TrafficData, OptimizationData, DownloadRequest
from utils.time import unix_to_iso, iso_to_unix

load_dotenv()

STORAGE_API_URL = os.getenv("STORAGE_API_URL")

def prepare_storage_payload(data: dict) -> dict:
    """Prepare data for storage by converting timestamp to Unix format.
    
    Creates a copy of the data to avoid modifying the original.
    Works with both traffic data and optimization data.
    """
    # Deep copy to avoid modifying the original data
    storage_data = copy.deepcopy(data)
    
    # Ensure timestamp is in Unix format
    if "timestamp" in storage_data and isinstance(storage_data["timestamp"], str):
        storage_data["timestamp"] = iso_to_unix(storage_data["timestamp"])
    
    # Convert any nested Pydantic models to dictionaries
    for key, value in storage_data.items():
        if hasattr(value, "dict"):
            storage_data[key] = value.dict()
    
    return storage_data

def upload_to_storage(data: dict) -> dict:
    """Upload data to traffic-storage service.
    
    Automatically prepares the payload with Unix timestamp.
    """
    try:
        # Check if data is of type optimization
        if data.get("type") == "optimization":
            if isinstance(data.get("timestamp"), str):
                print("Optimization data received with ISO timestamp.")
                # Convert timestamp to Unix format
                print(f"Original timestamp: {data['timestamp']}")
                data["timestamp"] = iso_to_unix(data["timestamp"])   
                print("Converted to Unix timestamp.")
                print(f"Data after conversion: {data["timestamp"]}")     
        
        # Prepare payload with Unix timestamp
        storage_payload = prepare_storage_payload(data)
        
        url = f"{STORAGE_API_URL}/upload"
        response = requests.post(url, json=storage_payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error uploading to storage: {str(e)}")
        raise

def download_from_storage(request: DownloadRequest) -> dict:
    """Download data from traffic-storage based on TLS ID, timestamp, and type.
    
    Accepts timestamp in ISO format and converts as needed.
    """
    try:
        # Convert timestamp to Unix for storage request
        unix_timestamp = iso_to_unix(request.timestamp)
        
        url = f"{STORAGE_API_URL}/download"
        payload = {
            "traffic_light_id": request.traffic_light_id,
            "timestamp": unix_timestamp,
            "type": request.type
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Convert back timestamp to ISO format for downstream compatibility
        if "timestamp" in result and isinstance(result["timestamp"], int):
            result["timestamp"] = unix_to_iso(result["timestamp"])
            
        return result
    except Exception as e:
        print(f"Error downloading from storage: {str(e)}")
        raise