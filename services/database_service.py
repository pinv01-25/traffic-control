from typing import Dict, Any, List, Optional, Union
from database.db import SessionLocal
from database.metadata_model import MetadataIndex
from utils.error_handler import ErrorHandler
from utils.time import iso_to_unix
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for handling database operations."""
    
    @staticmethod
    def register_metadata(data_type: str, timestamp: int, traffic_light_id: str) -> None:
        """
        Register metadata in the local database.
        
        Args:
            data_type: Type of data (data, optimization)
            timestamp: Unix timestamp
            traffic_light_id: Traffic light identifier
        """
        db = SessionLocal()
        try:
            # Check if metadata already exists
            existing = db.query(MetadataIndex).filter(
                MetadataIndex.type == data_type,
                MetadataIndex.timestamp == timestamp,
                MetadataIndex.traffic_light_id == traffic_light_id
            ).first()
            
            if existing:
                logger.info(f"Metadata already exists: {data_type}, {traffic_light_id}, {timestamp}")
                return
            
            logger.info(f"Registering metadata: {data_type}, {traffic_light_id}, {timestamp}")
            entry = MetadataIndex(
                type=data_type,
                timestamp=timestamp,
                traffic_light_id=traffic_light_id
            )
            db.add(entry)
            db.commit()
            logger.info("Metadata registered successfully.")
        except Exception as e:
            db.rollback()
            raise ErrorHandler.handle_database_error(e, "register_metadata")
        finally:
            db.close()
    
    @staticmethod
    def register_optimization_metadata(optimized_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """
        Register optimization metadata.
        
        Args:
            optimized_data: Optimized data containing timestamp and traffic_light_id
        """
        # Check if this is a list of optimizations (batch result)
        if isinstance(optimized_data, list):
            logger.info(f"Registering {len(optimized_data)} optimization metadata entries...")
            
            # Register each individual optimization
            for i, individual_optimization in enumerate(optimized_data):
                logger.info(f"Registering individual optimization {i+1}/{len(optimized_data)} for sensor {individual_optimization.get('traffic_light_id')}")
                
                # Convert ISO timestamp to Unix timestamp
                iso_timestamp = individual_optimization["timestamp"]
                unix_timestamp = iso_to_unix(iso_timestamp)
                
                DatabaseService.register_metadata(
                    "optimization",
                    unix_timestamp,
                    individual_optimization["traffic_light_id"]
                )
            
            logger.info(f"Successfully registered {len(optimized_data)} individual optimizations")
        else:
            # Check if this is an optimization batch (has 'optimizations' field)
            if "optimizations" in optimized_data:
                logger.info(f"Registering optimization batch with {len(optimized_data['optimizations'])} optimizations...")
                
                # Register each optimization in the batch
                for i, individual_optimization in enumerate(optimized_data["optimizations"]):
                    logger.info(f"Registering batch optimization {i+1}/{len(optimized_data['optimizations'])} for sensor {individual_optimization.get('traffic_light_id')}")
                    
                    # Convert ISO timestamp to Unix timestamp
                    iso_timestamp = individual_optimization["timestamp"]
                    unix_timestamp = iso_to_unix(iso_timestamp)
                    
                    DatabaseService.register_metadata(
                        "optimization",
                        unix_timestamp,
                        individual_optimization["traffic_light_id"]
                    )
                
                logger.info(f"Successfully registered {len(optimized_data['optimizations'])} batch optimizations")
            else:
                # Single optimization - register directly
                # Convert ISO timestamp to Unix timestamp
                iso_timestamp = optimized_data["timestamp"]
                unix_timestamp = iso_to_unix(iso_timestamp)
                
                DatabaseService.register_metadata(
                    "optimization",
                    unix_timestamp,
                    optimized_data["traffic_light_id"]
                )
    
    @staticmethod
    def get_metadata_by_traffic_light(traffic_light_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get metadata entries for a specific traffic light.
        
        Args:
            traffic_light_id: Traffic light identifier
            limit: Maximum number of entries to return
        Returns:
            List of metadata entries
        """
        db = SessionLocal()
        try:
            entries = db.query(MetadataIndex).filter(
                MetadataIndex.traffic_light_id == traffic_light_id
            ).order_by(MetadataIndex.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    "id": entry.id,
                    "type": entry.type,
                    "timestamp": entry.timestamp,
                    "traffic_light_id": entry.traffic_light_id,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None
                }
                for entry in entries
            ]
        except Exception as e:
            raise ErrorHandler.handle_database_error(e, "get_metadata_by_traffic_light")
        finally:
            db.close()
    
    @staticmethod
    def get_metadata_by_type(data_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get metadata entries by data type.
        
        Args:
            data_type: Type of data to filter by
            limit: Maximum number of entries to return
        Returns:
            List of metadata entries
        """
        db = SessionLocal()
        try:
            entries = db.query(MetadataIndex).filter(
                MetadataIndex.type == data_type
            ).order_by(MetadataIndex.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    "id": entry.id,
                    "type": entry.type,
                    "timestamp": entry.timestamp,
                    "traffic_light_id": entry.traffic_light_id,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None
                }
                for entry in entries
            ]
        except Exception as e:
            raise ErrorHandler.handle_database_error(e, "get_metadata_by_type")
        finally:
            db.close()
    
    @staticmethod
    def get_recent_metadata(limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent metadata entries.
        
        Args:
            limit: Maximum number of entries to return
        Returns:
            List of recent metadata entries
        """
        db = SessionLocal()
        try:
            entries = db.query(MetadataIndex).order_by(
                MetadataIndex.timestamp.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": entry.id,
                    "type": entry.type,
                    "timestamp": entry.timestamp,
                    "traffic_light_id": entry.traffic_light_id,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None
                }
                for entry in entries
            ]
        except Exception as e:
            raise ErrorHandler.handle_database_error(e, "get_recent_metadata")
        finally:
            db.close()
    
    @staticmethod
    def delete_metadata_by_traffic_light(traffic_light_id: str) -> int:
        """
        Delete all metadata entries for a specific traffic light.
        
        Args:
            traffic_light_id: Traffic light identifier
        Returns:
            Number of deleted entries
        """
        db = SessionLocal()
        try:
            deleted_count = db.query(MetadataIndex).filter(
                MetadataIndex.traffic_light_id == traffic_light_id
            ).delete()
            db.commit()
            logger.info(f"Deleted {deleted_count} metadata entries for traffic light {traffic_light_id}")
            return deleted_count
        except Exception as e:
            db.rollback()
            raise ErrorHandler.handle_database_error(e, "delete_metadata_by_traffic_light")
        finally:
            db.close()
    
    @staticmethod
    def get_metadata_stats() -> Dict[str, Any]:
        """
        Get metadata statistics.
        
        Returns:
            Dictionary with metadata statistics
        """
        db = SessionLocal()
        try:
            total_entries = db.query(MetadataIndex).count()
            data_entries = db.query(MetadataIndex).filter(MetadataIndex.type == "data").count()
            optimization_entries = db.query(MetadataIndex).filter(MetadataIndex.type == "optimization").count()
            batch_entries = db.query(MetadataIndex).filter(MetadataIndex.type == "data").count()  # Changed from "data-batch" to "data"
            
            # Get unique traffic light IDs
            unique_traffic_lights = db.query(MetadataIndex.traffic_light_id).distinct().count()
            
            return {
                "total_entries": total_entries,
                "data_entries": data_entries,
                "optimization_entries": optimization_entries,
                "batch_entries": batch_entries,
                "unique_traffic_lights": unique_traffic_lights
            }
        except Exception as e:
            raise ErrorHandler.handle_database_error(e, "get_metadata_stats")
        finally:
            db.close() 