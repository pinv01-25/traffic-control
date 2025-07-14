from datetime import datetime, timezone
from typing import Union
import re

class TimestampValidator:
    """Utility class for timestamp validation and conversion."""
    
    @staticmethod
    def validate_iso_timestamp(timestamp_str: str) -> bool:
        """
        Validates if a string is a valid ISO timestamp.
        
        Args:
            timestamp_str: Input timestamp string (ISO format)
        Returns:
            True if valid, False otherwise
        """
        try:
            # Handle 'Z' timezone indicator
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str.replace('Z', '+00:00')
            
            # Try to parse as ISO format
            datetime.fromisoformat(timestamp_str)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_unix_timestamp(timestamp: Union[int, str]) -> bool:
        """
        Validates if a value is a reasonable Unix timestamp.
        
        Args:
            timestamp: Unix timestamp (seconds since epoch)
        Returns:
            True if valid, False otherwise
        """
        try:
            if isinstance(timestamp, str):
                timestamp = int(timestamp)
            
            # Ensure it's reasonable (after year 2000 and before year 2100)
            return 946684800 <= timestamp <= 4102444800
        except (ValueError, TypeError):
            return False

def iso_to_unix(timestamp_str: str) -> int:
    """
    Converts ISO timestamp string to Unix timestamp.
    
    Args:
        timestamp_str: Input timestamp string (ISO format)
    Returns:
        Unix timestamp (seconds since epoch)
    Raises:
        ValueError: If timestamp format is invalid
    """
    if not TimestampValidator.validate_iso_timestamp(timestamp_str):
        raise ValueError(f"Invalid ISO timestamp format: {timestamp_str}")
    
    # Handle 'Z' timezone indicator
    if timestamp_str.endswith('Z'):
        timestamp_str = timestamp_str.replace('Z', '+00:00')
    
    # Convert to datetime and then to unix timestamp
    dt = datetime.fromisoformat(timestamp_str)
    return int(dt.timestamp())

def unix_to_iso(unix_timestamp: Union[int, str]) -> str:
    """
    Converts Unix timestamp to ISO timestamp string.
    
    Args:
        unix_timestamp: Unix timestamp (seconds since epoch)
    Returns:
        ISO timestamp string
    Raises:
        ValueError: If timestamp is invalid
    """
    try:
        if isinstance(unix_timestamp, str):
            # Check if it's already an ISO format string
            if TimestampValidator.validate_iso_timestamp(unix_timestamp):
                return unix_timestamp
            unix_timestamp = int(unix_timestamp)
        
        if not TimestampValidator.validate_unix_timestamp(unix_timestamp):
            raise ValueError(f"Invalid Unix timestamp: {unix_timestamp}")
        
        # Convert Unix timestamp to ISO format with UTC timezone
        dt = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
        return dt.isoformat().replace('+00:00', 'Z')
    except (ValueError, TypeError) as e:
        raise ValueError(f"Failed to convert timestamp: {e}")

def normalize_timestamp(timestamp: Union[str, int]) -> tuple[str, int]:
    """
    Normalizes a timestamp to both ISO and Unix formats.
    
    Args:
        timestamp: Timestamp in either ISO string or Unix int format
    Returns:
        Tuple of (iso_string, unix_int)
    """
    if isinstance(timestamp, str):
        if TimestampValidator.validate_iso_timestamp(timestamp):
            unix_ts = iso_to_unix(timestamp)
            return timestamp, unix_ts
        else:
            raise ValueError(f"Invalid timestamp format: {timestamp}")
    elif isinstance(timestamp, int):
        if TimestampValidator.validate_unix_timestamp(timestamp):
            iso_str = unix_to_iso(timestamp)
            return iso_str, timestamp
        else:
            raise ValueError(f"Invalid Unix timestamp: {timestamp}")
    else:
        raise ValueError(f"Unsupported timestamp type: {type(timestamp)}")