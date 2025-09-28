import requests
import time
import logging
from typing import Dict, Any, List, Optional, Union
from .config_manager import ConfigManager
from shared.constants import Constants

class ApiClient:

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.api_key = Constants.ETHERSCAN_API_KEY
        self.network_config = config_manager.get_network_config()
        self.api_url = self.network_config["api_url"]
        self.max_retries = Constants.MAX_RETRIES
        self.delay_between_requests = Constants.DELAY_BETWEEN_REQUESTS
        self.block_chunk_size = Constants.BLOCK_CHUNK_SIZE
        
    def _make_request_with_retry(self, url: str, params: Dict[str, Any], 
                                retries: int = None) -> Optional[Dict[str, Any]]:

        if retries is None:
            retries = self.max_retries
            
        for attempt in range(1, retries + 1):
            try:
                response = requests.get(url, params=params, timeout=Constants.REQUEST_TIMEOUT)
                
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
            data = self._make_request_with_retry(self.api_url, params)
            
            if data and self._validate_etherscan_response(data):
                if data.get("message") in ["No transactions found", "No records found"]:
                    return {"result": []}
                return data
            
            logging.error(f"Invalid Etherscan response (attempt {attempt}): {data}")
            
        raise Exception("Failed to get valid response from Etherscan API")
    
    def get_block_by_timestamp(self, timestamp: int, closest: str = "before") -> int:

        params = {
            "module": "block",
            "action": "getblocknobytime",
            "timestamp": timestamp,
            "closest": closest
        }
        
        try:
            data = self.etherscan_api_request(params)
            return int(data["result"])
        except (ValueError, KeyError, TypeError) as e:
            logging.error(f"Failed to parse block number for timestamp {timestamp}: {e}")
            raise
    
    def get_token_transactions(self, contract_address: str, start_block: int, 
                              end_block: int) -> List[Dict[str, Any]]:

        all_transactions = []
        current_start = start_block
        
        while current_start <= end_block:
            current_end = min(current_start + self.block_chunk_size - 1, end_block)
            
            params = {
                "module": "account",
                "action": "tokentx",
                "contractaddress": contract_address,
                "startblock": current_start,
                "endblock": current_end,
                "sort": "asc"
            }
            
            print(f"Fetching transactions for blocks {current_start} - {current_end}...")
            
            try:
                data = self.etherscan_api_request(params)
                transactions = data.get("result", [])
                
                if transactions:
                    print(f"Found {len(transactions)} transactions")
                    all_transactions.extend(transactions)
                    
            except Exception as e:
                logging.error(f"Error fetching transactions for blocks {current_start}-{current_end}: {e}")
            finally:
                current_start = current_end + 1
                time.sleep(self.delay_between_requests)
        
        return all_transactions
    
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
    
    def get_token_price_from_dexscreener(self, token_address: str) -> Union[float, str]:

        url = Constants.DEXSCREENER_API_URL.format(token_address.lower())
        
        for attempt in range(1, 6):
            try:
                data = self._make_request_with_retry(url, {})
                
                if not data:
                    continue
                    
                pairs = data.get("pairs", [])
                native_address = self.network_config["native_address"].lower()
                
                for pair in pairs:
                    base_addr = pair.get("baseToken", {}).get("address", "").lower()
                    quote_addr = pair.get("quoteToken", {}).get("address", "").lower()
                    
                    if native_address in (base_addr, quote_addr):
                        if base_addr == token_address.lower():
                            return float(pair["priceNative"])
                        elif quote_addr == token_address.lower():
                            return 1.0 / float(pair["priceNative"])
                
                logging.error(f"No native pair found for token {token_address}")
                break
                
            except (ValueError, KeyError, TypeError) as e:
                logging.error(f"Error parsing Dexscreener response (attempt {attempt}): {e}")
            except Exception as e:
                logging.error(f"Error fetching from Dexscreener (attempt {attempt}): {e}")
            
            time.sleep(self.delay_between_requests * attempt)
        
        return "error"
    
    def get_native_token_usd_price(self) -> Union[float, str]:

        token_id = self.network_config["native_token_full_name"]
        url = Constants.COINGECKO_API_URL
        params = {
            "ids": token_id,
            "vs_currencies": "usd"
        }
        
        for attempt in range(1, 4):
            try:
                data = self._make_request_with_retry(url, params)
                
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