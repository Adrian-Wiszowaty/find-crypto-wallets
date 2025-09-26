"""
Klasa odpowiedzialna za analizę portfeli kryptowalut.
"""
import json
import os
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timezone, timedelta
from config_manager import ConfigManager
from api_client import ApiClient
from constants import Constants


class WalletAnalyzer:
    """Analizuje portfele kryptowalut pod kątem wzorców transakcji i salda"""
    
    def __init__(self, config_manager: ConfigManager, api_client: ApiClient):
        self.config_manager = config_manager
        self.api_client = api_client
        self.frequency_interval_seconds = Constants.FREQUENCY_INTERVAL_SECONDS
        self.min_frequency_violations = Constants.MIN_FREQUENCY_VIOLATIONS
        self.min_transaction_count = Constants.MIN_TRANSACTION_COUNT
        self.min_usd_value = Constants.MIN_USD_VALUE
        
        # Cache dla weryfikacji częstotliwości
        paths = config_manager.get_paths_config()
        self.cache_file = paths["cache_file"]
        self.frequency_cache = self._load_frequency_cache()
    
    def _load_frequency_cache(self) -> Dict[str, bool]:
        """Ładuje cache weryfikacji częstotliwości z pliku"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading frequency cache: {e}")
        
        return {}
    
    def save_frequency_cache(self) -> None:
        """Zapisuje cache weryfikacji częstotliwości do pliku"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.frequency_cache, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving frequency cache: {e}")
    
    def parse_date(self, date_str: str) -> int:
        """Konwertuje datę w formacie DD-MM-YYYY H:M:S do znacznika unixowego"""
        try:
            dt = datetime.strptime(date_str, Constants.DATE_FORMAT)
            dt = dt - timedelta(hours=Constants.TIMEZONE_OFFSET_HOURS)
            dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except Exception as e:
            logging.error(f"{Constants.ERROR_INVALID_DATE_FORMAT} {date_str}: {e}")
            raise
    
    def _check_transaction_frequency(self, transactions: List[Dict[str, Any]]) -> bool:
        """Sprawdza częstotliwość transakcji w liście"""
        if len(transactions) < 2:
            return True  # Za mało transakcji do analizy
        
        # Sortowanie od najnowszej do najstarszej
        sorted_txs = sorted(transactions, key=lambda x: int(x["timeStamp"]), reverse=True)
        
        violations = 0
        for i in range(len(sorted_txs) - 1):
            t1 = int(sorted_txs[i]["timeStamp"])
            t2 = int(sorted_txs[i + 1]["timeStamp"])
            
            if (t1 - t2) < self.frequency_interval_seconds:
                violations += 1
        
        return violations < self.min_frequency_violations
    
    def check_wallet_token_frequency(self, wallet: str, wallet_transactions: List[Dict[str, Any]]) -> bool:
        """Sprawdza częstotliwość transakcji tokena dla portfela"""
        if wallet in self.frequency_cache:
            return False  # Portfel już oznaczony jako podejrzany
        
        if len(wallet_transactions) < self.min_transaction_count:
            return True  # Za mało transakcji do analizy
        
        # Bierzemy ostatnie 10 transakcji tokena
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
        """Sprawdza częstotliwość wszystkich transakcji portfela"""
        if wallet in self.frequency_cache:
            return False
        
        # Pobieramy ostatnie 10 transakcji wszystkich typów
        all_transactions = self.api_client.get_wallet_transactions(wallet, count=10)
        
        if not self._check_transaction_frequency(all_transactions):
            self.frequency_cache[wallet] = True
            return False
        
        return True
    
    def simulate_wallet_balance(self, wallet: str, wallet_transactions: List[Dict[str, Any]], 
                               t1_unix: int, t2_unix: int, t3_unix: int) -> Tuple[float, float, int, int]:
        """
        Symuluje saldo tokenów portfela w okresie od T1 do T3.
        Zwraca: (zakupione_tokeny, końcowe_saldo, liczba_zakupów, liczba_sprzedaży)
        """
        purchased = 0.0
        balance = 0.0
        purchase_count = 0
        sale_count = 0
        
        wallet_lower = wallet.lower()
        
        for tx in wallet_transactions:
            timestamp = int(tx["timeStamp"])
            
            # Sprawdzamy czy transakcja jest w zakresie T1-T3
            if not (t1_unix <= timestamp <= t3_unix):
                continue
            
            try:
                token_decimals = int(tx.get("tokenDecimal", "0"))
                amount = float(tx["value"]) / (10 ** token_decimals)
            except (ValueError, TypeError) as e:
                logging.error(f"Error calculating transaction amount: {tx} - {e}")
                continue
            
            # Transakcja przychodzą (zakup)
            if tx["to"].lower() == wallet_lower:
                balance += amount
                # Jeśli zakup był w okresie T1-T2, liczymy jako "purchased"
                if t1_unix <= timestamp <= t2_unix:
                    purchased += amount
                    purchase_count += 1
            
            # Transakcja wychodząca (sprzedaż)
            elif tx["from"].lower() == wallet_lower:
                balance -= amount
                sale_count += 1
        
        return round(purchased, 2), round(balance, 2), purchase_count, sale_count
    
    def calculate_wallet_value(self, final_balance: float, token_address: str) -> Tuple[Any, Any]:
        """
        Oblicza wartość portfela w native token i USD.
        Zwraca: (native_value, usd_value)
        """
        # Pobieramy kurs tokena do native tokena
        token_rate = self.api_client.get_token_price_from_dexscreener(token_address)
        if token_rate == "error":
            return "error", "error"
        
        # Pobieramy kurs native tokena do USD
        native_usd_rate = self.api_client.get_native_token_usd_price()
        if native_usd_rate == "error":
            return "error", "error"
        
        try:
            native_value = round(final_balance * float(token_rate), 2)
            usd_value = round(native_value * float(native_usd_rate), 2)
            return native_value, usd_value
        except (ValueError, TypeError) as e:
            logging.error(f"Error calculating wallet value: {e}")
            return "error", "error"
    
    def filter_wallets_by_criteria(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtruje portfele według kryteriów biznesowych"""
        filtered_results = []
        
        for result in results:
            # Sprawdzamy czy zakupił jakiekolwiek tokeny
            if result["purchased"] == 0:
                continue
            
            # Sprawdzamy czy zachował przynajmniej 50% tokenów
            percentage = (result["final_balance"] / result["purchased"]) * 100
            if result["final_balance"] < 0.5 * result["purchased"]:
                continue
            
            # Sprawdzamy minimalną wartość USD (jeśli dostępna)
            if (result["usd_value"] != "error" and 
                isinstance(result["usd_value"], (int, float)) and 
                result["usd_value"] < self.min_usd_value):
                print(f"Wallet {result['wallet']} rejected ({result['usd_value']} USD < {self.min_usd_value} USD)")
                continue
            
            # Dodajemy procent do wyników
            result["percentage"] = f"{percentage:.2f}%"
            filtered_results.append(result)
        
        return filtered_results
    
    def analyze_transactions(self, transactions: List[Dict[str, Any]], 
                           t1_unix: int, t2_unix: int, t3_unix: int) -> Tuple[List[str], Dict[str, List[Dict[str, Any]]]]:
        """
        Analizuje transakcje i zwraca kandydatów na portfele oraz ich transakcje.
        Zwraca: (lista_portfeli_kandydatów, słownik_transakcji_portfeli)
        """
        # Filtrujemy transakcje do okresu T1-T3
        period_transactions = [
            tx for tx in transactions 
            if t1_unix <= int(tx["timeStamp"]) <= t3_unix
        ]
        
        print(f"Transactions in period T1-T3: {len(period_transactions)}")
        
        # Grupujemy transakcje według portfeli
        wallet_transactions = {}
        candidate_wallets = set()
        
        for tx in period_transactions:
            wallet_from = tx["from"].lower()
            wallet_to = tx["to"].lower()
            tx_timestamp = int(tx["timeStamp"])
            
            # Dodajemy transakcje do grup portfeli
            for wallet in [wallet_from, wallet_to]:
                if wallet not in wallet_transactions:
                    wallet_transactions[wallet] = []
                wallet_transactions[wallet].append(tx)
            
            # Jeśli to zakup w okresie T1-T2, dodajemy do kandydatów
            if t1_unix <= tx_timestamp <= t2_unix:
                candidate_wallets.add(wallet_to)
        
        return list(candidate_wallets), wallet_transactions
    
    def filter_wallets_by_frequency(self, candidate_wallets: List[str], 
                                   wallet_transactions: Dict[str, List[Dict[str, Any]]],
                                   blockchain_analyzer) -> List[str]:
        """
        Filtruje portfele na podstawie częstotliwości transakcji.
        
        Args:
            candidate_wallets: Lista kandydujących portfeli
            wallet_transactions: Słownik transakcji dla każdego portfela
            blockchain_analyzer: Instancja BlockchainAnalyzer dla pobierania transakcji
            
        Returns:
            List[str]: Lista przefiltrowanych portfeli
        """
        filtered_wallets = []
        total_wallets = len(candidate_wallets)
        
        for index, wallet in enumerate(candidate_wallets, start=1):
            print(f"{index}/{total_wallets}: {wallet}")
            
            # Sprawdź czy portfel już jest w cache
            if wallet in self.frequency_cache:
                print(f"Portfel {wallet} odrzucony (był w cache).")
                continue
            
            # Sprawdź częstotliwość na podstawie transakcji tokena
            txs = wallet_transactions.get(wallet, [])
            if not self.check_wallet_token_frequency(wallet, txs):
                print(f"Portfel {wallet} odrzucony (częste transakcje tokena).")
                continue
            
            # Sprawdź częstotliwość na podstawie wszystkich transakcji portfela
            if not self.check_wallet_general_frequency(wallet):
                print(f"Portfel {wallet} odrzucony (częste transakcje adresu).")
                continue
            
            filtered_wallets.append(wallet)
        
        return filtered_wallets
    
    def analyze_wallet_balances(self, wallets: List[str], 
                               wallet_transactions: Dict[str, List[Dict[str, Any]]],
                               t1_unix: int, t2_unix: int, t3_unix: int,
                               exchange_rate, native_to_usd_rate) -> List[Dict[str, Any]]:
        """
        Analizuje salda portfeli i zwraca finalne wyniki.
        
        Args:
            wallets: Lista portfeli do analizy
            wallet_transactions: Słownik transakcji dla każdego portfela
            t1_unix, t2_unix, t3_unix: Timestamps okresów czasowych
            exchange_rate: Kurs wymiany tokena
            native_to_usd_rate: Kurs natywnego tokena do USD
            
        Returns:
            List[Dict[str, Any]]: Lista wyników analizy portfeli
        """
        results = []
        
        for wallet in wallets:
            txs = wallet_transactions.get(wallet, [])
            purchased, final_balance, purchase_count, sale_count = self.simulate_wallet_balance(
                wallet, txs, t1_unix, t2_unix, t3_unix
            )
            
            if purchased == 0:
                continue
                
            percentage = (final_balance / purchased) * 100
            if final_balance < 0.5 * purchased:
                continue
            
            # Oblicz wartości w natywnym tokenie i USD
            if exchange_rate != "error" and native_to_usd_rate != "error":
                native_value = round(final_balance * exchange_rate, 2)
                usd_value = round(native_value * native_to_usd_rate, 2)
            else:
                native_value = "error"
                usd_value = "error"
            
            # Sprawdź minimalną wartość USD
            if usd_value != "error" and usd_value < Constants.MIN_USD_VALUE:
                print(f"Portfel {wallet} odrzucony ({usd_value} USD < {Constants.MIN_USD_VALUE} USD).")
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