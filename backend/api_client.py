import requests
import time
import logging
from typing import Dict, Any, List, Optional, Union
from .config_manager import ConfigManager
from shared.constants.api_constants import ApiConstants

class ApiClient:

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.api_key = ApiConstants.ETHERSCAN_API_KEY
        self.network_config = config_manager.get_network_config()
        self.api_url = self.network_config["api_url"]
        self.max_retries = ApiConstants.MAX_RETRIES
        self.delay_between_requests = ApiConstants.DELAY_BETWEEN_REQUESTS
        self.block_chunk_size = ApiConstants.BLOCK_CHUNK_SIZE
        
    def make_request_with_retry(self, url: str, params: Dict[str, Any],
                                retries: Optional[int] = None) -> Optional[Dict[str, Any]]:

        if retries is None:
            retries = self.max_retries
            
        for attempt in range(1, retries + 1):
            try:
                response = requests.get(url, params=params, timeout=ApiConstants.REQUEST_TIMEOUT)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    wait_time = self.delay_between_requests * attempt * 2
                    logging.warning(f"Rate limit hit, waiting {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logging.error(f"HTTP {response.status_code}: {response.text}")
                    
            except requests.RequestException as e:
                logging.error(f"Request error (attempt {attempt}): {e}")
            except Exception as e:
                logging.error(f"Unexpected error (attempt {attempt}): {e}")
                
            time.sleep(self.delay_between_requests * attempt)
        
        return None
    
    def _validate_etherscan_response(self, data: Dict[str, Any]) -> bool:

        if not isinstance(data, dict) or "result" not in data:
            return False
            
        if data.get("status") == "1" or isinstance(data["result"], list):
            return True
            
        if data.get("status") == "0" and "No transactions found" in str(data.get("message", "")):
            return True
            
        return False
    
    def etherscan_api_request(self, params: Dict[str, Any]) -> Dict[str, Any]:

        params["apikey"] = self.api_key
        
        for attempt in range(1, self.max_retries + 1):
            data = self.make_request_with_retry(self.api_url, params, retries=1)

            if data and self._validate_etherscan_response(data):
                if data.get("message") in ["No transactions found", "No records found"]:
                    return {"result": []}
                return data
            
            logging.error(f"Invalid Etherscan response (attempt {attempt}): {data}")
            
        raise Exception("Failed to get valid response from Etherscan API")
    
    def get_wallet_transactions(self, wallet_address: str, count: int = 10) -> List[Dict[str, Any]]:

        params = {
            "module": "account",
            "action": "txlist",
            "address": wallet_address,
            "page": 1,
            "offset": count,
            "sort": "desc"
        }
        
        try:
            data = self.etherscan_api_request(params)
            return data.get("result", [])
        except Exception as e:
            logging.error(f"Error fetching wallet transactions for {wallet_address}: {e}")
            return []
    
    def get_dexscreener_pairs(self, token_address: str,
                              retries: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:

        url = ApiConstants.DEXSCREENER_API_URL.format(token_address.lower())
        data = self.make_request_with_retry(url, {}, retries=retries)

        if data is None:
            return None

        return data.get("pairs") or []

    def get_native_token_usd_price(self) -> Union[float, str]:

        token_id = self.network_config["native_token_full_name"]
        url = ApiConstants.COINGECKO_API_URL
        params = {
            "ids": token_id,
            "vs_currencies": "usd"
        }
        
        for attempt in range(1, 4):
            try:
                data = self.make_request_with_retry(url, params)
                
                if not data:
                    continue
                    
                price = data.get(token_id, {}).get("usd")
                if price is not None:
                    return float(price)
                
                logging.error(f"No USD price found for {token_id}")
                break
                
            except (ValueError, KeyError, TypeError) as e:
                logging.error(f"Error parsing CoinGecko response (attempt {attempt}): {e}")
            except Exception as e:
                logging.error(f"Error fetching from CoinGecko (attempt {attempt}): {e}")
            
            if attempt < 3:
                time.sleep(10 if attempt == 1 else self.delay_between_requests * attempt)
        
        return "error"