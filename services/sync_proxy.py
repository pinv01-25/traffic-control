import logging
import os
from typing import Any, Dict

import requests
from dotenv import load_dotenv

load_dotenv()

SYNC_API_URL = os.getenv("SYNC_API_URL")
logger = logging.getLogger(__name__)

class SyncProxy:
    """Proxy service for interacting with traffic-sync service."""
    
    @staticmethod
    def send_to_sync(data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data to traffic-sync service for optimization.
        
        Args:
            data: Data to send for optimization
        Returns:
            Optimization response
        """
        try:
            url = f"{SYNC_API_URL}/evaluate"
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            logger.info("Successfully sent data to sync service")
            return response.json()
        except Exception as e:
            logger.error(f"Error sending data to sync: {str(e)}")
            raise
    
    @staticmethod
    def send_batch_for_optimization(batch_data: Dict[str, Any], target_sensor_id: str) -> Dict[str, Any]:
        """Send batch data to traffic-sync service for optimization.
        
        Args:
            batch_data: Complete data batch
            target_sensor_id: ID of the target sensor for optimization (used as traffic_light_id)
        Returns:
            Batch optimization response
        """
        try:
            # Prepare batch data for sync service
            # The sync service expects the batch format with 'traffic_light_id' field
            sync_batch_data = {
                "version": batch_data["version"],
                "type": "data",  # Changed from "batch" to "data"
                "timestamp": batch_data["timestamp"],
                "traffic_light_id": target_sensor_id,
                "sensors": batch_data["sensors"]
            }
            
            logger.info(f"Sending batch with {len(batch_data['sensors'])} sensors for optimization")
            logger.info(f"Target sensor ID: {target_sensor_id}")
            
            # Send to the unified evaluate endpoint
            url = f"{SYNC_API_URL}/evaluate"
            response = requests.post(url, json=sync_batch_data)
            response.raise_for_status()
            
            logger.info("Successfully sent batch data to sync service")
            return response.json()
            
        except Exception as e:
            logger.error(f"Error sending batch for optimization: {str(e)}")
            raise

# Legacy function for backward compatibility
def send_to_sync(data: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    return SyncProxy.send_to_sync(data)