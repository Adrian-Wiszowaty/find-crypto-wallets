import time
import os
import json
import logging
from shared.constants import Constants

API_KEY_USED = ""
API_URL = ""

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WALLETS_FOLDER = os.path.join(BASE_DIR, Constants.FOLDER_WALLETS)
CACHE_FOLDER = os.path.join(BASE_DIR, Constants.FOLDER_CACHE)
LOGS_FOLDER = os.path.join(BASE_DIR, Constants.FOLDER_LOGS)
CACHE_FILE = os.path.join(CACHE_FOLDER, Constants.FILE_WALLET_CACHE)

def load_json_config(config_file=os.path.join(BASE_DIR, Constants.FOLDER_CONFIG, Constants.FILE_CONFIG)):
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{Constants.ERROR_CONFIG_NOT_FOUND} {config_file}")
    except Exception as e:
        print(f"Wystąpił błąd podczas ładowania pliku {config_file}: {e}")
    return {}

config = load_json_config()

NETWORK = config.get("NETWORK", Constants.DEFAULT_CONFIG["NETWORK"])
T1_STR = config.get("T1_STR", Constants.DEFAULT_CONFIG["T1_STR"])
T2_STR = config.get("T2_STR", Constants.DEFAULT_CONFIG["T2_STR"])
T3_STR = config.get("T3_STR", Constants.DEFAULT_CONFIG["T3_STR"])
TOKEN_CONTRACT_ADDRESS = config.get("TOKEN_CONTRACT_ADDRESS", Constants.DEFAULT_CONFIG["TOKEN_CONTRACT_ADDRESS"])

API_KEY_USED = Constants.ETHERSCAN_API_KEY

network_config = Constants.get_network_config(NETWORK)
API_URL = network_config["api_url"]
NATIVE_TOKEN_NAME = network_config["native_token_name"]
NATIVE_TOKEN_FULL_NAME = network_config["native_token_full_name"]
NATIVE_ADDRESS = network_config["native_address"]

if NETWORK == "BASE":
    BASE_NATIVE_ADDRESS = Constants.WETH_ADDRESS_BASE
    WETH_ADDRESS = BASE_NATIVE_ADDRESS
elif NETWORK == "ETH":
    WETH_ADDRESS = Constants.WETH_ADDRESS_ETH
else:
    WBNB_ADDRESS = Constants.WBNB_ADDRESS_BSC

LOG_FILE = os.path.join(LOGS_FOLDER, Constants.FILE_ERROR_LOG)

os.makedirs(WALLETS_FOLDER, exist_ok=True)
os.makedirs(LOGS_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)
logging.getLogger().setLevel(logging.ERROR)

start_time = time.time()

