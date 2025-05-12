from datetime import datetime

def iso_to_unix(timestamp_str: str) -> int:
    """
    Strips timezone suffix '-03' if present and converts to Unix timestamp.
    
    Args:
        timestamp_str: Input timestamp string (ISO format)
    Returns:
        Unix timestamp (seconds since epoch)
    """
    # Strip timezone if present
    if timestamp_str.endswith("-03"):
        timestamp_str = timestamp_str[:-3]
    
    # Convert to datetime and then to unix timestamp
    dt = datetime.fromisoformat(timestamp_str)
    return int(dt.timestamp())

def unix_to_iso(unix_timestamp: int) -> str:
    """Convert Unix timestamp to ISO timestamp string."""
    if isinstance(unix_timestamp, str):
        # Check if it's already an ISO format string
        try:
            datetime.fromisoformat(unix_timestamp.replace('Z', '+00:00'))
            return unix_timestamp
        except ValueError:
            pass
    
    # Convert Unix timestamp to ISO format
    dt = datetime.fromtimestamp(unix_timestamp)
    return dt.isoformat()