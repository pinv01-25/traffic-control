import copy
import logging
import os
import time

import requests
from dotenv import load_dotenv
from models.schemas import DownloadRequest
from services.data_processor import DataProcessor
from utils.time import iso_to_unix, unix_to_iso

load_dotenv()

STORAGE_API_URL = os.getenv("STORAGE_API_URL")
logger = logging.getLogger(__name__)

# Retry configuration for BlockDAG timing issues
MAX_DOWNLOAD_RETRIES = 5
RETRY_DELAY_BASE = 2  # seconds
RETRY_DELAY_MAX = 10  # seconds

class StorageProxy:
    """Proxy service for interacting with traffic-storage service."""
    
    @staticmethod
    def prepare_storage_payload(data: dict) -> dict:
        """Prepare data for storage by converting timestamp to Unix format.
        
        Creates a copy of the data to avoid modifying the original.
        Works with both traffic data and optimization data.
        """
        # Deep copy to avoid modifying the original data
        storage_data = copy.deepcopy(data)
        
        # Handle different data types
        data_type = storage_data.get("type", "data")
        
        if data_type == "data":  # Changed from "data-batch" to "data"
            # For data batches, use the internal unix timestamp if available
            if "_unix_timestamp" in storage_data:
                storage_data["timestamp"] = storage_data["_unix_timestamp"]
                # Remove internal field
                del storage_data["_unix_timestamp"]
            elif "timestamp" in storage_data and isinstance(storage_data["timestamp"], str):
                storage_data["timestamp"] = iso_to_unix(storage_data["timestamp"])
        elif data_type == "optimization":
            # Check if this is an optimization batch (has 'optimizations' field)
            if "optimizations" in storage_data:
                # Convert timestamp in the batch header
                if "timestamp" in storage_data and isinstance(storage_data["timestamp"], str):
                    storage_data["timestamp"] = iso_to_unix(storage_data["timestamp"])
                
                # Convert timestamps in each optimization
                for optimization in storage_data["optimizations"]:
                    if "timestamp" in optimization and isinstance(optimization["timestamp"], str):
                        optimization["timestamp"] = iso_to_unix(optimization["timestamp"])
        else:
                # Single optimization, convert timestamp if needed
            if "timestamp" in storage_data and isinstance(storage_data["timestamp"], str):
                storage_data["timestamp"] = iso_to_unix(storage_data["timestamp"])
        
        # Convert any nested Pydantic models to dictionaries
        for key, value in storage_data.items():
            if hasattr(value, "dict"):
                storage_data[key] = value.dict()
        
        return storage_data

    @staticmethod
    def upload_to_storage(data: dict) -> dict:
        """Upload data to traffic-storage service.
        
        Automatically prepares the payload with Unix timestamp.
        """
        try:
            # Prepare payload with Unix timestamp
            storage_payload = StorageProxy.prepare_storage_payload(data)
            
            url = f"{STORAGE_API_URL}/upload"
            response = requests.post(url, json=storage_payload)
            response.raise_for_status()
            
            logger.info(f"Successfully uploaded {data.get('type', 'unknown')} data to storage")
            return response.json()
        except Exception as e:
            logger.error(f"Error uploading to storage: {str(e)}")
            raise

    @staticmethod
    def upload_data_batch(batch_data: dict) -> dict:
        """Upload a data batch to storage.
        
        Args:
            batch_data: Processed data batch
        Returns:
            Storage response
        """
        try:
            # Process the batch if not already processed
            if "_unix_timestamp" not in batch_data:
                batch_data = DataProcessor.process_data_batch(batch_data)
            
            return StorageProxy.upload_to_storage(batch_data)
        except Exception as e:
            logger.error(f"Error uploading data batch to storage: {str(e)}")
            raise

    @staticmethod
    def download_from_storage(request: DownloadRequest) -> dict:
        """Download data from traffic-storage based on TLS ID, timestamp, and type.
        
        Accepts timestamp in ISO format and converts as needed.
        Includes retry logic for BlockDAG timing issues.
        """
        last_exception = None
        
        for attempt in range(MAX_DOWNLOAD_RETRIES):
            try:
                # Convert timestamp to Unix for storage request
                unix_timestamp = iso_to_unix(request.timestamp)
                
                url = f"{STORAGE_API_URL}/download"
                payload = {
                    "traffic_light_id": request.traffic_light_id,
                    "timestamp": unix_timestamp,
                    "type": request.type
                }
                
                logger.info(f"Download attempt {attempt + 1}/{MAX_DOWNLOAD_RETRIES} for {request.traffic_light_id}")
                response = requests.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                # Convert back timestamp to ISO format for downstream compatibility
                if "timestamp" in result and isinstance(result["timestamp"], int):
                    result["timestamp"] = unix_to_iso(result["timestamp"])
                    
                    logger.info(f"Successfully downloaded {request.type} data from storage on attempt {attempt + 1}")
                return result
                    
            except requests.exceptions.HTTPError as e:
                last_exception = e
                if e.response.status_code == 500 and "Record not found" in str(e):
                    # This is likely a BlockDAG timing issue, retry
                    if attempt < MAX_DOWNLOAD_RETRIES - 1:
                        delay = min(RETRY_DELAY_BASE * (2 ** attempt), RETRY_DELAY_MAX)
                        logger.warning(f"Record not found on attempt {attempt + 1}, retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Failed to download after {MAX_DOWNLOAD_RETRIES} attempts due to record not found")
                        raise
                else:
                    # Other HTTP errors, don't retry
                    logger.error(f"HTTP error downloading from storage: {str(e)}")
                    raise
            except Exception as e:
                    last_exception = e
                    if attempt < MAX_DOWNLOAD_RETRIES - 1:
                        delay = min(RETRY_DELAY_BASE * (2 ** attempt), RETRY_DELAY_MAX)
                        logger.warning(f"Download attempt {attempt + 1} failed: {str(e)}, retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Failed to download after {MAX_DOWNLOAD_RETRIES} attempts")
            raise
        
        # If we get here, all retries failed
        logger.error(f"All {MAX_DOWNLOAD_RETRIES} download attempts failed")
        raise last_exception

    @staticmethod
    def download_data_batch(reference_traffic_light_id: str, timestamp: str) -> dict:
        """Download a data batch from storage.
        
        Args:
            reference_traffic_light_id: Reference traffic light ID
            timestamp: ISO timestamp
        Returns:
            Data batch
        """
        try:
            # Create download request for data type
            request = DownloadRequest(
                traffic_light_id=reference_traffic_light_id,
                timestamp=timestamp,
                type="data"  # Changed from "data-batch" to "data"
            )
            
            logger.info(f"Downloading data batch for {reference_traffic_light_id} at {timestamp}")
            return StorageProxy.download_from_storage(request)
        except Exception as e:
            logger.error(f"Error downloading data batch from storage: {str(e)}")
            raise

# Legacy functions for backward compatibility
def prepare_storage_payload(data: dict) -> dict:
    """Legacy function for backward compatibility."""
    return StorageProxy.prepare_storage_payload(data)

def upload_to_storage(data: dict) -> dict:
    """Legacy function for backward compatibility."""
    return StorageProxy.upload_to_storage(data)

def download_from_storage(request: DownloadRequest) -> dict:
    """Legacy function for backward compatibility."""
    return StorageProxy.download_from_storage(request)