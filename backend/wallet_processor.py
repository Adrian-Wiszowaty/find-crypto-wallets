import time
import os
import json
import logging
from shared.constants.config_constants import ConfigConstants
from shared.constants.file_constants import FileConstants
from shared.constants.message_constants import MessageConstants

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WALLETS_FOLDER = os.path.join(BASE_DIR, FileConstants.FOLDER_WALLETS)
CACHE_FOLDER = os.path.join(BASE_DIR, FileConstants.FOLDER_CACHE)
LOGS_FOLDER = os.path.join(BASE_DIR, FileConstants.FOLDER_LOGS)
LOG_FILE = os.path.join(LOGS_FOLDER, FileConstants.FILE_ERROR_LOG)

def load_json_config(config_file=os.path.join(BASE_DIR, FileConstants.FOLDER_CONFIG, FileConstants.FILE_CONFIG)):
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{MessageConstants.ERROR_CONFIG_NOT_FOUND} {config_file}")
    except Exception as e:
        print(f"An error occurred while loading file {config_file}: {e}")
    return {}

def _setup_environment():
    os.makedirs(WALLETS_FOLDER, exist_ok=True)
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    os.makedirs(CACHE_FOLDER, exist_ok=True)

    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
        force=True
    )

def main():

    _setup_environment()
    start_time = time.time()

    try:
        from .config_manager import ConfigManager
        from .api_client import ApiClient
        from .blockchain_analyzer import BlockchainAnalyzer
        from .wallet_analyzer import WalletAnalyzer
        from .excel_reporter import ExcelReporter
        from .exchange_rate_service import ExchangeRateService
        from shared.datetime_helper import DateTimeHelper

        fresh_config = load_json_config()
        current_network = fresh_config.get("NETWORK", ConfigConstants.DEFAULT_CONFIG["NETWORK"])
        current_t1_str = fresh_config.get("T1_STR", ConfigConstants.DEFAULT_CONFIG["T1_STR"])
        current_t2_str = fresh_config.get("T2_STR", ConfigConstants.DEFAULT_CONFIG["T2_STR"])
        current_t3_str = fresh_config.get("T3_STR", ConfigConstants.DEFAULT_CONFIG["T3_STR"])
        current_token_address = fresh_config.get("TOKEN_CONTRACT_ADDRESS", ConfigConstants.DEFAULT_CONFIG["TOKEN_CONTRACT_ADDRESS"])

        print(f"Wybrana sieć: {current_network}")

        config_manager = ConfigManager()
        api_client = ApiClient(config_manager)
        blockchain_analyzer = BlockchainAnalyzer(api_client)
        exchange_rate_service = ExchangeRateService(config_manager, api_client)

        token_name = exchange_rate_service.get_token_name(current_token_address)
        if token_name is not None:
            print(f"Wybrany token: {token_name}")
        else:
            print(f"Wybrany token: {current_token_address} (nie udało się pobrać nazwy)")
            token_name = current_token_address

        wallet_analyzer = WalletAnalyzer(config_manager, api_client)
        excel_reporter = ExcelReporter(config_manager)

        try:
            DateTimeHelper.validate_date_range(current_t1_str, current_t2_str, current_t3_str)
        except ValueError as e:
            print(f"Date validation error: {e}")
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
        print("---")

        filtered_wallets = wallet_analyzer.filter_wallets_by_frequency(
            candidate_wallets,
            wallet_transactions,
            blockchain_analyzer
        )
        print("---")
        print(f"Portfeli po weryfikacji: {len(filtered_wallets)}")

        exchange_rate = exchange_rate_service.get_exchange_rate(current_token_address, retries=5)
        if exchange_rate is None:
            print("Nie udało się pobrać kursu wymiany tokena. Wartość natywna nie zostanie obliczona.")

        current_network_config = ConfigManager.get_network_config_by_name(current_network)
        current_native_token_name = current_network_config["native_token_name"]

        native_to_usd_rate = exchange_rate_service.get_native_to_usd_rate()
        if native_to_usd_rate is None:
            print("Nie udało się pobrać kursu wymiany natywnego tokena do USD.")
        else:
            print(f"Kurs wymiany {current_native_token_name} -> USD: {native_to_usd_rate}")

        token_usd_rate = exchange_rate_service.get_token_usd_rate(current_token_address, retries=5)
        if token_usd_rate is None:
            print("Nie udało się pobrać kursu tokena do USD.")
        else:
            print(f"Kurs wymiany tokena -> USD na dzień T3: ${token_usd_rate:.6f}")

        print("---")

        final_results = wallet_analyzer.analyze_wallet_balances(
            filtered_wallets,
            wallet_transactions,
            t1_unix, t2_unix, t3_unix,
            exchange_rate, native_to_usd_rate
        )
        print("---")
        print(f"Portfeli po filtracji: {len(final_results)}")

        wallet_analyzer.save_frequency_cache()

        output_filename = excel_reporter.generate_report(final_results, token_name, current_t1_str, current_t2_str, current_t3_str)
        print(f"Raport zapisany do: {output_filename}")

        elapsed_time = time.time() - start_time
        execution_time_formatted = DateTimeHelper.format_execution_time(elapsed_time)
        print(f"Czas wykonania skryptu do momentu zapisu pliku: {execution_time_formatted}")

    except Exception as e:
        logging.error(f"Main function error: {e}")
        print("A critical error occurred. Check the logs in:", LOG_FILE)
        raise

if __name__ == "__main__":
    main()
