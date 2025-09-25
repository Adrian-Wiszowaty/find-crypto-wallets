"""
Ulepszone klasy do obsługi błędów i logowania.
"""
import logging
import sys
from typing import Optional, Any
from datetime import datetime


class CustomFormatter(logging.Formatter):
    """Niestandardowy formatter dla logów z kolorami"""
    
    # Kody kolorów ANSI
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        if hasattr(record, 'color') and record.color:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
            record.msg = f"{color}{record.msg}{reset}"
        
        return super().format(record)


class LoggerSetup:
    """Klasa do konfiguracji systemu logowania"""
    
    @staticmethod
    def setup_logger(name: str, log_file: str, level: int = logging.INFO, 
                    console_output: bool = False) -> logging.Logger:
        """
        Konfiguruje logger z plikiem logów i opcjonalnie z wyjściem na konsolę.
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Usuń istniejące handlery
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Formatter dla plików
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Handler dla pliku
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Błąd tworzenia file handler: {e}")
        
        # Handler dla konsoli (opcjonalny)
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            
            # Kolorowy formatter dla konsoli
            console_formatter = CustomFormatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger


class ValidationError(Exception):
    """Wyjątek dla błędów walidacji danych"""
    pass


class ApiError(Exception):
    """Wyjątek dla błędów API"""
    pass


class ConfigurationError(Exception):
    """Wyjątek dla błędów konfiguracji"""
    pass


class DataValidator:
    """Klasa do walidacji różnych typów danych"""
    
    @staticmethod
    def validate_ethereum_address(address: str) -> bool:
        """Waliduje adres Ethereum"""
        if not address:
            return False
        
        # Podstawowa walidacja - adres powinien zaczynać się od 0x i mieć 42 znaki
        if not address.startswith('0x') or len(address) != 42:
            return False
        
        # Sprawdź czy zawiera tylko hex znaki
        try:
            int(address[2:], 16)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_datetime_string(date_str: str, format_str: str = "%d-%m-%Y %H:%M:%S") -> bool:
        """Waliduje format daty"""
        try:
            datetime.strptime(date_str, format_str)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_network(network: str) -> bool:
        """Waliduje nazwę sieci"""
        valid_networks = ['ETH', 'BSC', 'BASE']
        return network in valid_networks
    
    @staticmethod
    def validate_positive_number(value: Any) -> bool:
        """Waliduje czy wartość jest liczbą dodatnią"""
        try:
            num = float(value)
            return num > 0
        except (ValueError, TypeError):
            return False


class ErrorHandler:
    """Klasa do obsługi i raportowania błędów"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def handle_api_error(self, error: Exception, context: str = "") -> None:
        """Obsługuje błędy API"""
        error_msg = f"API Error{f' in {context}' if context else ''}: {error}"
        self.logger.error(error_msg)
        raise ApiError(error_msg)
    
    def handle_validation_error(self, message: str, context: str = "") -> None:
        """Obsługuje błędy walidacji"""
        error_msg = f"Validation Error{f' in {context}' if context else ''}: {message}"
        self.logger.error(error_msg)
        raise ValidationError(error_msg)
    
    def handle_configuration_error(self, message: str, context: str = "") -> None:
        """Obsługuje błędy konfiguracji"""
        error_msg = f"Configuration Error{f' in {context}' if context else ''}: {message}"
        self.logger.error(error_msg)
        raise ConfigurationError(error_msg)
    
    def log_warning(self, message: str, context: str = "") -> None:
        """Loguje ostrzeżenie"""
        warning_msg = f"{f'[{context}] ' if context else ''}{message}"
        self.logger.warning(warning_msg)
    
    def log_info(self, message: str, context: str = "") -> None:
        """Loguje informację"""
        info_msg = f"{f'[{context}] ' if context else ''}{message}"
        self.logger.info(info_msg)
    
    def log_error(self, error: Exception, context: str = "") -> None:
        """Loguje błąd bez rzucania wyjątku"""
        error_msg = f"{f'[{context}] ' if context else ''}{error}"
        self.logger.error(error_msg)


class RetryMechanism:
    """Klasa implementująca mechanizm ponawiania operacji"""
    
    @staticmethod
    def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0, 
                          backoff_factor: float = 2.0, logger: Optional[logging.Logger] = None):
        """
        Wykonuje funkcję z mechanizmem ponawiania i wykładniczym opóźnieniem.
        """
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
    """Klasa do monitorowania wydajności operacji"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._start_times = {}
    
    def start_timer(self, operation_name: str) -> None:
        """Rozpoczyna pomiar czasu operacji"""
        import time
        self._start_times[operation_name] = time.time()
        self.logger.info(f"Started: {operation_name}")
    
    def end_timer(self, operation_name: str) -> float:
        """Kończy pomiar czasu i zwraca czas trwania"""
        import time
        
        if operation_name not in self._start_times:
            self.logger.warning(f"Timer for '{operation_name}' was not started")
            return 0.0
        
        duration = time.time() - self._start_times[operation_name]
        del self._start_times[operation_name]
        
        self.logger.info(f"Completed: {operation_name} (Duration: {duration:.2f}s)")
        return duration
    
    def get_memory_usage(self) -> str:
        """Zwraca informacje o użyciu pamięci"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return f"RSS: {memory_info.rss / 1024 / 1024:.1f} MB, VMS: {memory_info.vms / 1024 / 1024:.1f} MB"
        except ImportError:
            return "psutil not available"
        except Exception as e:
            return f"Error getting memory info: {e}"