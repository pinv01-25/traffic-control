import logging
import traceback
from functools import wraps
from typing import Any, Callable

from fastapi import HTTPException

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling for the traffic control service."""
    
    @staticmethod
    def handle_validation_error(error: ValueError, context: str = "") -> HTTPException:
        """Handle validation errors."""
        error_msg = f"Validation error in {context}: {str(error)}" if context else str(error)
        logger.error(error_msg)
        return HTTPException(status_code=422, detail=error_msg)
    
    @staticmethod
    def handle_storage_error(error: Exception, context: str = "") -> HTTPException:
        """Handle storage-related errors."""
        error_msg = f"Storage error in {context}: {str(error)}" if context else str(error)
        logger.error(error_msg)
        return HTTPException(status_code=500, detail=error_msg)
    
    @staticmethod
    def handle_sync_error(error: Exception, context: str = "") -> HTTPException:
        """Handle sync service errors."""
        error_msg = f"Sync service error in {context}: {str(error)}" if context else str(error)
        logger.error(error_msg)
        return HTTPException(status_code=500, detail=error_msg)
    
    @staticmethod
    def handle_database_error(error: Exception, context: str = "") -> HTTPException:
        """Handle database errors."""
        error_msg = f"Database error in {context}: {str(error)}" if context else str(error)
        logger.error(error_msg)
        return HTTPException(status_code=500, detail=error_msg)
    
    @staticmethod
    def handle_generic_error(error: Exception, context: str = "") -> HTTPException:
        """Handle generic errors."""
        error_msg = f"Unexpected error in {context}: {str(error)}" if context else str(error)
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return HTTPException(status_code=500, detail="Internal server error")
    
    @staticmethod
    def safe_execute(func: Callable, *args, context: str = "", **kwargs) -> Any:
        """
        Safely execute a function with error handling.
        
        Args:
            func: Function to execute
            context: Context for error messages
            *args, **kwargs: Function arguments
        Returns:
            Function result
        Raises:
            HTTPException: If function fails
        """
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            raise ErrorHandler.handle_validation_error(e, context) from e
        except Exception as e:
            raise ErrorHandler.handle_generic_error(e, context) from e

def error_handler_decorator(context: str = ""):
    """
    Decorator for automatic error handling.
    
    Args:
        context: Context for error messages
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                raise ErrorHandler.handle_validation_error(e, context) from e
            except Exception as e:
                raise ErrorHandler.handle_generic_error(e, context) from e
        return wrapper
    return decorator 