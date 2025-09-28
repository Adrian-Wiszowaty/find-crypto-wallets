import logging
from datetime import datetime, timezone, timedelta
from typing import Union
from constants import Constants

class DateTimeHelper:
    
    @staticmethod
    def parse_date(date_str: str) -> int:
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
        
        minutes, secs = divmod(seconds, 60)
        return f"{int(minutes):02d}:{int(secs):02d}"
    
    @staticmethod
    def timestamp_to_readable(timestamp: Union[int, str]) -> str:
        
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
        
        return int(datetime.now(timezone.utc).timestamp())
    
    @staticmethod
    def validate_date_range(t1_str: str, t2_str: str, t3_str: str) -> bool:
        
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