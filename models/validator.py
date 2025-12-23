import re
from typing import Any, Dict, List, Union

from utils.time import TimestampValidator


class DataValidator:
    """Modular validator for traffic data payloads."""
    
    ALLOWED_TYPES = ["data", "optimization", "batch-optimization"]
    
    @staticmethod
    def validate_required_fields(payload: Dict[str, Any], required_fields: List[str]) -> None:
        """Validates that all required fields are present."""
        missing_fields = [field for field in required_fields if field not in payload]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
    
    @staticmethod
    def validate_version(version: str) -> None:
        """Validates version format (semantic versioning)."""
        if not re.match(r"^\d+(\.\d+)*$", version):
            raise ValueError(f"Invalid version format: {version}. Expected semantic versioning.")
    
    @staticmethod
    def validate_type(data_type: str) -> None:
        """Validates data type."""
        if data_type not in DataValidator.ALLOWED_TYPES:
            raise ValueError(f"Invalid type value: {data_type}. Expected one of {DataValidator.ALLOWED_TYPES}")
    
    @staticmethod
    def validate_timestamp(timestamp: Union[str, int]) -> None:
        """Validates timestamp format."""
        if isinstance(timestamp, str):
            if not TimestampValidator.validate_iso_timestamp(timestamp):
                raise ValueError(f"Invalid timestamp format: {timestamp}. Expected ISO format.")
        elif isinstance(timestamp, int):
            if not TimestampValidator.validate_unix_timestamp(timestamp):
                raise ValueError(f"Invalid Unix timestamp: {timestamp}")
        else:
            raise ValueError(f"Invalid timestamp type: {type(timestamp)}. Expected string or int.")
    
    @staticmethod
    def validate_traffic_light_id(traffic_light_id: str) -> None:
        """Validates traffic light ID format."""
        if not re.match(r'^\d+$', traffic_light_id):
            raise ValueError(f"Invalid traffic_light_id format: {traffic_light_id}. Expected only numbers.")
    
    @staticmethod
    def validate_data_specific_fields(payload: Dict[str, Any]) -> None:
        """Validates fields specific to data type (unified for single and batch)."""
        # Check if it's batch format (has sensors) or single format (has direct fields)
        if "sensors" in payload:
            # Batch format
            required_batch_fields = ["traffic_light_id", "sensors"]
            DataValidator.validate_required_fields(payload, required_batch_fields)
            
            # Validate traffic_light_id
            DataValidator.validate_traffic_light_id(payload["traffic_light_id"])
            
            # Validate sensors
            sensors = payload.get("sensors", [])
            if not isinstance(sensors, list) or len(sensors) == 0:
                raise ValueError("sensors must be a non-empty list")
            
            if len(sensors) > 10:
                raise ValueError("sensors list cannot exceed 10 items")
            
            # Validate each sensor
            sensor_ids = []
            for i, sensor in enumerate(sensors):
                if not isinstance(sensor, dict):
                    raise ValueError(f"sensor at index {i} must be a dictionary")
                
                # Validate sensor has required fields
                required_sensor_fields = ["traffic_light_id", "controlled_edges", "metrics", "vehicle_stats"]
                DataValidator.validate_required_fields(sensor, required_sensor_fields)
                
                # Validate traffic_light_id
                DataValidator.validate_traffic_light_id(sensor["traffic_light_id"])
                sensor_ids.append(sensor["traffic_light_id"])
            
            # Validate traffic_light_id is in sensors
            reference_id = payload["traffic_light_id"]
            if reference_id not in sensor_ids:
                raise ValueError(f"traffic_light_id {reference_id} must be present in sensors list")
        else:
            # Single sensor format (legacy compatibility)
            required_data_fields = ["traffic_light_id", "metrics", "controlled_edges", "vehicle_stats"]
            DataValidator.validate_required_fields(payload, required_data_fields)
            DataValidator.validate_traffic_light_id(payload["traffic_light_id"])
    
    @staticmethod
    def validate_optimization_specific_fields(payload: Dict[str, Any]) -> None:
        """Validates fields specific to optimization type."""
        required_opt_fields = ["optimization", "impact"]
        DataValidator.validate_required_fields(payload, required_opt_fields)
        
        # Validate optimization details
        optimization = payload.get("optimization", {})
        if not isinstance(optimization, dict):
            raise ValueError("optimization must be a dictionary")
        
        required_opt_details = ["green_time_sec", "red_time_sec"]
        DataValidator.validate_required_fields(optimization, required_opt_details)
        
        # Validate green and red times are positive integers
        green_time = optimization.get("green_time_sec")
        red_time = optimization.get("red_time_sec")
        
        if not isinstance(green_time, int) or green_time <= 0:
            raise ValueError("green_time_sec must be a positive integer")
        
        if not isinstance(red_time, int) or red_time <= 0:
            raise ValueError("red_time_sec must be a positive integer")
        
        # Validate impact details
        impact = payload.get("impact", {})
        if not isinstance(impact, dict):
            raise ValueError("impact must be a dictionary")
        
        required_impact_fields = ["original_congestion", "optimized_congestion", "original_category", "optimized_category"]
        DataValidator.validate_required_fields(impact, required_impact_fields)
        
        # Validate congestion values are integers
        if not isinstance(impact.get("original_congestion"), int):
            raise ValueError("original_congestion must be an integer")
        
        if not isinstance(impact.get("optimized_congestion"), int):
            raise ValueError("optimized_congestion must be an integer")
        
        # Validate categories are valid
        valid_categories = ["none", "mild", "severe"]
        if impact.get("original_category") not in valid_categories:
            raise ValueError(f"original_category must be one of {valid_categories}")
        
        if impact.get("optimized_category") not in valid_categories:
            raise ValueError(f"optimized_category must be one of {valid_categories}")

