from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any
from datetime import datetime
import re

class TrafficMetrics(BaseModel):
    vehicles_per_minute: int = Field(..., ge=0, description="Number of vehicles per minute")
    avg_speed_kmh: float = Field(..., ge=0, le=200, description="Average speed in km/h")
    avg_circulation_time_sec: float = Field(..., ge=0, description="Average circulation time in seconds")
    density: float = Field(..., ge=0, le=1, description="Traffic density (0-1)")

class VehicleStats(BaseModel):
    motorcycle: int = Field(..., ge=0, description="Number of motorcycles")
    car: int = Field(..., ge=0, description="Number of cars")
    bus: int = Field(..., ge=0, description="Number of buses")
    truck: int = Field(..., ge=0, description="Number of trucks")

class SensorData(BaseModel):
    traffic_light_id: str = Field(..., description="Unique identifier for the traffic light")
    controlled_edges: List[str] = Field(..., min_items=1, description="List of controlled edges")
    metrics: TrafficMetrics
    vehicle_stats: VehicleStats

    @validator('traffic_light_id')
    def validate_traffic_light_id(cls, v):
        if not re.match(r'^\d+$', v):
            raise ValueError('traffic_light_id must contain only numbers')
        return v

class TrafficData(BaseModel):
    """Unified data model that handles both single sensors and batches"""
    version: str = Field(..., description="Version of the data format")
    type: str = Field(default="data", description="Type of data (always 'data' for both single and batch)")
    timestamp: str = Field(..., description="ISO timestamp of the data collection")
    traffic_light_id: str = Field(..., description="Traffic light ID")
    sensors: List[SensorData] = Field(None, min_items=1, max_items=10, description="List of sensor data (1-10 sensors)")
    
    # Legacy single sensor fields (optional)
    controlled_edges: List[str] = Field(None, min_items=1, description="List of controlled edges (legacy)")
    metrics: TrafficMetrics = Field(None, description="Traffic metrics (legacy)")
    vehicle_stats: VehicleStats = Field(None, description="Vehicle statistics (legacy)")

    @validator('version')
    def validate_version(cls, v):
        if not re.match(r'^\d+(\.\d+)*$', v):
            raise ValueError('Version must follow semantic versioning format')
        return v

    @validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            # Try to parse as ISO format with timezone
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('Timestamp must be in ISO format (e.g., 2025-05-19T14:20:00Z)')

    @validator('traffic_light_id')
    def validate_traffic_light_id(cls, v):
        if not re.match(r'^\d+$', v):
            raise ValueError('traffic_light_id must contain only numbers')
        return v

    @validator('sensors')
    def validate_sensors_reference_id(cls, v, values):
        if v and 'traffic_light_id' in values:
            reference_id = values['traffic_light_id']
            sensor_ids = [sensor.traffic_light_id for sensor in v]
            if reference_id not in sensor_ids:
                raise ValueError(f'traffic_light_id {reference_id} must be present in sensors list')
        return v

    def is_batch(self) -> bool:
        """Check if this is batch data (has sensors field)."""
        return self.sensors is not None and len(self.sensors) > 0

    def is_single_sensor(self) -> bool:
        """Check if this is single sensor data (has legacy fields)."""
        return (self.controlled_edges is not None and 
                self.metrics is not None and 
                self.vehicle_stats is not None)

    def to_batch_format(self) -> 'TrafficData':
        """Convert single sensor format to batch format."""
        if self.is_batch():
            return self
        
        if not self.is_single_sensor():
            raise ValueError("Data must be either batch or single sensor format")
        
        # Create batch format from single sensor
        return TrafficData(
            version=self.version,
            type=self.type,
            timestamp=self.timestamp,
            traffic_light_id=self.traffic_light_id,
            sensors=[SensorData(
                traffic_light_id=self.traffic_light_id,
                controlled_edges=self.controlled_edges,
                metrics=self.metrics,
                vehicle_stats=self.vehicle_stats
            )]
        )

    @classmethod
    def from_single_sensor(cls, sensor_data: dict) -> 'TrafficData':
        """Create TrafficData from a single sensor (legacy format)"""
        return cls(
            version="2.0",
            type="data",
            timestamp=sensor_data["timestamp"],
            traffic_light_id=sensor_data["traffic_light_id"],
            controlled_edges=sensor_data["controlled_edges"],
            metrics=sensor_data["metrics"],
            vehicle_stats=sensor_data["vehicle_stats"]
        )
