#!/usr/bin/env python3
import requests
import time
import os
import json
import logging
from datetime import datetime, timezone
from dateutil import parser as date_parser

T1_STR = "Mar-18-2025 06:00:00 AM UTC"
T2_STR = "Mar-18-2025 11:00:00 AM UTC"
T3_STR = "Mar-18-2025 02:47:00 PM UTC"

TOKEN_CONTRACT_ADDRESS = "0xC52AA2014d70f90EDaC790F49de088A3A65C2992"

API_KEY = os.getenv("BSCSCAN_API_KEY", "")
API_URL_BASE = "https://api.bscscan.com/api"

BLOCK_CHUNK_SIZE = 1200

FREQUENCY_INTERVAL_SECONDS = 60
MIN_FREQ_VIOLATIONS = 5

DELAY_BETWEEN_REQUESTS = 0.2
MAX_RETRIES = 3

WALLETS_FOLDER = "Wallets"
LOGS_FOLDER = "Logs"

CACHE_FILE = os.path.join(WALLETS_FOLDER, "wallet_frequency_cache.json")

MIN_BNB_VALUE = 0.1

DEX_API_URL = "https://api.dexscreener.com/latest/dex/tokens/{}"
WBNB_ADDRESS = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
NATIVE_TOKEN_NAME = "BNB"

LOG_FILE = os.path.join(LOGS_FOLDER, "error_log.txt")

os.makedirs(WALLETS_FOLDER, exist_ok=True)
os.makedirs(LOGS_FOLDER, exist_ok=True)

def divide_blocks_into_chunks(start_block, end_block, chunk_size):
    chunks = []
    current_start = start_block
    while current_start <= end_block:
        current_end = min(current_start + chunk_size - 1, end_block)
        chunks.append((current_start, current_end))
        current_start = current_end + 1
    return chunks

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def parse_date(date_str):
    try:
        dt = date_parser.parse(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return int(dt.timestamp())
    except Exception as e:
        import re
        pattern = r'(\w+-\d{1,2}-\d{4})\s+(\d{1,2}:\d{2}:\d{2})\s+(AM|PM)\s+(UTC)'
        match = re.match(pattern, date_str)
        if match:
            date_part, time_part, meridiem, tz = match.groups()
            hour_str = time_part.split(':')[0]
            try:
                hour = int(hour_str)
            except ValueError:
                logging.error(f"Failed to convert the time from {time_part}")
                raise e
            if hour > 12:
                new_date_str = f"{date_part} {time_part} {tz}"
                try:
                    dt = date_parser.parse(new_date_str)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    else:
                        dt = dt.astimezone(timezone.utc)
                    return int(dt.timestamp())
                except Exception as e2:
                    logging.error(f"Failed to fix the date format: {date_str} - {e2}")
                    raise e2
        logging.error(f"Date parsing error {date_str}: {e}")
        raise e

def api_request(params):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(API_URL_BASE, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1" and "result" in data:
                    return data
                elif data.get("message") == "No transactions found":
                    return {"result": []}
                else:
                    logging.error(f"API error: {data}")
            else:
                logging.error(f"HTTP error {response.status_code}: {response.text}")
        except Exception as e:
            logging.error(f"Exception during the API request: {e}")
        time.sleep(DELAY_BETWEEN_REQUESTS * attempt)
    raise Exception("Failed to get a valid response from the API after the maximum number of attempts.")

def get_block_by_timestamp(timestamp, closest="before"):
    params = {
        "module": "block",
        "action": "getblocknobytime",
        "timestamp": timestamp,
        "closest": closest,
        "apikey": API_KEY
    }
    data = api_request(params)
    try:
        block_number = int(data["result"])
        return block_number
    except Exception as e:
        logging.error(f"Failed to fetch block number for timestamp {timestamp}: {e}")
        raise

def get_token_transactions(startblock, endblock):
    all_txs = []
    current_start = startblock
    while current_start <= endblock:
        current_end = min(current_start + BLOCK_CHUNK_SIZE - 1, endblock)
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": TOKEN_CONTRACT_ADDRESS,
            "startblock": current_start,
            "endblock": current_end,
            "sort": "asc",
            "apikey": API_KEY
        }
        print(f"Pobieram transakcje dla bloków {current_start} - {current_end}...")
        try:
            data = api_request(params)
            if "result" in data and isinstance(data["result"], list):
                txs = data["result"]
                print(f"Liczba transakcji w odpowiedzi: {len(txs)}")
                all_txs.extend(txs)
            else:
                logging.error(f"Invalid API response format for blocks {current_start}-{current_end}: {data}")
        except Exception as e:
            logging.error(f"Error processing data for blocks {current_start}-{current_end}: {e}")
        finally:
            current_start = current_end + 1
            time.sleep(DELAY_BETWEEN_REQUESTS)
    return all_txs

def load_frequency_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading cache from {CACHE_FILE}: {e}")
    return {}

def save_frequency_cache(cache):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)
    except Exception as e:
        logging.error(f"Error saving cache to {CACHE_FILE}: {e}")