def validate_payload(payload: Dict[str, Any]) -> bool:
    """
    Validates the payload for consistency and completeness.
    
    Args:
        payload: Dictionary containing the data payload
    Returns:
        True if validation passes
    Raises:
        ValueError: If validation fails
    """
    # Validate required base fields
    required_base_fields = ["version", "type", "timestamp"]
    DataValidator.validate_required_fields(payload, required_base_fields)
    
    # Validate version
    DataValidator.validate_version(payload["version"])
    
    # Validate type
    DataValidator.validate_type(payload["type"])
    
    # Validate timestamp
    DataValidator.validate_timestamp(payload["timestamp"])
    
    # Type-specific validations
    data_type = payload["type"]
    
    if data_type == "data":
        DataValidator.validate_data_specific_fields(payload)
    
    elif data_type == "optimization":
        # Validate traffic_light_id for optimization
        if "traffic_light_id" not in payload:
            raise ValueError("Missing required field for optimization type: traffic_light_id")
        DataValidator.validate_traffic_light_id(payload["traffic_light_id"])
        DataValidator.validate_optimization_specific_fields(payload)
    
    elif data_type == "batch-optimization":
        # Validate batch optimization response
        required_batch_opt_fields = ["reference_id", "sensor_count", "optimizations"]
        DataValidator.validate_required_fields(payload, required_batch_opt_fields)
        
        # Validate optimizations list
        optimizations = payload.get("optimizations", [])
        if not isinstance(optimizations, list) or len(optimizations) == 0:
            raise ValueError("optimizations must be a non-empty list")
        
        # Validate each optimization in the batch
        for i, optimization in enumerate(optimizations):
            if not isinstance(optimization, dict):
                raise ValueError(f"optimization at index {i} must be a dictionary")
            
            # Validate each optimization has required fields
            if "traffic_light_id" not in optimization:
                raise ValueError(f"optimization at index {i} missing traffic_light_id")
            if "optimization" not in optimization:
                raise ValueError(f"optimization at index {i} missing optimization details")
            if "impact" not in optimization:
                raise ValueError(f"optimization at index {i} missing impact details")
            
            # Validate traffic_light_id format
            DataValidator.validate_traffic_light_id(optimization["traffic_light_id"])
    
    return True

def validate_data_payload(data: Dict[str, Any]) -> bool:
    """
    Validates a data payload (unified for single and batch).
    
    Args:
        data: Dictionary containing the data payload
    Returns:
        True if validation passes
    Raises:
        ValueError: If validation fails
    """
    return validate_payload(data)