def main():
    
    try:
        from .config_manager import ConfigManager
        from .api_client import ApiClient
        from .blockchain_analyzer import BlockchainAnalyzer
        from .wallet_analyzer import WalletAnalyzer
        from .excel_reporter import ExcelReporter
        from .exchange_rate_service import ExchangeRateService
        from .cache_manager import CacheManager
        from shared.datetime_helper import DateTimeHelper
        
        fresh_config = load_json_config()
        current_network = fresh_config.get("NETWORK", Constants.DEFAULT_CONFIG["NETWORK"])
        current_t1_str = fresh_config.get("T1_STR", Constants.DEFAULT_CONFIG["T1_STR"])
        current_t2_str = fresh_config.get("T2_STR", Constants.DEFAULT_CONFIG["T2_STR"])
        current_t3_str = fresh_config.get("T3_STR", Constants.DEFAULT_CONFIG["T3_STR"])
        current_token_address = fresh_config.get("TOKEN_CONTRACT_ADDRESS", Constants.DEFAULT_CONFIG["TOKEN_CONTRACT_ADDRESS"])
        
        print(f"Wybrana sieć: {current_network}")
        
        config_manager = ConfigManager()
        api_client = ApiClient(config_manager)
        blockchain_analyzer = BlockchainAnalyzer(api_client)
        cache_manager = CacheManager(config_manager)
        exchange_rate_service = ExchangeRateService(config_manager)
        
        token_name = exchange_rate_service.get_token_name(current_token_address)
        if token_name != "error":
            print(f"Wybrany token: {token_name}")
        else:
            print(f"Wybrany token: {current_token_address} (nie udało się pobrać nazwy)")
            token_name = current_token_address
                
        wallet_analyzer = WalletAnalyzer(config_manager, api_client)
        excel_reporter = ExcelReporter(config_manager)
        
        try:
            DateTimeHelper.validate_date_range(current_t1_str, current_t2_str, current_t3_str)
        except ValueError as e:
            print(f"Błąd walidacji dat: {e}")
            raise
        
        t1_unix = DateTimeHelper.parse_date(current_t1_str)
        t2_unix = DateTimeHelper.parse_date(current_t2_str)
        t3_unix = DateTimeHelper.parse_date(current_t3_str)
        print(f"T1: {t1_unix}, T2: {t2_unix}, T3: {t3_unix}")
        
        start_block = blockchain_analyzer.get_block_by_timestamp(t1_unix, closest="after")
        end_block = blockchain_analyzer.get_block_by_timestamp(t3_unix, closest="before")
        print(f"Zakres bloków: {start_block} - {end_block}")
        
        all_transactions = blockchain_analyzer.get_token_transactions(start_block, end_block, current_token_address)
        print(f"Pobrano łącznie {len(all_transactions)} transakcji tokena.")
        
        txs_in_period = blockchain_analyzer.filter_transactions_by_timerange(all_transactions, t1_unix, t3_unix)
        print(f"Transakcje w okresie T1-T3: {len(txs_in_period)}")
        
        wallet_transactions = blockchain_analyzer.group_transactions_by_wallet(txs_in_period)
        
        candidate_wallets = blockchain_analyzer.find_candidate_wallets(txs_in_period, t1_unix, t2_unix)
        print(f"Znaleziono {len(candidate_wallets)} kandydatów (portfeli z zakupem w okresie T1-T2).")
        print(f"---")
        
        filtered_wallets = wallet_analyzer.filter_wallets_by_frequency(
            candidate_wallets, 
            wallet_transactions,
            blockchain_analyzer
        )
        print(f"---")
        print(f"Portfeli po weryfikacji: {len(filtered_wallets)}")
        
        exchange_rate = exchange_rate_service.get_exchange_rate(current_token_address, retries=5)
        if exchange_rate == "error":
            print("Nie udało się pobrać kursu wymiany tokena. Wartość natywna ustawiona jako 'error'.")
        
        current_network_config = Constants.get_network_config(current_network)
        current_native_token_name = current_network_config["native_token_name"]
        
        native_to_usd_rate = exchange_rate_service.get_native_to_usd_rate()
        if native_to_usd_rate == "error":
            print("Nie udało się pobrać kursu wymiany natywnego tokena do USD.")
        else:
            print(f"Kurs wymiany {current_native_token_name} -> USD: {native_to_usd_rate}")

        token_usd_rate = exchange_rate_service.get_token_usd_rate(current_token_address, retries=5)
        if token_usd_rate == "error":
            print("Nie udało się pobrać kursu tokena do USD.")
        else:
            print(f"Kurs wymiany tokena -> USD na dzień T3: ${token_usd_rate:.6f}")
        
        print(f"---")

        final_results = wallet_analyzer.analyze_wallet_balances(
            filtered_wallets,
            wallet_transactions,
            t1_unix, t2_unix, t3_unix,
            exchange_rate, native_to_usd_rate
        )
        print(f"---")
        print(f"Portfeli po filtracji: {len(final_results)}")
        
        cache_manager.save_frequency_cache(wallet_analyzer.frequency_cache)
        
        output_filename = excel_reporter.generate_report(final_results, token_name, current_t1_str, current_t2_str, current_t3_str)
        print(f"Raport zapisany do katalogu 'wallets'")

        elapsed_time = time.time() - start_time
        execution_time_formatted = DateTimeHelper.format_execution_time(elapsed_time)
        print(f"Czas wykonania skryptu do momentu zapisu pliku: {execution_time_formatted}")
        
    except Exception as e:
        logging.error(f"Błąd głównej funkcji: {e}")
        print("Wystąpił krytyczny błąd. Sprawdź logi w pliku:", LOG_FILE)
        raise

if __name__ == "__main__":
    main()
