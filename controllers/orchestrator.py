from fastapi import APIRouter, HTTPException
from models.validator import validate_payload
from models.schemas import TrafficData, OptimizationData, DownloadRequest
from services.storage_proxy import upload_to_storage, download_from_storage
from services.sync_proxy import send_to_sync
from database.db import SessionLocal
from database.metadata_model import MetadataIndex
from utils.time import iso_to_unix
import logging
import json

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("process_endpoint")

router = APIRouter()

@router.post("/process")
def process(data: TrafficData):
    logger.info("Starting process endpoint...")
    
    # Validate the incoming data
    try:
        validate_payload(data.dict())
        logger.info("Payload validation successful.")
    except ValueError as ve:
        logger.error(f"Payload validation failed: {ve}")
        raise HTTPException(status_code=422, detail=str(ve))
    
    # Convert ISO timestamp to Unix timestamp for local database
    unix_timestamp = iso_to_unix(data.timestamp)
    
    # Upload to storage
    try:
        logger.info("Uploading data to storage...")
        # No need for special payload, upload_to_storage will handle conversion
        upload_response = upload_to_storage(data.dict())
        logger.info("Upload successful:", upload_response)
    except Exception as e:
        logger.error(f"Upload to storage failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload to storage failed: {str(e)}")
    
    # Register metadata locally
    db = SessionLocal()
    try:
        logger.info("Registering metadata locally...")
        entry = MetadataIndex(
            type=data.type,
            timestamp=unix_timestamp,
            traffic_light_id=data.traffic_light_id
        )
        db.add(entry)
        db.commit()
        logger.info("Metadata registered successfully.")
    finally:
        db.close()
    
    # Download same data - use original timestamp format for consistency
    request = DownloadRequest(
        traffic_light_id=data.traffic_light_id,
        timestamp=data.timestamp,
        type=data.type
    )
    
    try:
        logger.info("Downloading data from storage...")
        fetched_data = download_from_storage(request)
        logger.info("Download successful:", fetched_data)
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
    
    # Optimize using sync
    try:
        logger.info("Sending data for optimization...")
        logger.info(f"Payload to /evaluate: {json.dumps(fetched_data, indent=2)}")
        optimized = send_to_sync(fetched_data)

        logger.info(f"Optimization successful: {json.dumps(optimized, indent=2)}")
    except Exception as e:
        logger.error(f"Sync optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync optimization failed: {str(e)}")
    
        # Validate the incoming data
    try:
        logger.info("Validating optimized payload...")
        validate_payload(optimized)
        logger.info("Optimized payload validation successful.")
    except ValueError as ve:
        logger.error(f"Optimized payload validation failed: {ve}")
        raise HTTPException(status_code=422, detail=str(ve))
    
    # Upload optimized data
    try:
        logger.info("Uploading optimized data to storage...")
        # No need to manually convert timestamp, upload_to_storage will handle it
        upload_to_storage(optimized)
        logger.info("Optimized data upload successful.")
    except Exception as e:
        logger.error(f"Optimized upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Optimized upload failed: {str(e)}")
    
    # Register optimization locally
    db = SessionLocal()
    try:
        logger.info("Registering optimization metadata locally...")
        opt_unix_timestamp = iso_to_unix(optimized["timestamp"])
        opt_entry = MetadataIndex(
            type="optimization",
            timestamp=opt_unix_timestamp,
            traffic_light_id=optimized["traffic_light_id"]
        )
        db.add(opt_entry)
        db.commit()
        logger.info("Optimization metadata registered successfully.")
    finally:
        db.close()
    
    logger.info("Process completed successfully.")
    return {"status": "success", "message": "Data processed and optimized successfully"}