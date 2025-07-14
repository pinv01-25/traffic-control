import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings and configuration."""
    
    # API URLs
    STORAGE_API_URL: str = os.getenv("STORAGE_API_URL", "http://localhost:8000")
    SYNC_API_URL: str = os.getenv("SYNC_API_URL", "http://localhost:8002")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./traffic_control.db")
    
    # Validation settings
    MAX_SENSORS_PER_BATCH: int = int(os.getenv("MAX_SENSORS_PER_BATCH", "10"))
    MIN_SENSORS_PER_BATCH: int = int(os.getenv("MIN_SENSORS_PER_BATCH", "1"))
    
    # Timestamp validation
    MIN_TIMESTAMP: int = int(os.getenv("MIN_TIMESTAMP", "946684800"))  # 2000-01-01
    MAX_TIMESTAMP: int = int(os.getenv("MAX_TIMESTAMP", "4102444800"))  # 2100-01-01
    
    # Traffic light ID pattern
    TRAFFIC_LIGHT_ID_PATTERN: str = r'^\d+$'
    
    # Allowed data types
    ALLOWED_DATA_TYPES: List[str] = ["data", "optimization"]
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

# Global settings instance
settings = Settings() 