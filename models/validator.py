import re
from datetime import datetime
from typing import Dict, Any

def validate_payload(payload: Dict[str, Any]) -> bool:
    """
    Validates the payload for consistency and completeness.
    Raises ValueError if validation fails.
    Returns True if validation passes.
    """
    required_fields = ["version", "type", "timestamp", "traffic_light_id"]
    
    # Check required fields
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate timestamp format - accept both ISO string and Unix integer
    timestamp = payload["timestamp"]
    if isinstance(timestamp, str):
        try:
            # Try to parse as ISO format
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Invalid timestamp format: {timestamp}. Expected ISO format.")
    elif isinstance(timestamp, int):
        # Unix timestamp - ensure it's reasonable (after year 2000 and before year 2100)
        if timestamp < 946684800 or timestamp > 4102444800:
            raise ValueError(f"Unix timestamp out of reasonable range: {timestamp}")
    else:
        raise ValueError(f"Invalid timestamp type: {type(timestamp)}. Expected string or int.")
    
    # Validate version format (semantic versioning)
    version = payload["version"]
    if not re.match(r"^\d+(\.\d+)*$", version):
        raise ValueError(f"Invalid version format: {version}. Expected semantic versioning.")
    
    # Validate type
    allowed_types = ["data", "optimization"]
    if payload["type"] not in allowed_types:
        raise ValueError(f"Invalid type value: {payload['type']}. Expected one of {allowed_types}")
    
    # Type-specific validations
    if payload["type"] == "data":
        # Validate data-specific fields
        if "metrics" not in payload:
            raise ValueError("Missing required field for data type: metrics")
        if "controlled_edges" not in payload:
            raise ValueError("Missing required field for data type: controlled_edges")
        if "vehicle_stats" not in payload:
            raise ValueError("Missing required field for data type: vehicle_stats")
    
    elif payload["type"] == "optimization":
        # Validate optimization-specific fields
        if "optimization" not in payload:
            raise ValueError("Missing required field for optimization type: optimization")
        if "impact" not in payload:
            raise ValueError("Missing required field for optimization type: impact")
    
    return True