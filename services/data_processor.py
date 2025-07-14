from typing import Dict, Any, List, Optional
from models.schemas import SensorData, TrafficData
from models.validator import validate_data_payload
from utils.time import normalize_timestamp
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """Service for processing traffic data batches and individual sensor data."""
    
    @staticmethod
    def process_data_batch(batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a data batch by validating each sensor and the overall structure.
        
        Args:
            batch_data: Raw batch data dictionary
        Returns:
            Processed and validated batch data
        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate the entire batch structure
            validate_data_payload(batch_data)
            
            # Validate each individual sensor using Pydantic models
            sensors = batch_data.get("sensors", [])
            for i, sensor in enumerate(sensors):
                try:
                    # Validate sensor using Pydantic model
                    SensorData(**sensor)
                except Exception as e:
                    raise ValueError(f"Sensor at index {i} validation failed: {e}")
            
            # Normalize timestamp
            timestamp = batch_data["timestamp"]
            iso_timestamp, unix_timestamp = normalize_timestamp(timestamp)
            
            # Create processed batch with normalized timestamp
            processed_batch = {
                **batch_data,
                "timestamp": iso_timestamp,
                "_unix_timestamp": unix_timestamp  # Internal field for storage
            }
            
            logger.info(f"Successfully processed data batch with {len(sensors)} sensors")
            return processed_batch
            
        except Exception as e:
            logger.error(f"Failed to process data batch: {e}")
            raise
    
    @staticmethod
    def extract_sensor_data(batch_data: Dict[str, Any], sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Extracts data for a specific sensor from a batch.
        
        Args:
            batch_data: Processed batch data
            sensor_id: ID of the sensor to extract
        Returns:
            Sensor data dictionary or None if not found
        """
        sensors = batch_data.get("sensors", [])
        for sensor in sensors:
            if sensor.get("traffic_light_id") == sensor_id:
                # Convert to single sensor format
                return {
                    "version": batch_data["version"],
                    "type": "data",
                    "timestamp": batch_data["timestamp"],
                    "traffic_light_id": sensor["traffic_light_id"],
                    "controlled_edges": sensor["controlled_edges"],
                    "metrics": sensor["metrics"],
                    "vehicle_stats": sensor["vehicle_stats"]
                }
        return None
    
    @staticmethod
    def extract_sensors_for_optimization(batch_data: Dict[str, Any], target_sensor_id: str) -> List[Dict[str, Any]]:
        """
        Extracts relevant sensors for optimization based on target sensor.
        
        Args:
            batch_data: Processed batch data
            target_sensor_id: ID of the target sensor for optimization
        Returns:
            List of sensor data relevant for optimization
        """
        sensors = batch_data.get("sensors", [])
        relevant_sensors = []
        
        # Find the target sensor
        target_sensor = None
        for sensor in sensors:
            if sensor.get("traffic_light_id") == target_sensor_id:
                target_sensor = sensor
                break
        
        if not target_sensor:
            logger.warning(f"Target sensor {target_sensor_id} not found in batch")
            return []
        
        # For now, return all sensors in the batch
        # This can be enhanced with proximity logic later
        for sensor in sensors:
            sensor_data = {
                "version": batch_data["version"],
                "type": "data",
                "timestamp": batch_data["timestamp"],
                "traffic_light_id": sensor["traffic_light_id"],
                "controlled_edges": sensor["controlled_edges"],
                "metrics": sensor["metrics"],
                "vehicle_stats": sensor["vehicle_stats"]
            }
            relevant_sensors.append(sensor_data)
        
        logger.info(f"Extracted {len(relevant_sensors)} sensors for optimization of {target_sensor_id}")
        return relevant_sensors
    
    @staticmethod
    def convert_legacy_to_batch(legacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts legacy single sensor data to batch format.
        
        Args:
            legacy_data: Legacy single sensor data
        Returns:
            Data in batch format
        """
        return {
            "version": legacy_data["version"],
            "type": "data",  # Changed from "data-batch" to "data"
            "timestamp": legacy_data["timestamp"],
            "traffic_light_id": legacy_data["traffic_light_id"],
            "sensors": [{
                "traffic_light_id": legacy_data["traffic_light_id"],
                "controlled_edges": legacy_data["controlled_edges"],
                "metrics": legacy_data["metrics"],
                "vehicle_stats": legacy_data["vehicle_stats"]
            }]
        }
    
    @staticmethod
    def get_batch_metadata(batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts metadata from batch data for storage.
        
        Args:
            batch_data: Processed batch data
        Returns:
            Metadata dictionary
        """
        return {
            "type": batch_data["type"],
            "timestamp": batch_data["_unix_timestamp"],
            "traffic_light_id": batch_data["traffic_light_id"],  # Changed from "reference_traffic_light_id"
            "sensor_count": len(batch_data.get("sensors", [])),
            "version": batch_data["version"]
        } 