from fastapi import APIRouter, HTTPException
from models.validator import validate_payload
from models.schemas import TrafficData, OptimizationData, DownloadRequest
from services.storage_proxy import upload_to_storage, download_from_storage
from services.sync_proxy import send_to_sync
from database.db import SessionLocal
from database.metadata_model import MetadataIndex
from utils.time import iso_to_unix

router = APIRouter()

@router.post("/process")
def process(data: TrafficData):
    print("Starting process endpoint...")
    
    # Validate the incoming data
    try:
        validate_payload(data.dict())
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    
    # Convert ISO timestamp to Unix timestamp for local database
    unix_timestamp = iso_to_unix(data.timestamp)
    
    # Upload to storage
    try:
        print("Uploading data to storage...")
        # No need for special payload, upload_to_storage will handle conversion
        upload_response = upload_to_storage(data.dict())
        print("Upload successful:", upload_response)
    except Exception as e:
        print("Upload to storage failed:", str(e))
        raise HTTPException(status_code=500, detail=f"Upload to storage failed: {str(e)}")
    
    # Register metadata locally
    db = SessionLocal()
    try:
        print("Registering metadata locally...")
        entry = MetadataIndex(
            type=data.type,
            timestamp=unix_timestamp,
            traffic_light_id=data.traffic_light_id
        )
        db.add(entry)
        db.commit()
        print("Metadata registered successfully.")
    finally:
        db.close()
    
    # Download same data - use original timestamp format for consistency
    request = DownloadRequest(
        traffic_light_id=data.traffic_light_id,
        timestamp=data.timestamp,
        type=data.type
    )
    
    try:
        print("Downloading data from storage...")
        fetched_data = download_from_storage(request)
        print("Download successful:", fetched_data)
    except Exception as e:
        print("Download failed:", str(e))
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
    
    # Optimize using sync
    try:
        print("Sending data for optimization...")
        optimized = send_to_sync(fetched_data)
        print("Optimization successful:", optimized)
    except Exception as e:
        print("Sync optimization failed:", str(e))
        raise HTTPException(status_code=500, detail=f"Sync optimization failed: {str(e)}")
    
        # Validate the incoming data
    try:
        validate_payload(optimized.dict())
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    
    # Upload optimized data
    try:
        print("Uploading optimized data to storage...")
        # No need to manually convert timestamp, upload_to_storage will handle it
        upload_to_storage(optimized)
        print("Optimized data upload successful.")
    except Exception as e:
        print("Optimized upload failed:", str(e))
        raise HTTPException(status_code=500, detail=f"Optimized upload failed: {str(e)}")
    
    # Register optimization locally
    db = SessionLocal()
    try:
        print("Registering optimization metadata locally...")
        opt_unix_timestamp = iso_to_unix(optimized["timestamp"])
        opt_entry = MetadataIndex(
            type="optimization",
            timestamp=opt_unix_timestamp,
            traffic_light_id=optimized["traffic_light_id"]
        )
        db.add(opt_entry)
        db.commit()
        print("Optimization metadata registered successfully.")
    finally:
        db.close()
    
    print("Process completed successfully.")
    return {"status": "success", "message": "Data processed and optimized successfully"}