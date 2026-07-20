[🇵🇱 Polski](README.md) | **🇬🇧 English**

# Find Crypto Wallets

[![CI](https://github.com/Adrian-Wiszowaty/find-crypto-wallets/actions/workflows/ci.yml/badge.svg)](https://github.com/Adrian-Wiszowaty/find-crypto-wallets/actions/workflows/ci.yml)

A GUI tool that finds early-buyer wallets for a given ERC-20 token.
You provide the contract address and three points in time, and the app fetches on-chain
transactions, filters out bots, picks wallets that bought early and held, then prices
their balances in USD and saves the result to an Excel file.

## Where it came from

It started with manually browsing Etherscan. I wanted to check which wallets bought a
given token in the first hours after launch and actually held it — instead of selling
within minutes like bots do. With hundreds of transfers in the time window, doing this by
hand was tedious and easy to get wrong.

So I wrote a script that fetches all token transfers in a given range, groups them by
wallet, and works out who bought, how much they held, and what it was worth on a chosen
day. Over time it grew into a tool with a GUI, bot filtering, and Excel export.

## What it does

- Fetches all token transfers in a given time window (T1-T3) on the chosen network.
- Identifies wallets that bought during the buy window (T1-T2) and held tokens through the verification day (T3).
- Filters out bots and suspicious addresses based on transaction frequency.
- Prices remaining balances in the native token and in USD (Dexscreener + CoinGecko).
- Exports a ready ranking to an `.xlsx` file.

## Example

![GUI](gui.png)
![Excel](excel.png)

## How it works

The app walks through four stages:

1. **Configuration** — in the GUI you pick a network, paste the contract address, and set
   three timestamps: start of buying (T1), end of buying (T2), and verification day (T3).
2. **Fetching** — dates are converted to block numbers, and token transfers are pulled from
   the Etherscan V2 API in chunks by block range.
3. **Filtering** — transactions are grouped by wallet; candidates from the T1-T2 window go
   through a frequency analysis that rejects bots.
4. **Pricing & report** — for wallets that held at least 50% of their purchase, the balance
   on day T3 is calculated, converted to USD, and saved to Excel.

The logic is split into layers: data fetching, wallet analysis, pricing, and reporting. The
API client is injected into the services (dependency injection), so each part can be tested
independently, and network definitions (ETH, BSC, Base) live in one place — adding another
one is just an entry in `network_constants.py`.

```text
backend/
  api_client.py             requests to Etherscan / Dexscreener / CoinGecko, with retries
  blockchain_analyzer.py    block lookup and fetching/grouping of token transactions
  wallet_analyzer.py        bot filtering and wallet balance simulation (Decimal)
  exchange_rate_service.py  token exchange rates and USD conversion, with pair caching
  excel_reporter.py         .xlsx report generation
  config_manager.py         configuration and supported network definitions
  wallet_processor.py       ties the whole analysis flow together
frontend/
  gui_app.py                GUI (ttkbootstrap) with live log preview
shared/
  constants/                analysis thresholds, networks, formats and messages
  datetime_helper.py        date parsing in the Europe/Warsaw timezone
```

## Requirements

- Python 3.9+
- Free Etherscan API key (one key works for ETH, BSC, and Base)

## Installation

```bash
git clone https://github.com/Adrian-Wiszowaty/find-crypto-wallets.git
cd find-crypto-wallets
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Open `.env` and paste your API key. Get a free Etherscan key at
<https://etherscan.io/myapikey>.

## Running

```bash
python app.py
```

In the app window, pick a network, paste the token contract address, set the three
timestamps (T1 ≤ T2 ≤ T3), and click **Run analysis**. Logs stream live in the window, and
the finished report lands in the `wallets/` folder.

## Configuration

The API key is kept in `.env` (template in `.env.example`); other parameters are set in the
GUI or in constants. Dates use the format `DD-MM-YYYY HH:MM:SS` (Europe/Warsaw local time).

| Parameter | Where | Description |
|---|---|---|
| `ETHERSCAN_API_KEY` | `.env` | Etherscan API key (required) |
| `NETWORK` | GUI | Network: `ETH`, `BSC`, or `BASE` (default `ETH`) |
| `T1`, `T2`, `T3` | GUI | Start of buying, end of buying, verification day |
| `TOKEN_CONTRACT_ADDRESS` | GUI | Contract address of the analyzed token |
| `MIN_BALANCE_PERCENTAGE` | `api_constants.py` | Minimum % of the purchase a wallet must hold through T3 (default 50) |
| `MIN_USD_VALUE` | `api_constants.py` | Minimum USD balance for a wallet to make the report (default 100) |

Other thresholds (transaction frequency, block chunk size, retry limits) are in
`shared/constants/api_constants.py`.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see [LICENSE](LICENSE).