def get_exchange_rate(token_address, retries=5):
    attempt = 0
    rate = None
    while attempt < retries:
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address.lower()}"
            print(f"Generated URL for token: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logging.error(f"Server response for token: {response.status_code}, body: {response.text}")
                raise Exception(f"HTTP error dla tokena: {response.status_code}")
            
            data = response.json()
            
            pairs = data.get("pairs", [])
            for pair in pairs:
                if WBNB_ADDRESS.lower() in (pair.get("baseToken", {}).get("address", "").lower(),
                                            pair.get("quoteToken", {}).get("address", "").lower()):
                    if pair.get("baseToken", {}).get("address", "").lower() == token_address.lower():
                        rate = float(pair["priceNative"])
                    elif pair.get("quoteToken", {}).get("address", "").lower() == token_address.lower():
                        rate = 1 / float(pair["priceNative"])
                    break
            
            if rate is not None:
                break
            else:
                logging.error(f"Nie znaleziono pary z WBNB dla tokena {token_address}")
                raise Exception("Brak odpowiedniej pary w danych API")
        
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} to fetch the rate failed: {e}")
            attempt += 1
            time.sleep(DELAY_BETWEEN_REQUESTS * attempt)
    
    if rate is None:
        rate = "error"
    
    return rate

def frequency_check(wallet, wallet_txs, cache):
    if wallet in cache:
        return False
    
    if len(wallet_txs) < MIN_TX_COUNT:
        return True

    sorted_txs = sorted(wallet_txs, key=lambda x: int(x["timeStamp"]), reverse=True)
    last_10 = sorted_txs[:10]
    
    violations = 0
    for i in range(len(last_10) - 1):
        t1 = int(last_10[i]["timeStamp"])
        t2 = int(last_10[i+1]["timeStamp"])
        if (t1 - t2) < FREQUENCY_INTERVAL_SECONDS:
            violations += 1
    
    if violations >= MIN_FREQ_VIOLATIONS:
        cache[wallet] = True
        return False
    
    return True

def simulate_wallet_balance(wallet, wallet_txs, t1_unix, t2_unix, t3_unix):
    purchased = 0.0
    balance = 0.0
    for tx in wallet_txs:
        ts = int(tx["timeStamp"])
        try:
            token_decimals = int(tx.get("tokenDecimal", "0"))
            amount = float(tx["value"]) / (10 ** token_decimals)
        except Exception as e:
            logging.error(f"Error recalculating transaction value: {tx} - {e}")
            continue

        if t1_unix <= ts <= t3_unix:
            if tx["to"].lower() == wallet.lower():
                balance += amount
                if t1_unix <= ts <= t2_unix:
                    purchased += amount
            elif tx["from"].lower() == wallet.lower():
                balance -= amount
    return purchased, balance

def get_output_filename():
    base_name = os.path.join(WALLETS_FOLDER, f"{TOKEN_CONTRACT_ADDRESS}.xlsx")
    if not os.path.exists(base_name):
        return base_name
    suffix = 1
    while True:
        new_name = os.path.join(WALLETS_FOLDER, f"{TOKEN_CONTRACT_ADDRESS}_{suffix}.xlsx")
        if not os.path.exists(new_name):
            return new_name
        suffix += 1

