from decimal import Decimal

from backend.wallet_analyzer import WalletAnalyzer

WALLET = "0x1111111111111111111111111111111111111111"
OTHER = "0x2222222222222222222222222222222222222222"


def _bare_analyzer() -> WalletAnalyzer:
    return object.__new__(WalletAnalyzer)


def _tx(timestamp: int, sender: str, recipient: str, value: int, decimals: int = 0) -> dict:
    return {
        "timeStamp": str(timestamp),
        "from": sender,
        "to": recipient,
        "value": str(value),
        "tokenDecimal": str(decimals),
    }


def test_simulate_counts_purchases_and_sales():
    analyzer = _bare_analyzer()
    transactions = [
        _tx(100, OTHER, WALLET, 10),
        _tx(150, OTHER, WALLET, 5),
        _tx(250, WALLET, OTHER, 4),
    ]
    assert analyzer.simulate_wallet_balance(WALLET, transactions, 100, 200, 300) == (15.0, 11.0, 2, 1)


def test_simulate_ignores_transactions_outside_window():
    analyzer = _bare_analyzer()
    transactions = [
        _tx(50, OTHER, WALLET, 10),
        _tx(100, OTHER, WALLET, 7),
        _tx(400, WALLET, OTHER, 3),
    ]
    assert analyzer.simulate_wallet_balance(WALLET, transactions, 100, 200, 300) == (7.0, 7.0, 1, 0)


def test_simulate_applies_token_decimals():
    analyzer = _bare_analyzer()
    transactions = [_tx(100, OTHER, WALLET, 1500, decimals=2)]
    assert analyzer.simulate_wallet_balance(WALLET, transactions, 100, 200, 300) == (15.0, 15.0, 1, 0)


def test_simulate_keeps_large_amounts_exact():
    analyzer = _bare_analyzer()
    big = 9007199254740993
    transactions = [_tx(100 + i, OTHER, WALLET, big) for i in range(3)]
    purchased, _, purchase_count, _ = analyzer.simulate_wallet_balance(WALLET, transactions, 100, 200, 300)
    assert purchase_count == 3
    assert purchased == Decimal(big) * 3


def _frequency_analyzer() -> WalletAnalyzer:
    analyzer = object.__new__(WalletAnalyzer)
    analyzer.frequency_interval_seconds = 60
    analyzer.min_frequency_violations = 5
    return analyzer


def test_frequency_rejects_rapid_bursts():
    analyzer = _frequency_analyzer()
    transactions = [_tx(1000 + i * 10, OTHER, WALLET, 1) for i in range(7)]
    assert analyzer._check_transaction_frequency(transactions) is False


def test_frequency_accepts_spread_out_transactions():
    analyzer = _frequency_analyzer()
    transactions = [_tx(1000 + i * 100, OTHER, WALLET, 1) for i in range(7)]
    assert analyzer._check_transaction_frequency(transactions) is True


def test_frequency_accepts_single_transaction():
    analyzer = _frequency_analyzer()
    assert analyzer._check_transaction_frequency([_tx(1, OTHER, WALLET, 1)]) is True
