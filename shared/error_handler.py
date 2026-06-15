import json
import logging
import os
from typing import Any, Callable, Optional
from functools import wraps

class ErrorHandler:
    
    @staticmethod
    def safe_execute(func: Callable, *args, default_return=None,
                    log_error: bool = True, error_message: Optional[str] = None, **kwargs) -> Any:
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_error:
                msg = error_message or f"Error while executing {func.__name__}: {e}"
                logging.error(msg)
            return default_return
    
    @staticmethod
    def safe_json_load(file_path: str, default_return: Optional[dict] = None) -> dict:

        if default_return is None:
            default_return = {}

        try:
            if not os.path.exists(file_path):
                logging.warning(f"Plik nie istnieje: {file_path}")
                return default_return
                
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error in file {file_path}: {e}")
            return default_return
        except Exception as e:
            logging.error(f"Error loading file {file_path}: {e}")
            return default_return
    
    @staticmethod
    def safe_json_save(data: dict, file_path: str, create_dirs: bool = True) -> bool:
        
        try:
            if create_dirs:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            logging.error(f"Error saving file {file_path}: {e}")
            return False
    
    @staticmethod
    def retry_on_exception(max_retries: int = 3, delay: float = 0.1, 
                          exceptions: tuple = (Exception,)) -> Callable:
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                import time
                
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_retries:
                            logging.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                            time.sleep(delay * (attempt + 1))
                        else:
                            logging.error(f"All attempts failed for {func.__name__}")

                if last_exception is not None:
                    raise last_exception
                raise RuntimeError(f"All attempts failed for {func.__name__}")
            return wrapper
        return decorator
    
    @staticmethod
    def validate_numeric_input(value: Any, min_value: Optional[float] = None,
                             max_value: Optional[float] = None) -> Optional[float]:
        
        try:
            num_value = float(value)
            
            if min_value is not None and num_value < min_value:
                logging.error(f"Value {num_value} is below the minimum {min_value}")
                return None
                
            if max_value is not None and num_value > max_value:
                logging.error(f"Value {num_value} is above the maximum {max_value}")
                return None
                
            return num_value
            
        except (ValueError, TypeError) as e:
            logging.error(f"Error converting value '{value}' to a number: {e}")
            return None