def write_excel(filename, header_lines, rows):
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    current_row = 1
    
    for header in header_lines:
        cell = ws.cell(row=current_row, column=1, value=header)
        cell.font = Font(italic=True, color="808080")
        current_row += 1
    
    current_row += 1
    
    if rows:
        fieldnames = list(rows[0].keys())
        for col, name in enumerate(fieldnames, start=1):
            cell = ws.cell(row=current_row, column=col, value=name.upper())
            cell.font = Font(bold=True)
        current_row += 1
        
        for row in rows:
            for col, key in enumerate(fieldnames, start=1):
                value = row.get(key, "")
                if key in ["purchased", "final_balance"]:
                    try:
                        value = float(value)
                    except:
                        pass
                ws.cell(row=current_row, column=col, value=value)
            current_row += 1
        
        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max_length + 2
    else:
        ws.cell(row=current_row, column=1, value="Brak danych")
    
    wb.save(filename)

def main():
    try:
        print("Rozpoczynam działanie skryptu...")
        t1_unix = parse_date(T1_STR)
        t2_unix = parse_date(T2_STR)
        t3_unix = parse_date(T3_STR)
        print(f"T1: {t1_unix}, T2: {t2_unix}, T3: {t3_unix}")
        
        start_block = get_block_by_timestamp(t1_unix, closest="after")
        end_block = get_block_by_timestamp(t3_unix, closest="before")
        print(f"Zakres bloków: {start_block} - {end_block}")
        
        all_transactions = get_token_transactions(start_block, end_block)
        print(f"Pobrano łącznie {len(all_transactions)} transakcji tokena.")
        
        txs_in_period = [tx for tx in all_transactions if t1_unix <= int(tx["timeStamp"]) <= t3_unix]
        txs_in_period.sort(key=lambda tx: int(tx["timeStamp"]))
        print(f"Transakcje w okresie T1-T3: {len(txs_in_period)}")

        candidate_wallets = []
        wallet_transactions = {}
        for tx in txs_in_period:
            wallet_from = tx["from"].lower()
            wallet_to = tx["to"].lower()
            tx_timestamp = int(tx["timeStamp"])
            
            if wallet_from not in wallet_transactions:
                wallet_transactions[wallet_from] = []
            if wallet_to not in wallet_transactions:
                wallet_transactions[wallet_to] = []
            wallet_transactions[wallet_from].append(tx)
            wallet_transactions[wallet_to].append(tx)
            
            if t1_unix <= tx_timestamp <= t2_unix and wallet_to not in candidate_wallets:
                candidate_wallets.append(wallet_to)

        print(f"Znaleziono {len(candidate_wallets)} kandydatów (portfeli z zakupem w okresie T1-T2).")
        
        exchange_rate = get_exchange_rate(TOKEN_CONTRACT_ADDRESS, retries=5)
        if exchange_rate == "error":
            print("Nie udało się pobrać kursu wymiany tokena. Wartość natywna dla portfela ustawiona jako 'error'.")
        else:
            print(f"Kurs wymiany tokena -> {NATIVE_TOKEN_NAME} na dzień T3: {exchange_rate}")
        
        frequency_cache = load_frequency_cache()

        final_results = []
        for wallet in candidate_wallets:
            txs = wallet_transactions.get(wallet, [])
            
            if not frequency_check(wallet, txs, frequency_cache):
                print(f"Portfel {wallet} odrzucony z powodu zbyt częstych transakcji.")
                continue
            
            purchased, final_balance = simulate_wallet_balance(wallet, txs, t1_unix, t2_unix, t3_unix)
            if purchased == 0:
                continue
            percentage = (final_balance / purchased) * 100
            if final_balance < 0.5 * purchased:
                continue
            
            if exchange_rate != "error":
                native_value = final_balance * exchange_rate
            else:
                native_value = "error"
            
            final_results.append({
                "wallet": wallet,
                "purchased": purchased,
                "final_balance": final_balance,
                "percentage": f"{percentage:.2f}%",
                "native_value": native_value
            })

        save_frequency_cache(frequency_cache)
        
        print(f"Portfeli po filtracji: {len(final_results)}")
        
        header_lines = [
            f"TOKEN_CONTRACT_ADDRESS: {TOKEN_CONTRACT_ADDRESS}",
            f"T1: {T1_STR}",
            f"T2: {T2_STR}",
            f"T3: {T3_STR}",
        ]
        
        output_filename = get_output_filename()
        write_excel(output_filename, header_lines, final_results)
        print(f"Wyniki zapisane do pliku: {output_filename}")
    except Exception as e:
        logging.error(f"Main function error: {e}")
        print("A critical error occurred. Check the logs in:", LOG_FILE)

if __name__ == "__main__":
    main()
