import logging
from typing import Union, Optional, List, Dict, Any
from .api_client import ApiClient
from .config_manager import ConfigManager

class ExchangeRateService:

    def __init__(self, config_manager: ConfigManager, api_client: ApiClient):
        self.config_manager = config_manager
        self.api_client = api_client
        self.network_config = config_manager.get_network_config()
        self.native_address = self.network_config["native_address"].lower()
        self._pairs_cache: Dict[str, List[Dict[str, Any]]] = {}

    def _fetch_pairs(self, token_address: str, retries: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        token_address = token_address.lower()

        if token_address in self._pairs_cache:
            return self._pairs_cache[token_address]

        pairs = self.api_client.get_dexscreener_pairs(token_address, retries)
        if pairs is not None:
            self._pairs_cache[token_address] = pairs

        return pairs

    def get_exchange_rate(self, token_address: str, retries: Optional[int] = None) -> Union[float, str]:
        pairs = self._fetch_pairs(token_address, retries)
        if pairs is None:
            logging.error(f"Failed to fetch the exchange rate for token {token_address}")
            return "error"

        token_addr = token_address.lower()
        for pair in pairs:
            base_addr = pair.get("baseToken", {}).get("address", "").lower()
            quote_addr = pair.get("quoteToken", {}).get("address", "").lower()

            if self.native_address not in (base_addr, quote_addr):
                continue

            try:
                if base_addr == token_addr:
                    return float(pair["priceNative"])
                if quote_addr == token_addr:
                    return 1.0 / float(pair["priceNative"])
            except (KeyError, ValueError, ZeroDivisionError) as e:
                logging.error(f"Error parsing exchange rate for token {token_address}: {e}")

        logging.error(f"No native pair found for token {token_address}")
        return "error"

    def get_token_usd_rate(self, token_address: str, retries: Optional[int] = None) -> Union[float, str]:
        pairs = self._fetch_pairs(token_address, retries)
        if pairs is None:
            logging.error(f"Failed to fetch the USD rate for token {token_address}")
            return "error"

        for pair in pairs:
            price_usd = pair.get("priceUsd")
            if price_usd is None:
                continue
            try:
                return float(price_usd)
            except ValueError as e:
                logging.error(f"Error parsing USD rate for token {token_address}: {e}")

        logging.error(f"No USD price found for token {token_address}")
        return "error"

    def get_token_name(self, token_address: str, retries: Optional[int] = None) -> str:
        pairs = self._fetch_pairs(token_address, retries)
        if pairs is None:
            logging.error(f"Failed to fetch the token name for token {token_address}")
            return "error"

        token_addr = token_address.lower()
        for pair in pairs:
            base_token = pair.get("baseToken", {})
            quote_token = pair.get("quoteToken", {})

            if base_token.get("address", "").lower() == token_addr:
                return base_token.get("name") or base_token.get("symbol") or "error"
            if quote_token.get("address", "").lower() == token_addr:
                return quote_token.get("name") or quote_token.get("symbol") or "error"

        logging.error(f"No token name found for token {token_address}")
        return "error"

    def get_native_to_usd_rate(self) -> Union[float, str]:
        return self.api_client.get_native_token_usd_price()
