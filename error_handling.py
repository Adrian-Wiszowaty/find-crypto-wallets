import logging
import sys
from typing import Optional, Any
from datetime import datetime


class CustomFormatter(logging.Formatter):
    
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        if hasattr(record, 'color') and record.color:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
            record.msg = f"{color}{record.msg}{reset}"
        
        return super().format(record)


class LoggerSetup:
    
    @staticmethod
    def setup_logger(name: str, log_file: str, level: int = logging.INFO, 
                    console_output: bool = False) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Error creating file handler: {e}")
        
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            
            console_formatter = CustomFormatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger


class ValidationError(Exception):
    pass


class ApiError(Exception):
    pass


class ConfigurationError(Exception):
    pass


class DataValidator:
    
    @staticmethod
    def validate_ethereum_address(address: str) -> bool:
        if not address:
            return False
        
        if not address.startswith('0x') or len(address) != 42:
            return False
        
        try:
            int(address[2:], 16)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_datetime_string(date_str: str, format_str: str = "%d-%m-%Y %H:%M:%S") -> bool:
        try:
            datetime.strptime(date_str, format_str)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_network(network: str) -> bool:
        valid_networks = ['ETH', 'BSC', 'BASE']
        return network in valid_networks
    
    @staticmethod
    def validate_positive_number(value: Any) -> bool:
        try:
            num = float(value)
            return num > 0
        except (ValueError, TypeError):
            return False


class ErrorHandler:
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def handle_api_error(self, error: Exception, context: str = "") -> None:
        error_msg = f"API Error{f' in {context}' if context else ''}: {error}"
        self.logger.error(error_msg)
        raise ApiError(error_msg)
    
    def handle_validation_error(self, message: str, context: str = "") -> None:
        error_msg = f"Validation Error{f' in {context}' if context else ''}: {message}"
        self.logger.error(error_msg)
        raise ValidationError(error_msg)
    
    def handle_configuration_error(self, message: str, context: str = "") -> None:
        error_msg = f"Configuration Error{f' in {context}' if context else ''}: {message}"
        self.logger.error(error_msg)
        raise ConfigurationError(error_msg)
    
    def log_warning(self, message: str, context: str = "") -> None:
        warning_msg = f"{f'[{context}] ' if context else ''}{message}"
        self.logger.warning(warning_msg)
    
    def log_info(self, message: str, context: str = "") -> None:
        info_msg = f"{f'[{context}] ' if context else ''}{message}"
        self.logger.info(info_msg)
    
    def log_error(self, error: Exception, context: str = "") -> None:
        error_msg = f"{f'[{context}] ' if context else ''}{error}"
        self.logger.error(error_msg)


class RetryMechanism:
    
    @staticmethod
    def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0, 
                          backoff_factor: float = 2.0, logger: Optional[logging.Logger] = None):
        import time
        
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    if logger:
                        logger.error(f"All {max_retries} attempts failed. Last error: {e}")
                    raise
                
                delay = base_delay * (backoff_factor ** attempt)
                if logger:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                
                time.sleep(delay)


class PerformanceMonitor:
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._start_times = {}
    
    def start_timer(self, operation_name: str) -> None:
        import time
        self._start_times[operation_name] = time.time()
        self.logger.info(f"Started: {operation_name}")
    
    def end_timer(self, operation_name: str) -> float:
        import time
        
        if operation_name not in self._start_times:
            self.logger.warning(f"Timer for '{operation_name}' was not started")
            return 0.0
        
        duration = time.time() - self._start_times[operation_name]
        del self._start_times[operation_name]
        
        self.logger.info(f"Completed: {operation_name} (Duration: {duration:.2f}s)")
        return duration
    
    def get_memory_usage(self) -> str:
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return f"RSS: {memory_info.rss / 1024 / 1024:.1f} MB, VMS: {memory_info.vms / 1024 / 1024:.1f} MB"
        except ImportError:
            return "psutil not available"
        except Exception as e:
            return f"Error getting memory info: {e}"