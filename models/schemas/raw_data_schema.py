"""Schema for raw simulation data from traffic-sim.

Accepts data with minimal validation — no ID normalization,
density in veh/km (not 0-1), partial vehicle_stats allowed.
The DataFormatter service handles all normalization before
passing to the strict TrafficData pipeline.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class RawSensorMetrics(BaseModel):
    """Raw metrics from SUMO — density in veh/km, not normalized."""

    vehicles_per_minute: int = Field(..., ge=0)
    avg_speed_kmh: float = Field(..., ge=0)
    avg_circulation_time_sec: float = Field(..., ge=0)
    density: float = Field(..., ge=0)  # veh/km, may exceed 1.0


class RawSensorData(BaseModel):
    """A single sensor's raw data from SUMO."""

    traffic_light_id: str = Field(..., description="Raw SUMO traffic light ID (e.g. 'J0')")
    controlled_edges: List[str] = Field(..., min_items=1)
    metrics: RawSensorMetrics
    vehicle_stats: Optional[Dict[str, int]] = None  # May be partial or missing


class RawSimulationData(BaseModel):
    """Raw simulation payload from traffic-sim.

    Accepts raw SUMO data without normalization. The /ingest endpoint
    feeds this through DataFormatter to produce a validated TrafficData.
    """

    timestamp: str = Field(..., description="ISO timestamp")
    source_id: str = Field(..., description="Primary traffic light raw SUMO ID")
    sensors: List[RawSensorData] = Field(..., min_items=1, max_items=10)

    @validator("timestamp")
    def validate_timestamp(cls, v):
        try:
            if not re.match(
                r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$",
                v,
            ):
                raise ValueError(
                    "Timestamp must be in strict ISO format (e.g., 2025-05-19T14:20:00Z)"
                )
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            raise ValueError(
                "Timestamp must be in ISO format (e.g., 2025-05-19T14:20:00Z)"
            ) from None
