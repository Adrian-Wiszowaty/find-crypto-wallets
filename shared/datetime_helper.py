import logging
from datetime import datetime, timezone, timedelta
from shared.constants.config_constants import ConfigConstants
from shared.constants.message_constants import MessageConstants

class DateTimeHelper:
    
    @staticmethod
    def parse_date(date_str: str) -> int:
        try:
            dt = datetime.strptime(date_str, ConfigConstants.DATE_FORMAT)
            dt = dt - timedelta(hours=ConfigConstants.TIMEZONE_OFFSET_HOURS)
            dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except ValueError as e:
            error_msg = f"{MessageConstants.ERROR_INVALID_DATE_FORMAT} {date_str}: {e}"
            logging.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Date parsing error {date_str}: {e}"
            logging.error(error_msg)
            raise Exception(error_msg)
    
    @staticmethod
    def format_execution_time(seconds: float) -> str:
        
        minutes, secs = divmod(seconds, 60)
        return f"{int(minutes):02d}:{int(secs):02d}"

    @staticmethod
    def validate_date_range(t1_str: str, t2_str: str, t3_str: str) -> bool:
        
        try:
            t1 = DateTimeHelper.parse_date(t1_str)
            t2 = DateTimeHelper.parse_date(t2_str)
            t3 = DateTimeHelper.parse_date(t3_str)
            
            if not (t1 <= t2 <= t3):
                raise ValueError("Dates must satisfy T1 ≤ T2 ≤ T3")
            
            return True
        except Exception as e:
            logging.error(f"Date range validation error: {e}")
            raise