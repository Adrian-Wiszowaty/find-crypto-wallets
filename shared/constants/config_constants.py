from shared.constants.api_constants import ApiConstants

class ConfigConstants:
    
    DATE_FORMAT = "%d-%m-%Y %H:%M:%S"
    TIMEZONE_OFFSET_HOURS = 1
    
    DEFAULT_CONFIG = {
        "NETWORK": "ETH",
        "T1_STR": "17-03-2025 22:25:00",
        "T2_STR": "18-03-2025 19:30:00", 
        "T3_STR": "19-03-2025 20:00:00",
        "TOKEN_CONTRACT_ADDRESS": ApiConstants.DEFAULT_TOKEN_ADDRESS
    }