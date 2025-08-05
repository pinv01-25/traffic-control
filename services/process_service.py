import json
import time
from typing import Dict, Any, Optional, List, Union
from models.validator import validate_payload, validate_optimization_response, validate_sync_service_input, validate_optimization_batch_response
from models.schemas import TrafficData
from models.response_models import ResponseFactory
from services.storage_proxy import StorageProxy
from services.sync_proxy import SyncProxy
from services.data_processor import DataProcessor
from services.database_service import DatabaseService
from utils.time import iso_to_unix
import logging
import json

logger = logging.getLogger(__name__)

class ProcessService:
    """Service for handling traffic data processing business logic."""
    
    @staticmethod
    def process_single_sensor(data: TrafficData) -> Dict[str, Any]:
        """
        Process a single sensor's traffic data through the complete pipeline.
        
        Args:
            data: Single sensor traffic data (unified format)
        Returns:
            Processing result
        """
        logger.info(f"Processing single sensor data for traffic light {data.traffic_light_id}")
        
        # Validate incoming data
        ProcessService._validate_incoming_data(data.dict())
        
        # Convert timestamp
        unix_timestamp = iso_to_unix(data.timestamp)
        
        # Upload to storage
        upload_response = ProcessService._upload_to_storage(data.dict())
        
        # Register metadata locally
        DatabaseService.register_metadata(data.type, unix_timestamp, data.traffic_light_id)
        
        # Download data for optimization
        fetched_data = ProcessService._download_for_optimization(data)
        
        # Optimize using sync
        optimized = ProcessService._optimize_data(fetched_data)
        
        # Validate optimized data
        ProcessService._validate_optimized_data(optimized)
        
        # Upload optimized data
        ProcessService._upload_optimized_data(optimized)
        
        # Register optimization metadata
        DatabaseService.register_optimization_metadata(optimized)
        
        logger.info("Single sensor processing completed successfully")
        return ResponseFactory.processing_success()
    
    @staticmethod
    def process_data_batch(batch_data: TrafficData) -> Dict[str, Any]:
        """
        Process a batch of sensor data through the complete pipeline.
        
        Args:
            batch_data: Batch of sensor data (unified format)
        Returns:
            Processing result
        """
        logger.info(f"Processing batch data with {len(batch_data.sensors)} sensors")
        
        # Process and validate batch
        processed_batch = DataProcessor.process_data_batch(batch_data.dict())
        
        # Upload batch to storage
        upload_metadata = ProcessService._upload_batch_to_storage(processed_batch)
        
        # Register metadata locally
        DatabaseService.register_metadata(
            upload_metadata["type"],
            upload_metadata["timestamp"],
            upload_metadata["traffic_light_id"]
        )
        
        # Download batch for optimization
        fetched_batch = ProcessService._download_batch_for_optimization(processed_batch)
        
        # Optimize batch using sync service
        optimized = ProcessService._optimize_batch(fetched_batch, batch_data.traffic_light_id)
        
        # Validate optimized data
        ProcessService._validate_optimized_data(optimized)
        
        # Upload optimized data
        ProcessService._upload_optimized_data(optimized)
        
        # Register optimization metadata
        DatabaseService.register_optimization_metadata(optimized)
        
        logger.info("Batch processing completed successfully")
        return ResponseFactory.processing_success(
            data_type=batch_data.type,
            traffic_light_id=batch_data.traffic_light_id,
            timestamp=batch_data.timestamp
        )
    
    # Private helper methods
    @staticmethod
    def _validate_incoming_data(data: Dict[str, Any]) -> None:
        """Validate incoming data."""
        try:
            validate_payload(data)
            logger.info("Payload validation successful.")
        except ValueError as e:
            logger.error(f"Payload validation failed: {e}")
            raise
    
    @staticmethod
    def _upload_to_storage(data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload data to storage."""
        try:
            logger.info("Uploading data to storage...")
            response = StorageProxy.upload_to_storage(data)
            logger.info("Upload successful:", response)
            return response
        except Exception as e:
            logger.error(f"Upload to storage failed: {e}")
            raise
    
    @staticmethod
    def _download_for_optimization(data: TrafficData) -> Dict[str, Any]:
        """Download data for optimization."""
        try:
            logger.info("Downloading data from storage...")
            from models.schemas import DownloadRequest
            request = DownloadRequest(
                traffic_light_id=data.traffic_light_id,
                timestamp=data.timestamp,
                type=data.type
            )
            fetched_data = StorageProxy.download_from_storage(request)
            logger.info("Download successful:", fetched_data)
            return fetched_data
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise
    
    @staticmethod
    def _optimize_data(data: Dict[str, Any]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Optimize data using sync service."""
        try:
            logger.info("Sending data for optimization...")
            
            # Validate data before sending to sync service
            validate_sync_service_input(data)
            
            logger.info(f"Payload to /evaluate: {json.dumps(data, indent=2)}")
            optimized = SyncProxy.send_to_sync(data)
            logger.info(f"Optimization successful: {json.dumps(optimized, indent=2)}")
            return optimized
        except Exception as e:
            logger.error(f"Sync optimization failed: {e}")
            raise
    
    @staticmethod
    def _validate_optimized_data(optimized: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """Validate optimized data."""
        try:
            logger.info("Validating optimized payload...")
            validate_optimization_batch_response(optimized)
            logger.info("Optimized data validation successful.")
        except ValueError as ve:
            logger.error(f"Optimized payload validation failed: {ve}")
            raise
    
    @staticmethod
    def _upload_optimized_data(optimized: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """Upload optimized data to storage."""
        try:
            logger.info("Uploading optimized data to storage...")
            
            # Check if this is a list of optimizations (batch result)
            if isinstance(optimized, list):
                logger.info(f"Processing list of {len(optimized)} optimizations...")
                
                # Always create optimization batch format for storage
                reference_optimization = optimized[0]
                optimization_batch = {
                    "version": reference_optimization["version"],
                    "type": "optimization",
                    "timestamp": reference_optimization["timestamp"],
                    "traffic_light_id": reference_optimization["traffic_light_id"],
                    "optimizations": optimized
                }
                
                logger.info(f"Uploading optimization batch with {len(optimized)} optimizations")
                StorageProxy.upload_to_storage(optimization_batch)
                logger.info(f"Successfully uploaded optimization batch to storage")
            else:
                # Single optimization - create batch format with single item
                optimization_batch = {
                    "version": optimized["version"],
                    "type": "optimization",
                    "timestamp": optimized["timestamp"],
                    "traffic_light_id": optimized["traffic_light_id"],
                    "optimizations": [optimized]
                }
                
                logger.info("Uploading single optimization as batch format")
                StorageProxy.upload_to_storage(optimization_batch)
                logger.info("Single optimization upload successful.")
                
        except Exception as e:
            logger.error(f"Optimized upload failed: {e}")
            raise
    
    @staticmethod
    def _upload_batch_to_storage(processed_batch: Dict[str, Any]) -> Dict[str, Any]:
        """Upload batch data to storage."""
        try:
            logger.info("Uploading batch data to storage...")
            response = StorageProxy.upload_data_batch(processed_batch)
            logger.info("Batch upload successful:", response)
            
            # Return metadata for database registration
            metadata = {
                "type": processed_batch["type"],
                "timestamp": processed_batch["_unix_timestamp"],
                "traffic_light_id": processed_batch["traffic_light_id"]
            }
            return metadata
        except Exception as e:
            logger.error(f"Batch upload to storage failed: {e}")
            raise
    
    @staticmethod
    def _download_batch_for_optimization(processed_batch: Dict[str, Any]) -> Dict[str, Any]:
        """Download batch data for optimization."""
        try:
            logger.info("Downloading batch data from storage...")
            fetched_batch = StorageProxy.download_data_batch(
                processed_batch["traffic_light_id"],
                processed_batch["timestamp"]
            )
            logger.info("Batch download successful:", fetched_batch)
            return fetched_batch
        except Exception as e:
            logger.error(f"Batch download failed: {e}")
            raise
    
    @staticmethod
    def _optimize_batch(fetched_batch: Dict[str, Any], reference_sensor_id: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Optimize batch data."""
        try:
            logger.info("Sending batch data for optimization...")
            
            # Validate data before sending to sync service
            validate_sync_service_input(fetched_batch)
            
            optimized = SyncProxy.send_batch_for_optimization(fetched_batch, reference_sensor_id)
            logger.info(f"Batch optimization successful: {json.dumps(optimized, indent=2)}")
            return optimized
        except Exception as e:
            logger.error(f"Batch sync optimization failed: {e}")
            raise 