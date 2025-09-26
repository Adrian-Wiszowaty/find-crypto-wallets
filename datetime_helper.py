"""
Klasa pomocnicza do obsługi operacji związanych z datami i czasem.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Union
from constants import Constants


class DateTimeHelper:
    """Zarządza operacjami związanymi z konwersją dat i czasem"""
    
    @staticmethod
    def parse_date(date_str: str) -> int:
        """
        Konwertuje datę w formacie "DD-MM-YYYY H:M:S" do znacznika unixowego
        i odejmuje 1 godzinę (timezone offset).
        
        Args:
            date_str: Data w formacie Constants.DATE_FORMAT
            
        Returns:
            int: Unix timestamp
            
        Raises:
            ValueError: Gdy format daty jest niepoprawny
            Exception: Inne błędy parsowania
        """
        try:
            dt = datetime.strptime(date_str, Constants.DATE_FORMAT)
            dt = dt - timedelta(hours=Constants.TIMEZONE_OFFSET_HOURS)
            dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except ValueError as e:
            error_msg = f"{Constants.ERROR_INVALID_DATE_FORMAT} {date_str}: {e}"
            logging.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Błąd parsowania daty {date_str}: {e}"
            logging.error(error_msg)
            raise Exception(error_msg)
    
    @staticmethod
    def format_execution_time(seconds: float) -> str:
        """
        Formatuje czas wykonania w czytelną formę MM:SS.
        
        Args:
            seconds: Czas w sekundach
            
        Returns:
            str: Sformatowany czas w formacie MM:SS
        """
        minutes, secs = divmod(seconds, 60)
        return f"{int(minutes):02d}:{int(secs):02d}"
    
    @staticmethod
    def timestamp_to_readable(timestamp: Union[int, str]) -> str:
        """
        Konwertuje timestamp Unix do czytelnego formatu daty.
        
        Args:
            timestamp: Unix timestamp
            
        Returns:
            str: Data w formacie YYYY-MM-DD HH:MM:SS UTC
        """
        try:
            if isinstance(timestamp, str):
                timestamp = int(timestamp)
            
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, OSError) as e:
            logging.error(f"Błąd konwersji timestamp {timestamp}: {e}")
            return f"Invalid timestamp: {timestamp}"
    
    @staticmethod
    def get_current_timestamp() -> int:
        """
        Zwraca aktualny Unix timestamp.
        
        Returns:
            int: Aktualny timestamp
        """
        return int(datetime.now(timezone.utc).timestamp())
    
    @staticmethod
    def validate_date_range(t1_str: str, t2_str: str, t3_str: str) -> bool:
        """
        Waliduje czy przedziały czasowe są logicznie poprawne (T1 <= T2 <= T3).
        
        Args:
            t1_str: Data T1 w formacie Constants.DATE_FORMAT
            t2_str: Data T2 w formacie Constants.DATE_FORMAT  
            t3_str: Data T3 w formacie Constants.DATE_FORMAT
            
        Returns:
            bool: True jeśli przedziały są poprawne
            
        Raises:
            ValueError: Gdy przedziały są niepoprawne lub daty mają zły format
        """
        try:
            t1 = DateTimeHelper.parse_date(t1_str)
            t2 = DateTimeHelper.parse_date(t2_str)
            t3 = DateTimeHelper.parse_date(t3_str)
            
            if not (t1 <= t2 <= t3):
                raise ValueError(f"")
            
            return True
        except Exception as e:
            logging.error(f"Błąd walidacji przedziału czasowego: {e}")
            raise