def validate_optimization_response(optimization: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
    """
    Validates optimization response from sync service.
    
    Args:
        optimization: Optimization response (single or list)
    Returns:
        True if validation passes
    Raises:
        ValueError: If validation fails
    """
    if isinstance(optimization, list):
        # Batch optimization response
        if len(optimization) == 0:
            raise ValueError("Optimization response list cannot be empty")
        
        for i, opt in enumerate(optimization):
            try:
                validate_payload(opt)
            except ValueError as e:
                raise ValueError(f"Optimization at index {i} validation failed: {e}") from e
    else:
        # Single optimization response
        validate_payload(optimization)
    
    return True

def validate_sync_service_input(data: Dict[str, Any]) -> bool:
    """
    Validates data before sending to sync service.
    
    Args:
        data: Data to be sent to sync service
    Returns:
        True if validation passes
    Raises:
        ValueError: If validation fails
    """
    # Basic structure validation
    if "type" not in data or data["type"] != "data":
        raise ValueError("Sync service input must have type 'data'")
    
    if "sensors" not in data:
        raise ValueError("Sync service input must have 'sensors' field")
    
    sensors = data.get("sensors", [])
    if not isinstance(sensors, list) or len(sensors) == 0:
        raise ValueError("sensors must be a non-empty list")
    
    if len(sensors) > 10:
        raise ValueError("sensors list cannot exceed 10 items")
    
    # Validate each sensor has required fields for sync service
    for i, sensor in enumerate(sensors):
        required_fields = ["traffic_light_id", "metrics"]
        missing_fields = [field for field in required_fields if field not in sensor]
        if missing_fields:
            raise ValueError(f"sensor at index {i} missing required fields: {missing_fields}")
        
        # Validate metrics structure
        metrics = sensor.get("metrics", {})
        required_metrics = ["vehicles_per_minute", "avg_speed_kmh", "density"]
        missing_metrics = [field for field in required_metrics if field not in metrics]
        if missing_metrics:
            raise ValueError(f"sensor at index {i} missing required metrics: {missing_metrics}")
        
        # Validate metric values are numeric
        for metric in required_metrics:
            value = metrics.get(metric)
            if not isinstance(value, (int, float)):
                raise ValueError(f"sensor at index {i} metric {metric} must be numeric")
    
    return True

def validate_optimization_batch_response(optimization_batch: Dict[str, Any]) -> bool:
    """
    Validates batch optimization response from sync service.
    
    This handles responses with type "optimization" that contain an optimizations array
    (1-10 optimizations) instead of single optimization fields.
    
    Args:
        optimization_batch: Batch optimization response
    Returns:
        True if validation passes
    Raises:
        ValueError: If validation fails
    """
    # Validate required base fields
    required_base_fields = ["version", "type", "timestamp", "traffic_light_id"]
    DataValidator.validate_required_fields(optimization_batch, required_base_fields)
    
    # Validate version
    DataValidator.validate_version(optimization_batch["version"])
    
    # Validate type is "optimization"
    if optimization_batch["type"] != "optimization":
        raise ValueError(f"Expected type 'optimization', got: {optimization_batch['type']}")
    
    # Validate timestamp
    DataValidator.validate_timestamp(optimization_batch["timestamp"])
    
    # Validate traffic_light_id
    DataValidator.validate_traffic_light_id(optimization_batch["traffic_light_id"])
    
    # Check if this is a batch response (has optimizations array)
    if "optimizations" in optimization_batch:
        # Validate optimizations array
        optimizations = optimization_batch.get("optimizations", [])
        if not isinstance(optimizations, list) or len(optimizations) == 0:
            raise ValueError("optimizations must be a non-empty list")
        
        if len(optimizations) > 10:
            raise ValueError("optimizations list cannot exceed 10 items")
        
        # Validate each optimization in the batch
        for i, optimization in enumerate(optimizations):
            if not isinstance(optimization, dict):
                raise ValueError(f"optimization at index {i} must be a dictionary")
            
            # Validate each optimization has required fields
            required_opt_fields = ["version", "type", "timestamp", "traffic_light_id", "optimization", "impact"]
            missing_fields = [field for field in required_opt_fields if field not in optimization]
            if missing_fields:
                raise ValueError(f"optimization at index {i} missing required fields: {missing_fields}")
            
            # Validate traffic_light_id format
            DataValidator.validate_traffic_light_id(optimization["traffic_light_id"])
            
            # Validate optimization details
            opt_details = optimization.get("optimization", {})
            if not isinstance(opt_details, dict):
                raise ValueError(f"optimization at index {i} optimization field must be a dictionary")
            
            required_opt_details = ["green_time_sec", "red_time_sec"]
            missing_opt_details = [field for field in required_opt_details if field not in opt_details]
            if missing_opt_details:
                raise ValueError(f"optimization at index {i} missing optimization details: {missing_opt_details}")
            
            # Validate green and red times are positive integers
            green_time = opt_details.get("green_time_sec")
            red_time = opt_details.get("red_time_sec")
            
            if not isinstance(green_time, int) or green_time <= 0:
                raise ValueError(f"optimization at index {i} green_time_sec must be a positive integer")
            
            if not isinstance(red_time, int) or red_time <= 0:
                raise ValueError(f"optimization at index {i} red_time_sec must be a positive integer")
            
            # Validate impact details
            impact = optimization.get("impact", {})
            if not isinstance(impact, dict):
                raise ValueError(f"optimization at index {i} impact field must be a dictionary")
            
            required_impact_fields = ["original_congestion", "optimized_congestion", "original_category", "optimized_category"]
            missing_impact_fields = [field for field in required_impact_fields if field not in impact]
            if missing_impact_fields:
                raise ValueError(f"optimization at index {i} missing impact details: {missing_impact_fields}")
            
            # Validate congestion values are integers
            if not isinstance(impact.get("original_congestion"), int):
                raise ValueError(f"optimization at index {i} original_congestion must be an integer")
            
            if not isinstance(impact.get("optimized_congestion"), int):
                raise ValueError(f"optimization at index {i} optimized_congestion must be an integer")
            
            # Validate categories are valid
            valid_categories = ["none", "mild", "severe"]
            if impact.get("original_category") not in valid_categories:
                raise ValueError(f"optimization at index {i} original_category must be one of {valid_categories}")
            
            if impact.get("optimized_category") not in valid_categories:
                raise ValueError(f"optimization at index {i} optimized_category must be one of {valid_categories}")
    
    else:
        # Single optimization response - use existing validation
        DataValidator.validate_optimization_specific_fields(optimization_batch)
    
    return True