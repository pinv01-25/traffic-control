"""Transforms raw simulation data into validated TrafficData format.

Centralizes all normalization logic that was previously scattered
across traffic-sim (ID normalization, density conversion, vehicle
stats padding, version assignment).
"""

import logging
import re
from typing import Dict, List, Optional

from models.schemas.data_schema import (
    SensorData,
    TrafficData,
    TrafficMetrics,
    VehicleStats,
)
from models.schemas.raw_data_schema import RawSimulationData

logger = logging.getLogger(__name__)

REQUIRED_VEHICLE_TYPES = ["motorcycle", "car", "bus", "truck"]
DENSITY_DIVISOR = 100.0
MAX_NORMALIZED_DENSITY = 1.0
TARGET_VERSION = "2.0"


class DataFormatter:
    """Transforms raw simulation data into TrafficData format."""

    @staticmethod
    def normalize_traffic_light_id(raw_id: str) -> str:
        """Extract digits from a SUMO traffic light ID.

        Examples: "J0" -> "0", "GS_cluster_J0_J1" -> "0", "42" -> "42"
        """
        match = re.search(r"(\d+)", str(raw_id))
        if match:
            return match.group(1)
        logger.warning(f"Could not extract digits from ID '{raw_id}', using as-is")
        return raw_id

    @staticmethod
    def normalize_density(raw_density_veh_km: float) -> float:
        """Convert density from veh/km to 0-1 normalized scale.

        Values already in 0-1 range are returned as-is.
        100 veh/km -> 1.0, 50 veh/km -> 0.5, values > 100 -> capped at 1.0.
        """
        if raw_density_veh_km <= MAX_NORMALIZED_DENSITY:
            return round(raw_density_veh_km, 3)
        normalized = min(raw_density_veh_km / DENSITY_DIVISOR, MAX_NORMALIZED_DENSITY)
        return round(normalized, 3)

    @staticmethod
    def ensure_vehicle_stats(
        raw_stats: Optional[Dict[str, int]],
        fallback_vehicle_count: int = 0,
    ) -> Dict[str, int]:
        """Ensure vehicle_stats has all 4 required keys.

        If raw_stats is None or empty, assigns all vehicles as 'car'.
        Otherwise fills missing keys with 0.
        """
        if not raw_stats:
            return {
                "motorcycle": 0,
                "car": fallback_vehicle_count,
                "bus": 0,
                "truck": 0,
            }
        return {vtype: raw_stats.get(vtype, 0) for vtype in REQUIRED_VEHICLE_TYPES}

    @classmethod
    def format_raw_to_traffic_data(cls, raw: RawSimulationData) -> TrafficData:
        """Transform a RawSimulationData into a validated TrafficData.

        Applies all normalizations:
        - traffic_light_id: extract digits only
        - density: veh/km -> 0-1 scale
        - vehicle_stats: ensure 4 required keys
        - version: set to TARGET_VERSION
        """
        normalized_source_id = cls.normalize_traffic_light_id(raw.source_id)

        sensors: List[SensorData] = []
        for raw_sensor in raw.sensors:
            norm_id = cls.normalize_traffic_light_id(raw_sensor.traffic_light_id)
            norm_density = cls.normalize_density(raw_sensor.metrics.density)
            vehicle_stats = cls.ensure_vehicle_stats(
                raw_sensor.vehicle_stats,
                fallback_vehicle_count=raw_sensor.metrics.vehicles_per_minute,
            )

            sensors.append(
                SensorData(
                    traffic_light_id=norm_id,
                    controlled_edges=raw_sensor.controlled_edges,
                    metrics=TrafficMetrics(
                        vehicles_per_minute=raw_sensor.metrics.vehicles_per_minute,
                        avg_speed_kmh=min(raw_sensor.metrics.avg_speed_kmh, 200.0),
                        avg_circulation_time_sec=raw_sensor.metrics.avg_circulation_time_sec,
                        density=norm_density,
                    ),
                    vehicle_stats=VehicleStats(**vehicle_stats),
                )
            )

        traffic_data = TrafficData(
            version=TARGET_VERSION,
            type="data",
            timestamp=raw.timestamp,
            traffic_light_id=normalized_source_id,
            sensors=sensors,
        )

        logger.info(
            f"Formatted raw data: source '{raw.source_id}' -> "
            f"traffic_light_id '{normalized_source_id}', "
            f"{len(sensors)} sensors"
        )

        return traffic_data
