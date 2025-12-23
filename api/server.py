import logging

from database.db import init_db
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.response_models import HealthCheckResponse, ResponseFactory
from models.schemas import TrafficData
from services.database_service import DatabaseService
from services.process_service import ProcessService
from utils.error_handler import error_handler_decorator


# ANSI color codes for consistent logging
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("traffic_control")

app = FastAPI(title="Traffic Control Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Traffic Control Service is running"}

@app.get("/healthcheck", response_model=HealthCheckResponse)
def health_check():
    return HealthCheckResponse()

@app.on_event("startup")
async def startup_event():
    init_db()

@app.post("/process")
@error_handler_decorator("data processing")
def process(data: TrafficData):
    """Process traffic data - handles both single sensors and batches (1-10 sensors)."""
    logger.info("Starting unified process endpoint...")
    
    # Check if this is batch data or single sensor data
    if data.is_batch():
        # Batch data
        logger.info(f"Processing batch with {len(data.sensors)} sensors")
        return ProcessService.process_data_batch(data)
    elif data.is_single_sensor():
        # Single sensor data - convert to batch format for processing
        logger.info(f"Processing single sensor for traffic light {data.traffic_light_id}")
        batch_data = data.to_batch_format()
        return ProcessService.process_data_batch(batch_data)
    else:
        raise HTTPException(
            status_code=400, 
            detail="Invalid data format. Must be either batch (with sensors) or single sensor (with direct fields)."
        )

# New metadata endpoints
@app.get("/metadata/traffic-light/{traffic_light_id}")
@error_handler_decorator("get metadata by traffic light")
def get_metadata_by_traffic_light(traffic_light_id: str, limit: int = 100):
    """Get metadata entries for a specific traffic light."""
    entries = DatabaseService.get_metadata_by_traffic_light(traffic_light_id, limit)
    return ResponseFactory.metadata_response(entries, limit)

@app.get("/metadata/type/{data_type}")
@error_handler_decorator("get metadata by type")
def get_metadata_by_type(data_type: str, limit: int = 100):
    """Get metadata entries by data type."""
    entries = DatabaseService.get_metadata_by_type(data_type, limit)
    return ResponseFactory.metadata_response(entries, limit)

@app.get("/metadata/recent")
@error_handler_decorator("get recent metadata")
def get_recent_metadata(limit: int = 50):
    """Get recent metadata entries."""
    entries = DatabaseService.get_recent_metadata(limit)
    return ResponseFactory.metadata_response(entries, limit)

@app.get("/metadata/stats")
@error_handler_decorator("get metadata stats")
def get_metadata_stats():
    """Get metadata statistics."""
    stats = DatabaseService.get_metadata_stats()
    return ResponseFactory.metadata_stats_response(stats)

@app.delete("/metadata/traffic-light/{traffic_light_id}")
@error_handler_decorator("delete metadata by traffic light")
def delete_metadata_by_traffic_light(traffic_light_id: str):
    """Delete all metadata entries for a specific traffic light."""
    deleted_count = DatabaseService.delete_metadata_by_traffic_light(traffic_light_id)
    return ResponseFactory.deletion_success(deleted_count, traffic_light_id)
