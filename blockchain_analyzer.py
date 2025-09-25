"""
Klasa odpowiedzialna za analizę blockchain i operacje związane z blokami.
"""
import time
import logging
from typing import List, Dict, Any, Tuple
from api_client import ApiClient
from constants import Constants


class BlockchainAnalyzer:
    """Zarządza operacjami związanymi z analizą blockchain i blokami"""
    
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client
        
    @staticmethod
    def divide_blocks_into_chunks(start_block: int, end_block: int, chunk_size: int) -> List[Tuple[int, int]]:
        """
        Funkcja pomocnicza do podziału zakresu bloków na paczki.
        
        Args:
            start_block: Początkowy blok
            end_block: Końcowy blok  
            chunk_size: Rozmiar pojedynczej paczki
            
        Returns:
            List[Tuple[int, int]]: Lista krotek (start, end) dla każdej paczki
        """
        chunks = []
        current_start = start_block
        
        while current_start <= end_block:
            current_end = min(current_start + chunk_size - 1, end_block)
            chunks.append((current_start, current_end))
            current_start = current_end + 1
            
        return chunks
    
    def get_block_by_timestamp(self, timestamp: int, closest: str = "before") -> int:
        """
        Pobiera numer bloku na podstawie znacznika czasu.
        
        Args:
            timestamp: Unix timestamp
            closest: "before" lub "after" - który blok wybrać
            
        Returns:
            int: Numer bloku
            
        Raises:
            Exception: Gdy nie udało się pobrać numeru bloku
        """
        params = {
            "module": "block",
            "action": "getblocknobytime", 
            "timestamp": timestamp,
            "closest": closest,
            "apikey": self.api_client.api_key
        }
        
        try:
            data = self.api_client._make_request_with_retry(
                self.api_client.api_url, 
                params
            )
            
            if not data or "result" not in data:
                raise Exception(f"Niepoprawna odpowiedź API dla timestamp {timestamp}")
                
            block_number = int(data["result"])
            return block_number
            
        except Exception as e:
            error_msg = f"Nie udało się pobrać numeru bloku dla timestamp {timestamp}: {e}"
            logging.error(error_msg)
            raise Exception(error_msg)
    
    def get_token_transactions(self, startblock: int, endblock: int, token_contract_address: str) -> List[Dict[str, Any]]:
        """
        Pobiera transakcje tokena z zakresu bloków startblock-endblock.
        
        Args:
            startblock: Początkowy blok
            endblock: Końcowy blok
            token_contract_address: Adres kontraktu tokena
            
        Returns:
            List[Dict[str, Any]]: Lista transakcji tokena
        """
        all_txs = []
        current_start = startblock
        
        while current_start <= endblock:
            current_end = min(current_start + Constants.BLOCK_CHUNK_SIZE - 1, endblock)
            
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
                data = self.api_client._make_request_with_retry(
                    self.api_client.api_url, 
                    params
                )
                
                if data and "result" in data and isinstance(data["result"], list):
                    txs = data["result"]
                    print(f"Liczba transakcji w odpowiedzi: {len(txs)}")
                    all_txs.extend(txs)
                else:
                    logging.error(f"Niepoprawny format odpowiedzi API dla bloków {current_start}-{current_end}: {data}")
                    
            except Exception as e:
                logging.error(f"Błąd podczas przetwarzania danych dla bloków {current_start}-{current_end}: {e}")
            finally:
                current_start = current_end + 1
                time.sleep(Constants.DELAY_BETWEEN_REQUESTS)
        
        return all_txs
    
    def get_wallet_transactions(self, wallet: str, count: int = 10, retries: int = None) -> List[Dict[str, Any]]:
        """
        Pobiera ostatnie 'count' transakcji dla danego portfela, niezależnie od tokena,
        korzystając z endpointu txlist.
        
        Args:
            wallet: Adres portfela
            count: Liczba transakcji do pobrania
            retries: Liczba prób (domyślnie z Constants)
            
        Returns:
            List[Dict[str, Any]]: Lista ostatnich transakcji portfela
        """
        if retries is None:
            retries = Constants.MAX_RETRIES
            
        params = {
            "module": "account",
            "action": "txlist",
            "address": wallet,
            "page": 1,
            "offset": count,
            "sort": "desc",
            "apikey": self.api_client.api_key
        }
        
        try:
            data = self.api_client._make_request_with_retry(
                self.api_client.api_url, 
                params, 
                retries
            )
            
            if data and "result" in data and isinstance(data["result"], list):
                return data["result"]
            else:
                logging.error(f"Nieoczekiwany format odpowiedzi przy pobieraniu transakcji portfela {wallet}: {data}")
                return []
                
        except Exception as e:
            logging.error(f"Błąd przy pobieraniu transakcji portfela {wallet}: {e}")
            return []
    
    def filter_transactions_by_timerange(self, transactions: List[Dict[str, Any]], 
                                       start_timestamp: int, end_timestamp: int) -> List[Dict[str, Any]]:
        """
        Filtruje transakcje według przedziału czasowego.
        
        Args:
            transactions: Lista transakcji
            start_timestamp: Początkowy timestamp
            end_timestamp: Końcowy timestamp
            
        Returns:
            List[Dict[str, Any]]: Przefiltrowane transakcje
        """
        filtered = []
        
        for tx in transactions:
            try:
                tx_timestamp = int(tx["timeStamp"])
                if start_timestamp <= tx_timestamp <= end_timestamp:
                    filtered.append(tx)
            except (ValueError, KeyError) as e:
                logging.warning(f"Pomiń transakcję z niepoprawnym timestamp: {tx}, błąd: {e}")
                continue
        
        # Sortuj według timestamp
        filtered.sort(key=lambda tx: int(tx["timeStamp"]))
        return filtered
    
    def group_transactions_by_wallet(self, transactions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Grupuje transakcje według adresów portfeli (zarówno from jak i to).
        
        Args:
            transactions: Lista transakcji
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Słownik {adres_portfela: [transakcje]}
        """
        wallet_transactions = {}
        
        for tx in transactions:
            try:
                wallet_from = tx["from"].lower()
                wallet_to = tx["to"].lower()
                
                # Dodaj transakcję do obu portfeli (nadawcy i odbiorcy)
                if wallet_from not in wallet_transactions:
                    wallet_transactions[wallet_from] = []
                if wallet_to not in wallet_transactions:
                    wallet_transactions[wallet_to] = []
                    
                wallet_transactions[wallet_from].append(tx)
                wallet_transactions[wallet_to].append(tx)
                
            except KeyError as e:
                logging.warning(f"Pomiń transakcję z brakującymi polami: {tx}, błąd: {e}")
                continue
        
        return wallet_transactions
    
    def find_candidate_wallets(self, transactions: List[Dict[str, Any]], 
                             purchase_start: int, purchase_end: int) -> List[str]:
        """
        Znajduje portfele które dokonały zakupu w określonym okresie (T1-T2).
        
        Args:
            transactions: Lista wszystkich transakcji
            purchase_start: Początek okresu zakupów (timestamp)
            purchase_end: Koniec okresu zakupów (timestamp)
            
        Returns:
            List[str]: Lista adresów kandydujących portfeli
        """
        candidate_wallets = []
        
        for tx in transactions:
            try:
                tx_timestamp = int(tx["timeStamp"])
                wallet_to = tx["to"].lower()
                
                # Sprawdź czy transakcja jest w okresie zakupów (T1-T2)
                if (purchase_start <= tx_timestamp <= purchase_end and 
                    wallet_to not in candidate_wallets):
                    candidate_wallets.append(wallet_to)
                    
            except (ValueError, KeyError) as e:
                logging.warning(f"Pomiń transakcję kandydata: {tx}, błąd: {e}")
                continue
        
        return candidate_wallets