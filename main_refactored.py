#!/usr/bin/env python3
"""
Zrefaktoryzowana główna aplikacja do znajdowania portfeli kryptowalut.
Wykorzystuje podział na klasy zgodnie z dobrymi praktykami programowania.
"""
import logging
import time
from typing import List, Dict, Any

from config_manager import ConfigManager
from api_client import ApiClient
from wallet_analyzer import WalletAnalyzer
from excel_reporter import ExcelReporter


class WalletFinder:
    """Główna klasa aplikacji do znajdowania portfeli kryptowalut"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self._setup_logging()
        self._setup_directories()
        
        # Inicjalizacja komponentów
        self.api_client = ApiClient(self.config_manager)
        self.wallet_analyzer = WalletAnalyzer(self.config_manager, self.api_client)
        self.excel_reporter = ExcelReporter(self.config_manager)
        
        # Czas startu dla pomiaru wydajności
        self.start_time = time.time()
    
    def _setup_logging(self) -> None:
        """Konfiguruje system logowania"""
        paths = self.config_manager.get_paths_config()
        
        logging.basicConfig(
            filename=paths["log_file"],
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )
    
    def _setup_directories(self) -> None:
        """Tworzy wymagane katalogi"""
        self.config_manager.ensure_directories()
    
    def _validate_configuration(self) -> bool:
        """Waliduje konfigurację przed uruchomieniem"""
        if not self.config_manager.validate_config():
            print("❌ Błędna konfiguracja. Sprawdź ustawienia.")
            return False
        
        return True
    
    def _get_time_periods(self) -> tuple:
        """Pobiera i konwertuje okresy czasowe z konfiguracji"""
        t1_str = self.config_manager.get("T1_STR")
        t2_str = self.config_manager.get("T2_STR")
        t3_str = self.config_manager.get("T3_STR")
        
        t1_unix = self.wallet_analyzer.parse_date(t1_str)
        t2_unix = self.wallet_analyzer.parse_date(t2_str)
        t3_unix = self.wallet_analyzer.parse_date(t3_str)
        
        print(f"Okresy czasowe - T1: {t1_unix}, T2: {t2_unix}, T3: {t3_unix}")
        return t1_unix, t2_unix, t3_unix
    
    def _fetch_blockchain_data(self, t1_unix: int, t3_unix: int) -> List[Dict[str, Any]]:
        """Pobiera dane z blockchain dla danego okresu"""
        token_address = self.config_manager.get("TOKEN_CONTRACT_ADDRESS")
        
        print("🔍 Pobieranie bloków dla zadanych timestampów...")
        start_block = self.api_client.get_block_by_timestamp(t1_unix, closest="after")
        end_block = self.api_client.get_block_by_timestamp(t3_unix, closest="before")
        
        print(f"📦 Zakres bloków: {start_block} - {end_block}")
        
        print("🔄 Pobieranie transakcji tokena...")
        all_transactions = self.api_client.get_token_transactions(
            token_address, start_block, end_block
        )
        
        print(f"📊 Pobrano łącznie {len(all_transactions)} transakcji tokena")
        return all_transactions
    
    def _analyze_wallets(self, transactions: List[Dict[str, Any]], 
                        t1_unix: int, t2_unix: int, t3_unix: int) -> List[str]:
        """Analizuje portfele i zwraca listę zatwierdzonych kandydatów"""
        print("🔎 Analizowanie transakcji w poszukiwaniu kandydatów...")
        
        # Znajdź kandydatów i pogrupuj ich transakcje
        candidates, wallet_transactions = self.wallet_analyzer.analyze_transactions(
            transactions, t1_unix, t2_unix, t3_unix
        )
        
        print(f"👥 Znaleziono {len(candidates)} kandydatów (portfele z zakupem w okresie T1-T2)")
        
        # Filtracja kandydatów
        filtered_wallets = []
        total_wallets = len(candidates)
        
        for index, wallet in enumerate(candidates, start=1):
            print(f"🔍 {index}/{total_wallets}: {wallet}")
            
            wallet_txs = wallet_transactions.get(wallet, [])
            
            # Sprawdzenie częstotliwości transakcji tokena
            if not self.wallet_analyzer.check_wallet_token_frequency(wallet, wallet_txs):
                print(f"❌ Portfel {wallet} odrzucony (częste transakcje tokena)")
                continue
            
            # Sprawdzenie częstotliwości wszystkich transakcji
            if not self.wallet_analyzer.check_wallet_general_frequency(wallet):
                print(f"❌ Portfel {wallet} odrzucony (częste transakcje ogólne)")
                continue
            
            filtered_wallets.append(wallet)
        
        print(f"✅ Portfeli po weryfikacji częstotliwości: {len(filtered_wallets)}")
        
        # Zapisz cache częstotliwości
        self.wallet_analyzer.save_frequency_cache()
        
        return filtered_wallets, wallet_transactions
    
    def _calculate_wallet_results(self, filtered_wallets: List[str], 
                                wallet_transactions: Dict[str, List[Dict[str, Any]]],
                                t1_unix: int, t2_unix: int, t3_unix: int) -> List[Dict[str, Any]]:
        """Oblicza wyniki dla zatwierdzonych portfeli"""
        token_address = self.config_manager.get("TOKEN_CONTRACT_ADDRESS")
        
        print("💰 Pobieranie kursów wymiany...")
        
        # Pobierz kursy raz dla wszystkich portfeli
        print(f"📈 Pobieranie kursu tokena {token_address}...")
        token_rate = self.api_client.get_token_price_from_dexscreener(token_address)
        
        network_config = self.config_manager.get_network_config()
        native_token = network_config["native_token_name"]
        print(f"💱 Pobieranie kursu {native_token} -> USD...")
        native_usd_rate = self.api_client.get_native_token_usd_price()
        
        if token_rate == "error":
            print("⚠️ Nie udało się pobrać kursu tokena. Wartości ustawione jako 'error'.")
        else:
            print(f"📊 Kurs tokena -> {native_token}: {token_rate}")
        
        if native_usd_rate == "error":
            print("⚠️ Nie udało się pobrać kursu natywnego tokena do USD.")
        else:
            print(f"📊 Kurs {native_token} -> USD: {native_usd_rate}")
        
        results = []
        
        print("🧮 Obliczanie wyników dla portfeli...")
        for wallet in filtered_wallets:
            wallet_txs = wallet_transactions.get(wallet, [])
            
            # Symulacja salda portfela
            purchased, final_balance, purchase_count, sale_count = \
                self.wallet_analyzer.simulate_wallet_balance(
                    wallet, wallet_txs, t1_unix, t2_unix, t3_unix
                )
            
            if purchased == 0:
                continue  # Pomiń portfele bez zakupów
            
            # Oblicz wartości
            if token_rate != "error" and native_usd_rate != "error":
                try:
                    native_value = round(final_balance * float(token_rate), 2)
                    usd_value = round(native_value * float(native_usd_rate), 2)
                except (ValueError, TypeError):
                    native_value = "error"
                    usd_value = "error"
            else:
                native_value = "error"
                usd_value = "error"
            
            # Oblicz procent zachowanych tokenów
            percentage = (final_balance / purchased) * 100 if purchased > 0 else 0
            
            results.append({
                "wallet": wallet,
                "purchase_count": purchase_count,
                "sale_count": sale_count,
                "purchased": purchased,
                "final_balance": final_balance,
                "percentage": f"{percentage:.2f}%",
                "native_value": native_value,
                "usd_value": usd_value,
            })
        
        return results
    
    def _get_execution_time(self) -> str:
        """Zwraca czas wykonania w formacie MM:SS"""
        elapsed_time = time.time() - self.start_time
        minutes, seconds = divmod(elapsed_time, 60)
        return f"{int(minutes):02}:{int(seconds):02}"
    
    def run(self) -> None:
        """Główna metoda uruchamiająca analizę portfeli"""
        try:
            print("🚀 Rozpoczynanie analizy portfeli kryptowalut...")
            
            # Walidacja konfiguracji
            if not self._validate_configuration():
                return
            
            network = self.config_manager.get("NETWORK")
            token_address = self.config_manager.get("TOKEN_CONTRACT_ADDRESS")
            print(f"🌐 Wybrana sieć: {network}")
            print(f"🪙 Adres tokena: {token_address}")
            
            # Pobranie okresów czasowych
            t1_unix, t2_unix, t3_unix = self._get_time_periods()
            
            # Pobranie danych z blockchain
            all_transactions = self._fetch_blockchain_data(t1_unix, t3_unix)
            
            if not all_transactions:
                print("⚠️ Brak transakcji w zadanym okresie.")
                return
            
            # Analiza portfeli
            filtered_wallets, wallet_transactions = self._analyze_wallets(
                all_transactions, t1_unix, t2_unix, t3_unix
            )
            
            if not filtered_wallets:
                print("⚠️ Brak portfeli spełniających kryteria.")
                return
            
            # Obliczenie wyników
            results = self._calculate_wallet_results(
                filtered_wallets, wallet_transactions, t1_unix, t2_unix, t3_unix
            )
            
            # Filtracja końcowych wyników
            final_results = self.wallet_analyzer.filter_wallets_by_criteria(results)
            
            print(f"📋 Portfeli po ostatecznej filtracji: {len(final_results)}")
            
            # Generowanie raportu
            if final_results:
                report_path = self.excel_reporter.generate_report(final_results, token_address)
                print(f"📊 Raport zapisany w: {report_path}")
            
            # Wyświetlenie podsumowania
            execution_time = self._get_execution_time()
            self.excel_reporter.print_summary(final_results, execution_time)
            
        except KeyboardInterrupt:
            print("\\n⏹️ Analizę przerwano przez użytkownika.")
        except Exception as e:
            error_msg = f"Krytyczny błąd podczas analizy: {e}"
            logging.error(error_msg)
            print(f"❌ {error_msg}")
            
            paths = self.config_manager.get_paths_config()
            print(f"📝 Szczegóły błędu zapisane w: {paths['log_file']}")


def main():
    """Funkcja główna aplikacji"""
    finder = WalletFinder()
    finder.run()


if __name__ == "__main__":
    main()