import requests
import time
import logging
from typing import Union, Dict, Any, Optional
from config_manager import ConfigManager
from constants import Constants


class ExchangeRateService:
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.network_config = config_manager.get_network_config()
        self.native_token_name = self.network_config["native_token_name"]
        self.native_token_full_name = self.network_config["native_token_full_name"]
        self.native_address = self.network_config["native_address"]
        
        network = config_manager.config.get("NETWORK", "ETH")
        if network == "BASE":
            self.wrapped_native_address = Constants.WETH_ADDRESS_BASE
        elif network == "ETH":
            self.wrapped_native_address = Constants.WETH_ADDRESS_ETH
        else:
            self.wrapped_native_address = Constants.WBNB_ADDRESS_BSC
        
        self.max_retries = Constants.MAX_RETRIES
        self.delay_between_requests = Constants.DELAY_BETWEEN_REQUESTS
        
    def get_exchange_rate(self, token_address: str, retries: int = None) -> Union[float, str]:
        if retries is None:
            retries = self.max_retries
            
        attempt = 0
        rate = None
        
        while attempt < retries:
            try:
                url = Constants.DEXSCREENER_API_URL.format(token_address.lower())
                response = requests.get(url, timeout=10)
                
                if response.status_code != 200:
                    error_msg = f"Server response for token: {response.status_code}, body: {response.text}"
                    logging.error(error_msg)
                    raise Exception(f"HTTP error dla tokena: {response.status_code}")
                
                data = response.json()
                pairs = data.get("pairs", [])
                
                for pair in pairs:
                    native_addr = self.wrapped_native_address.lower()
                    base_token_addr = pair.get("baseToken", {}).get("address", "").lower()
                    quote_token_addr = pair.get("quoteToken", {}).get("address", "").lower()
                    
                    if native_addr in (base_token_addr, quote_token_addr):
                        if base_token_addr == token_address.lower():
                            rate = float(pair["priceNative"])
                        elif quote_token_addr == token_address.lower():
                            rate = 1 / float(pair["priceNative"])
                        break
                
                if rate is not None:
                    logging.info(f"Pobrano kurs wymiany dla tokena {token_address}: {rate}")
                    return rate
                else:
                    error_msg = f"Nie znaleziono pary z natywnym tokenem dla tokena {token_address}"
                    logging.error(error_msg)
                    raise Exception("Brak odpowiedniej pary w danych API")
                    
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} to fetch the rate failed: {e}")
                attempt += 1
                if attempt < retries:
                    time.sleep(self.delay_between_requests * attempt)
        
        logging.error(f"Failed to fetch the exchange rate for token {token_address} after {retries} attempts")
        return "error"
    
    def get_native_to_usd_rate(self, retries: int = None) -> Union[float, str]:
        if retries is None:
            retries = 3
            
        attempt = 0
        rate = None
        
        while attempt < retries:
            try:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={self.native_token_full_name}&vs_currencies=usd"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 429:
                    logging.warning("CoinGecko rate limit exceeded. Waiting before the next attempt...")
                    time.sleep(10)
                    attempt += 1
                    continue
                
                if response.status_code != 200:
                    error_msg = f"Server response for native token: {response.status_code}, body: {response.text}"
                    logging.error(error_msg)
                    raise Exception(f"HTTP error dla natywnego tokena: {response.status_code}")
                
                data = response.json()
                rate = data.get(self.native_token_full_name, {}).get("usd")
                
                if rate is not None:
                    logging.info(f"Pobrano kurs wymiany {self.native_token_name} -> USD: {rate}")
                    return float(rate)
                else:
                    error_msg = f"Nie znaleziono kursu wymiany dla natywnego tokena {self.native_token_full_name}"
                    logging.error(error_msg)
                    raise Exception("Brak kursu wymiany w danych API")
                    
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} to fetch the native token USD rate failed: {e}")
                attempt += 1
                if attempt < retries:
                    time.sleep(self.delay_between_requests * attempt)
        
        logging.error(f"Failed to fetch the exchange rate {self.native_token_name} -> USD after {retries} attempts")
        return "error"
    
    def calculate_token_value_in_usd(self, token_amount: float, token_address: str) -> Dict[str, Union[float, str]]:
        result = {
            "native_value": "error",
            "usd_value": "error", 
            "exchange_rate": "error",
            "native_usd_rate": "error"
        }
        
        try:
            exchange_rate = self.get_exchange_rate(token_address)
            result["exchange_rate"] = exchange_rate
            
            if exchange_rate == "error":
                return result
                
            native_usd_rate = self.get_native_to_usd_rate()
            result["native_usd_rate"] = native_usd_rate
            
            if native_usd_rate == "error":
                native_value = round(token_amount * float(exchange_rate), 6)
                result["native_value"] = native_value
                return result
            
            native_value = round(token_amount * float(exchange_rate), 6)
            usd_value = round(native_value * float(native_usd_rate), 2)
            
            result["native_value"] = native_value
            result["usd_value"] = usd_value
            
            return result
            
        except Exception as e:
            logging.error(f"Error calculating token value in USD: {e}")
            return result
    
    def get_multiple_token_rates(self, token_addresses: list) -> Dict[str, Union[float, str]]:
        rates = {}
        
        for i, token_address in enumerate(token_addresses):
            logging.info(f"Pobieram kurs {i+1}/{len(token_addresses)} dla tokena {token_address}")
            rate = self.get_exchange_rate(token_address)
            rates[token_address] = rate
            
            if i < len(token_addresses) - 1:
                time.sleep(self.delay_between_requests)
                
        return rates
    
    def validate_rates(self, exchange_rate: Union[float, str], native_usd_rate: Union[float, str]) -> bool:
        return (exchange_rate != "error" and native_usd_rate != "error" and
                isinstance(exchange_rate, (int, float)) and 
                isinstance(native_usd_rate, (int, float)))