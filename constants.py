"""
Stałe używane w aplikacji Find Crypto Wallets.
Centralne miejsce do zarządzania wszystkimi stałymi wartościami.
"""


class Constants:
    """Klasa zawierająca wszystkie stałe używane w aplikacji"""
    
    # ================================ API KEYS & URLS ================================
    ETHERSCAN_API_KEY = "N1D6WM3XXK4E1SSNJV2BP4YQ4PWG32IXED"
    
    # API URLs dla różnych sieci (Etherscan V2)
    API_URL_BSC = "https://api.etherscan.io/v2/api?chainid=56"
    API_URL_ETH = "https://api.etherscan.io/v2/api?chainid=1" 
    API_URL_BASE = "https://api.etherscan.io/v2/api?chainid=8453"
    
    # External API URLs
    DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/tokens/{}"
    COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
    
    # ================================ BLOCKCHAIN ADDRESSES ================================
    # Domyślny adres kontraktu tokena
    DEFAULT_TOKEN_ADDRESS = "0x712f43B21cf3e1B189c27678C0f551c08c01D150"
    
    # Adresy natywnych tokenów dla różnych sieci
    WETH_ADDRESS_ETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    WETH_ADDRESS_BASE = "0x4200000000000000000000000000000000000006"
    WBNB_ADDRESS_BSC = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
    
    # Chain IDs
    CHAIN_ID_BSC = 56
    CHAIN_ID_ETH = 1
    CHAIN_ID_BASE = 8453
    
    # ================================ ANALYSIS PARAMETERS ================================
    # Parametry analizy bloków i transakcji
    BLOCK_CHUNK_SIZE = 1200
    FREQUENCY_INTERVAL_SECONDS = 60
    MIN_FREQUENCY_VIOLATIONS = 5
    MIN_TRANSACTION_COUNT = 10
    MIN_USD_VALUE = 100.0
    
    # Parametry requestów HTTP
    DELAY_BETWEEN_REQUESTS = 0.2
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 10
    
    # ================================ FILE & FOLDER NAMES ================================
    # Nazwy folderów
    FOLDER_WALLETS = "Wallets"
    FOLDER_CACHE = "Cache"
    FOLDER_LOGS = "Logs"
    FOLDER_CONFIG = "Config"
    FOLDER_IMAGES = "images"
    
    # Nazwy plików
    FILE_CONFIG = "config.json"
    FILE_ERROR_LOG = "error_log.txt"
    FILE_WALLET_CACHE = "wallet_frequency_cache.json"
    FILE_NETWORKS_CACHE = "networks_cache.json"
    FILE_APP_ICON = "twoja_ikona.png"
    
    # ================================ NETWORK CONFIGURATIONS ================================
    NETWORKS = {
        "BSC": {
            "api_url": API_URL_BSC,
            "chain_id": CHAIN_ID_BSC,
            "native_token_name": "BNB",
            "native_token_full_name": "binancecoin",
            "native_address": WBNB_ADDRESS_BSC,
            "explorer": "https://bscscan.com"
        },
        "ETH": {
            "api_url": API_URL_ETH,
            "chain_id": CHAIN_ID_ETH,
            "native_token_name": "ETH",
            "native_token_full_name": "ethereum",
            "native_address": WETH_ADDRESS_ETH,
            "explorer": "https://etherscan.io"
        },
        "BASE": {
            "api_url": API_URL_BASE,
            "chain_id": CHAIN_ID_BASE,
            "native_token_name": "ETH",
            "native_token_full_name": "ethereum",
            "native_address": WETH_ADDRESS_BASE,
            "explorer": "https://basescan.org"
        }
    }
    
    # ================================ DEFAULT CONFIGURATION VALUES ================================
    DEFAULT_CONFIG = {
        "NETWORK": "ETH",
        "T1_STR": "17-03-2025 22:25:00",
        "T2_STR": "18-03-2025 19:30:00", 
        "T3_STR": "19-03-2025 20:00:00",
        "TOKEN_CONTRACT_ADDRESS": DEFAULT_TOKEN_ADDRESS
    }
    
    # ================================ GUI PARAMETERS ================================
    # Parametry interfejsu użytkownika
    GUI_PADDING_X = 5
    GUI_PADDING_Y = 5
    GUI_MIN_WIDTH = 600
    GUI_MIN_HEIGHT = 400
    GUI_LOG_HEIGHT = 15
    GUI_LOG_WIDTH = 70
    
    # Kolory GUI
    GUI_LOG_BG_COLOR = "black"
    GUI_LOG_FG_COLOR = "white"
    GUI_LOG_INSERT_BG_COLOR = "white"
    
    # Nazwy aplikacji i motywów
    APP_TITLE = "Find Wallets"
    GUI_THEME = "flatly"
    
    # ================================ DATE & TIME FORMATS ================================
    DATE_FORMAT = "%d-%m-%Y %H:%M:%S"
    TIMEZONE_OFFSET_HOURS = 1  # Odejmowanie godziny od parsowanych dat
    
    # ================================ ETHERSCAN API MODULES & ACTIONS ================================
    # Moduły i akcje API Etherscan
    API_MODULE_ACCOUNT = "account"
    API_MODULE_BLOCK = "block"
    
    API_ACTION_TOKENTX = "tokentx"
    API_ACTION_TXLIST = "txlist"
    API_ACTION_BALANCE = "balance"
    API_ACTION_GET_BLOCK_BY_TIME = "getblocknobytime"
    
    API_SORT_ASC = "asc"
    API_SORT_DESC = "desc"
    
    # ================================ ERROR MESSAGES ================================
    ERROR_UNSUPPORTED_NETWORK = "Nieobsługiwana sieć"
    ERROR_CONFIG_NOT_FOUND = "BRAK PLIKU"
    ERROR_INVALID_DATE_FORMAT = "Błąd parsowania daty"
    ERROR_API_REQUEST_FAILED = "Failed to get valid response from Etherscan API"
    ERROR_ICON_LOAD_FAILED = "Błąd wczytywania ikony"
    ERROR_ICON_NOT_FOUND = "Plik ikony nie został znaleziony!"
    
    # ================================ SUCCESS MESSAGES ================================
    SUCCESS_CONFIG_LOADED = "Konfiguracja załadowana pomyślnie"
    SUCCESS_ANALYSIS_COMPLETE = "Analiza zakończona pomyślnie"
    
    # ================================ LOGGING LEVELS ================================
    LOG_LEVEL_INFO = "INFO"
    LOG_LEVEL_ERROR = "ERROR"
    LOG_LEVEL_WARNING = "WARNING"
    LOG_LEVEL_DEBUG = "DEBUG"
    
    @classmethod
    def get_network_config(cls, network: str) -> dict:
        """Zwraca konfigurację dla danej sieci"""
        if network not in cls.NETWORKS:
            raise ValueError(f"{cls.ERROR_UNSUPPORTED_NETWORK}: {network}")
        return cls.NETWORKS[network]
    
    @classmethod
    def get_supported_networks(cls) -> list:
        """Zwraca listę obsługiwanych sieci"""
        return list(cls.NETWORKS.keys())