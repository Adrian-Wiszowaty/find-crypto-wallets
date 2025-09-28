class ApiConstants:
    
    ETHERSCAN_API_KEY = "N1D6WM3XXK4E1SSNJV2BP4YQ4PWG32IXED"
    
    DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/tokens/{}"
    COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
    
    DEFAULT_TOKEN_ADDRESS = "0x712f43B21cf3e1B189c27678C0f551c08c01D150"
    
    DELAY_BETWEEN_REQUESTS = 0.2
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 10
    
    BLOCK_CHUNK_SIZE = 1200
    FREQUENCY_INTERVAL_SECONDS = 60
    MIN_FREQUENCY_VIOLATIONS = 5
    MIN_TRANSACTION_COUNT = 10
    MIN_USD_VALUE = 100.0
    MIN_BALANCE_PERCENTAGE = 50
    
    API_MODULE_ACCOUNT = "account"
    API_MODULE_BLOCK = "block"
    
    API_ACTION_TOKENTX = "tokentx"
    API_ACTION_TXLIST = "txlist"
    API_ACTION_BALANCE = "balance"
    API_ACTION_GET_BLOCK_BY_TIME = "getblocknobytime"
    
    API_SORT_ASC = "asc"
    API_SORT_DESC = "desc"