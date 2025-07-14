from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model for all API endpoints."""
    status: str
    message: str
    timestamp: datetime = datetime.now()

class SuccessResponse(BaseResponse):
    """Standard success response."""
    status: str = "success"

class ErrorResponse(BaseResponse):
    """Standard error response."""
    status: str = "error"
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ProcessingResponse(SuccessResponse):
    """Response for data processing operations."""
    data_type: str
    traffic_light_id: str
    timestamp: Union[str, int]

class BatchProcessingResponse(ProcessingResponse):
    """Response for batch processing operations."""
    sensor_count: int
    reference_sensor: str

class ZoneOptimizationResponse(ProcessingResponse):
    """Response for zone optimization operations."""
    zone_sensors: List[str]
    optimization_type: str = "zone"

class MetadataEntry(BaseModel):
    """Model for metadata entries."""
    id: int
    type: str
    timestamp: int
    traffic_light_id: str
    created_at: Optional[str] = None

class MetadataResponse(SuccessResponse):
    """Response for metadata operations."""
    data: List[MetadataEntry]
    count: int
    limit: int

class MetadataStatsResponse(SuccessResponse):
    """Response for metadata statistics."""
    stats: Dict[str, int]

class DeletionResponse(SuccessResponse):
    """Response for deletion operations."""
    deleted_count: int
    traffic_light_id: str

class HealthCheckResponse(BaseModel):
    """Response for health check endpoint."""
    status: str = "healthy"
    service: str = "traffic-control"
    timestamp: datetime = datetime.now()
    version: str = "2.0"

class ResponseFactory:
    """Factory for creating standardized API responses."""
    
    @staticmethod
    def success(message: str, **kwargs) -> Dict[str, Any]:
        """Create a success response."""
        return {
            "status": "success",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
    
    @staticmethod
    def error(message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create an error response."""
        response = {
            "status": "error",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        if error_code:
            response["error_code"] = error_code
        if details:
            response["details"] = details
        return response
    
    @staticmethod
    def processing_success(data_type: str, traffic_light_id: str, timestamp: Union[str, int], **kwargs) -> Dict[str, Any]:
        """Create a processing success response."""
        return ResponseFactory.success(
            "Data processed and optimized successfully",
            data_type=data_type,
            traffic_light_id=traffic_light_id,
            timestamp=timestamp,
            **kwargs
        )
    
    @staticmethod
    def batch_processing_success(sensor_count: int, reference_sensor: str, **kwargs) -> Dict[str, Any]:
        """Create a batch processing success response."""
        return ProcessingResponse(
            data_type="data",  # Changed from "data-batch" to "data"
            traffic_light_id=reference_sensor,
            timestamp=datetime.now().isoformat(),
            message=f"Successfully processed batch with {sensor_count} sensors",
            **kwargs
        ).dict()
    
    @staticmethod
    def zone_optimization_success(zone_sensors: List[str], **kwargs) -> Dict[str, Any]:
        """Create a zone optimization success response."""
        return ResponseFactory.processing_success(
            data_type="optimization",
            traffic_light_id=zone_sensors[0] if zone_sensors else "unknown",
            timestamp=datetime.now().isoformat(),
            zone_sensors=zone_sensors,
            optimization_type="zone",
            **kwargs
        )
    
    @staticmethod
    def metadata_response(entries: List[Dict[str, Any]], limit: int) -> Dict[str, Any]:
        """Create a metadata response."""
        return ResponseFactory.success(
            "Metadata retrieved successfully",
            data=entries,
            count=len(entries),
            limit=limit
        )
    
    @staticmethod
    def metadata_stats_response(stats: Dict[str, int]) -> Dict[str, Any]:
        """Create a metadata statistics response."""
        return ResponseFactory.success(
            "Metadata statistics retrieved successfully",
            stats=stats
        )
    
    @staticmethod
    def deletion_success(deleted_count: int, traffic_light_id: str) -> Dict[str, Any]:
        """Create a deletion success response."""
        return ResponseFactory.success(
            f"Deleted {deleted_count} metadata entries",
            deleted_count=deleted_count,
            traffic_light_id=traffic_light_id
        ) 