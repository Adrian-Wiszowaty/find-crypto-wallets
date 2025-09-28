class NetworkConstants:
    
    CHAIN_ID_ETH = 1
    CHAIN_ID_BSC = 56
    CHAIN_ID_BASE = 8453
    
    API_URL_ETH = "https://api.etherscan.io/v2/api?chainid=1" 
    API_URL_BSC = "https://api.etherscan.io/v2/api?chainid=56"
    API_URL_BASE = "https://api.etherscan.io/v2/api?chainid=8453"
    
    WETH_ADDRESS_ETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    WBNB_ADDRESS_BSC = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
    WETH_ADDRESS_BASE = "0x4200000000000000000000000000000000000006"

    
    NETWORKS = {
        "ETH": {
            "api_url": API_URL_ETH,
            "chain_id": CHAIN_ID_ETH,
            "native_token_name": "ETH",
            "native_token_full_name": "ethereum",
            "native_address": WETH_ADDRESS_ETH,
            "explorer": "https://etherscan.io"
        },
        "BSC": {
            "api_url": API_URL_BSC,
            "chain_id": CHAIN_ID_BSC,
            "native_token_name": "BNB",
            "native_token_full_name": "binancecoin",
            "native_address": WBNB_ADDRESS_BSC,
            "explorer": "https://bscscan.com"
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