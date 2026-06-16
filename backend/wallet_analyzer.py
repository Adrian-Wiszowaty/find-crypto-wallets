import json
import os
import logging
from typing import Dict, List, Tuple, Any, Optional
from .config_manager import ConfigManager
from .api_client import ApiClient
from shared.constants.api_constants import ApiConstants

class WalletAnalyzer:
    
    def __init__(self, config_manager: ConfigManager, api_client: ApiClient):
        self.config_manager = config_manager
        self.api_client = api_client
        self.frequency_interval_seconds = ApiConstants.FREQUENCY_INTERVAL_SECONDS
        self.min_frequency_violations = ApiConstants.MIN_FREQUENCY_VIOLATIONS
        self.min_transaction_count = ApiConstants.MIN_TRANSACTION_COUNT
        self.min_usd_value = ApiConstants.MIN_USD_VALUE
        self.min_balance_percentage = ApiConstants.MIN_BALANCE_PERCENTAGE / 100.0
        
        paths = config_manager.get_paths_config()
        self.cache_file = paths["cache_file"]
        self.frequency_cache = self._load_frequency_cache()
    
    def _load_frequency_cache(self) -> Dict[str, bool]:
        
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading frequency cache: {e}")
        
        return {}
    
    def save_frequency_cache(self) -> None:
        
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.frequency_cache, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving frequency cache: {e}")
    
    def _check_transaction_frequency(self, transactions: List[Dict[str, Any]]) -> bool:
        
        if len(transactions) < 2:
            return True
        
        sorted_txs = sorted(transactions, key=lambda x: int(x["timeStamp"]), reverse=True)
        
        violations = 0
        for i in range(len(sorted_txs) - 1):
            t1 = int(sorted_txs[i]["timeStamp"])
            t2 = int(sorted_txs[i + 1]["timeStamp"])
            
            if (t1 - t2) < self.frequency_interval_seconds:
                violations += 1
        
        return violations < self.min_frequency_violations
    
    def check_wallet_token_frequency(self, wallet: str, wallet_transactions: List[Dict[str, Any]]) -> bool:
        
        if wallet in self.frequency_cache:
            return False
        
        if len(wallet_transactions) < self.min_transaction_count:
            return True
        
        last_transactions = sorted(
            wallet_transactions, 
            key=lambda x: int(x["timeStamp"]), 
            reverse=True
        )[:10]
        
        if not self._check_transaction_frequency(last_transactions):
            self.frequency_cache[wallet] = True
            return False
        
        return True
    
    def check_wallet_general_frequency(self, wallet: str) -> bool:
        
        if wallet in self.frequency_cache:
            return False
        
        all_transactions = self.api_client.get_wallet_transactions(wallet, count=10)
        
        if not self._check_transaction_frequency(all_transactions):
            self.frequency_cache[wallet] = True
            return False
        
        return True
    
    def simulate_wallet_balance(self, wallet: str, wallet_transactions: List[Dict[str, Any]], 
                               t1_unix: int, t2_unix: int, t3_unix: int) -> Tuple[float, float, int, int]:
        
        purchased = 0.0
        balance = 0.0
        purchase_count = 0
        sale_count = 0
        
        wallet_lower = wallet.lower()
        
        for tx in wallet_transactions:
            timestamp = int(tx["timeStamp"])
            
            if not (t1_unix <= timestamp <= t3_unix):
                continue
            
            try:
                token_decimals = int(tx.get("tokenDecimal", "0"))
                amount = float(tx["value"]) / (10 ** token_decimals)
            except (ValueError, TypeError) as e:
                logging.error(f"Error calculating transaction amount: {tx} - {e}")
                continue
            
            if tx["to"].lower() == wallet_lower:
                balance += amount

                if t1_unix <= timestamp <= t2_unix:
                    purchased += amount
                    purchase_count += 1
            
            elif tx["from"].lower() == wallet_lower:
                balance -= amount
                sale_count += 1
        
        return round(purchased, 2), round(balance, 2), purchase_count, sale_count

    def filter_wallets_by_frequency(self, candidate_wallets: List[str],
                                   wallet_transactions: Dict[str, List[Dict[str, Any]]],
                                   blockchain_analyzer) -> List[str]:
        
        filtered_wallets = []
        total_wallets = len(candidate_wallets)
        
        for index, wallet in enumerate(candidate_wallets, start=1):
            print(f"{index}/{total_wallets}: {wallet}")
            
            if wallet in self.frequency_cache:
                print(f"Portfel {wallet} odrzucony (był w cache).")
                continue
            
            txs = wallet_transactions.get(wallet, [])
            if not self.check_wallet_token_frequency(wallet, txs):
                print(f"Portfel {wallet} odrzucony (częste transakcje tokena).")
                continue
            
            if not self.check_wallet_general_frequency(wallet):
                print(f"Portfel {wallet} odrzucony (częste transakcje adresu).")
                continue
            
            filtered_wallets.append(wallet)
        
        return filtered_wallets
    
    def analyze_wallet_balances(self, wallets: List[str], 
                               wallet_transactions: Dict[str, List[Dict[str, Any]]],
                               t1_unix: int, t2_unix: int, t3_unix: int,
                               exchange_rate: Optional[float], native_to_usd_rate: Optional[float]) -> List[Dict[str, Any]]:
        
        results = []
        
        for wallet in wallets:
            txs = wallet_transactions.get(wallet, [])
            purchased, final_balance, purchase_count, sale_count = self.simulate_wallet_balance(
                wallet, txs, t1_unix, t2_unix, t3_unix
            )
            
            if purchased == 0:
                continue
                
            percentage = (final_balance / purchased) * 100
            if final_balance < self.min_balance_percentage * purchased:
                continue
            
            if exchange_rate is not None and native_to_usd_rate is not None:
                native_value = round(final_balance * exchange_rate, 2)
                usd_value = round(native_value * native_to_usd_rate, 2)
            else:
                native_value = None
                usd_value = None

            if usd_value is not None and usd_value < ApiConstants.MIN_USD_VALUE:
                print(f"Portfel {wallet} odrzucony ({usd_value} USD < {ApiConstants.MIN_USD_VALUE} USD).")
                continue
            
            results.append({
                "wallet": wallet,
                "purchase_count": purchase_count,
                "sale_count": sale_count,
                "percentage": f"{percentage:.2f}%",
                "native_value": native_value,
                "usd_value": usd_value,
                "purchased": purchased,
                "final_balance": final_balance,
            })
        
        return results