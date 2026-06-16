import time
import logging
from typing import List, Dict, Any
from .api_client import ApiClient
from shared.constants.api_constants import ApiConstants

class BlockchainAnalyzer:
    
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client
        
    def get_block_by_timestamp(self, timestamp: int, closest: str = "before") -> int:
        params = {
            "module": "block",
            "action": "getblocknobytime", 
            "timestamp": timestamp,
            "closest": closest,
            "apikey": self.api_client.api_key
        }
        
        try:
            data = self.api_client.make_request_with_retry(
                self.api_client.api_url, 
                params
            )
            
            if not data or "result" not in data:
                raise Exception(f"Invalid API response for timestamp {timestamp}")

            if data.get("status") == "0":
                raise Exception(f"API rejected the request: {data.get('result') or data.get('message')}")

            return int(data["result"])
            
        except Exception as e:
            error_msg = f"Failed to fetch block number for timestamp {timestamp}: {e}"
            logging.error(error_msg)
            raise Exception(error_msg)
    
    def get_token_transactions(self, startblock: int, endblock: int, token_contract_address: str) -> List[Dict[str, Any]]:
        
        all_txs = []
        current_start = startblock
        
        while current_start <= endblock:
            current_end = min(current_start + ApiConstants.BLOCK_CHUNK_SIZE - 1, endblock)
            
            params = {
                "module": "account",
                "action": "tokentx",
                "contractaddress": token_contract_address,
                "startblock": current_start,
                "endblock": current_end,
                "sort": "asc",
                "apikey": self.api_client.api_key
            }
            
            print(f"Pobieram transakcje dla bloków {current_start} - {current_end}...")
            
            try:
                data = self.api_client.make_request_with_retry(
                    self.api_client.api_url, 
                    params
                )
                
                if data and "result" in data and isinstance(data["result"], list):
                    txs = data["result"]
                    print(f"Liczba transakcji w odpowiedzi: {len(txs)}")
                    all_txs.extend(txs)
                else:
                    logging.error(f"Invalid API response format for blocks {current_start}-{current_end}: {data}")
                    
            except Exception as e:
                logging.error(f"Error processing data for blocks {current_start}-{current_end}: {e}")
            finally:
                current_start = current_end + 1
                time.sleep(ApiConstants.DELAY_BETWEEN_REQUESTS)
        
        return all_txs
    
    def filter_transactions_by_timerange(self, transactions: List[Dict[str, Any]],
                                       start_timestamp: int, end_timestamp: int) -> List[Dict[str, Any]]:
        
        filtered = []
        
        for tx in transactions:
            try:
                tx_timestamp = int(tx["timeStamp"])
                if start_timestamp <= tx_timestamp <= end_timestamp:
                    filtered.append(tx)
            except (ValueError, KeyError) as e:
                logging.warning(f"Skipping transaction with invalid timestamp: {tx}, error: {e}")
                continue
        
        filtered.sort(key=lambda tx: int(tx["timeStamp"]))
        return filtered
    
    def group_transactions_by_wallet(self, transactions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        
        wallet_transactions = {}
        
        for tx in transactions:
            try:
                wallet_from = tx["from"].lower()
                wallet_to = tx["to"].lower()
                
                if wallet_from not in wallet_transactions:
                    wallet_transactions[wallet_from] = []
                if wallet_to not in wallet_transactions:
                    wallet_transactions[wallet_to] = []
                    
                wallet_transactions[wallet_from].append(tx)
                wallet_transactions[wallet_to].append(tx)
                
            except KeyError as e:
                logging.warning(f"Skipping transaction with missing fields: {tx}, error: {e}")
                continue
        
        return wallet_transactions
    
    def find_candidate_wallets(self, transactions: List[Dict[str, Any]], 
                             purchase_start: int, purchase_end: int) -> List[str]:
        
        candidate_wallets = []
        seen = set()

        for tx in transactions:
            try:
                tx_timestamp = int(tx["timeStamp"])
                wallet_to = tx["to"].lower()

                if (purchase_start <= tx_timestamp <= purchase_end and
                    wallet_to not in seen):
                    seen.add(wallet_to)
                    candidate_wallets.append(wallet_to)
                    
            except (ValueError, KeyError) as e:
                logging.warning(f"Skipping candidate transaction: {tx}, error: {e}")
                continue
        
        return candidate_wallets