# Find Crypto Wallets - Zrefaktoryzowana Aplikacja

## Opis

Aplikacja do znajdowania i analizy portfeli kryptowalut na podstawie wzorców transakcji. Została w pełni zrefaktoryzowana zgodnie z dobrymi praktykami programowania.

## Struktura Projektu

### Nowe Pliki (Zrefaktoryzowane)

- **`config_manager.py`** - Zarządzanie konfiguracją aplikacji
- **`api_client.py`** - Obsługa wszystkich zapytań API (Etherscan, Dexscreener, CoinGecko)
- **`wallet_analyzer.py`** - Analiza portfeli i wzorców transakcji
- **`excel_reporter.py`** - Generowanie raportów Excel
- **`main_window.py`** - Interface użytkownika (GUI)
- **`main_refactored.py`** - Główna logika aplikacji
- **`start_refactored.py`** - Punkt wejścia dla zrefaktoryzowanej aplikacji
- **`error_handling.py`** - Obsługa błędów i logowania

### Stare Pliki (Do zachowania kompatybilności)

- **`Main.py`** - Oryginalny kod (zachowany)
- **`Start.py`** - Oryginalny interface (zachowany)
- **`LogRedirector.py`** - Używany w obu wersjach

## Usprawnienia w Zrefaktoryzowanej Wersji

### 1. Architektura i Organizacja Kodu

- **Podział na klasy**: Każda klasa ma jedną odpowiedzialność (Single Responsibility Principle)
- **Separacja warstw**: API, logika biznesowa, interface użytkownika
- **Czytelność**: Lepsze nazewnictwo zmiennych i funkcji
- **Dokumentacja**: Docstringi dla wszystkich klas i metod

### 2. Zarządzanie Konfiguracją

```python
# Przed refaktoryzacją
config = load_json_config()
NETWORK = config.get("NETWORK", "ETH")

# Po refaktoryzacji
config_manager = ConfigManager()
network = config_manager.get("NETWORK", "ETH")
config_manager.validate_config()  # Walidacja!
```

### 3. Obsługa API

```python
# Przed - funkcje globalne
def api_request(params):
    # długa funkcja z logiką retry

# Po - klasa dedykowana
api_client = ApiClient(config_manager)
data = api_client.etherscan_api_request(params)
```

### 4. Obsługa Błędów

- **Właściwe wyjątki**: `ValidationError`, `ApiError`, `ConfigurationError`
- **Lepsze logowanie**: Strukturalne logi z poziomami ważności
- **Mechanizm retry**: Wykładniczy backoff dla zapytań API
- **Walidacja danych**: Sprawdzanie poprawności przed przetwarzaniem

### 5. Interface Użytkownika

```python
# Przed - funkcje i zmienne globalne
def create_time_combobox(parent, values):
    # kod tworzenia widgetów

# Po - klasa MainWindow
class MainWindow:
    def __init__(self):
        self._setup_main_window()
        self._setup_widgets()
```

## Uruchamianie

### Zrefaktoryzowana Wersja (Zalecana)

```bash
python start_refactored.py
```

### Oryginalna Wersja

```bash
python Start.py
```

## Wymagania

```
requests
openpyxl
ttkbootstrap
```

## Konfiguracja

Aplikacja używa pliku `config/config.json`:

```json
{
    "NETWORK": "ETH",
    "TOKEN_CONTRACT_ADDRESS": "0x712f43B21cf3e1B189c27678C0f551c08c01D150",
    "T1_STR": "17-03-2025 22:25:00",
    "T2_STR": "18-03-2025 19:30:00",
    "T3_STR": "19-03-2025 20:00:00"
}
```

## Nowe Funkcje w Zrefaktoryzowanej Wersji

### 🌐 Dynamiczne Pobieranie Wspieranych Sieci

Aplikacja teraz automatycznie pobiera listę wspieranych sieci blockchain z Etherscan API, zamiast mieć je zahardkodowane:

- **Automatyczne wykrywanie**: Testuje dostępność każdej sieci
- **Cache**: Zapisuje wyniki na 24h aby przyspieszyć uruchamianie
- **Fallback**: Używa domyślnych sieci w przypadku problemów z internetem
- **Odświeżanie**: Przycisk 🔄 do aktualizacji listy sieci

#### Obecnie Wspierane Sieci:
- **Ethereum (ETH)** - Chain ID: 1
- **BNB Smart Chain (BSC)** - Chain ID: 56  
- **Base (BASE)** - Chain ID: 8453
- **Polygon (POLYGON)** - Chain ID: 137
- **Arbitrum One (ARBITRUM)** - Chain ID: 42161
- **Optimism (OPTIMISM)** - Chain ID: 10
- **Avalanche C-Chain (AVALANCHE)** - Chain ID: 43114

### 📊 Rozszerzone Informacje o Sieciach

Każda sieć zawiera teraz kompletne metadane:

```json
{
  "ETH": {
    "api_url": "https://api.etherscan.io/v2/api?chainid=1",
    "chain_id": 1,
    "native_token_name": "ETH",
    "native_token_full_name": "ethereum",
    "native_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "display_name": "Ethereum",
    "explorer": "https://etherscan.io"
  }
}
```

## Klasy i ich Odpowiedzialności

### ConfigManager
- Ładowanie i zapisywanie konfiguracji  
- Walidacja ustawień
- Zarządzanie ścieżkami plików i folderów
- **NOWE**: Dynamiczne pobieranie wspieranych sieci
- **NOWE**: Cache sieci z automatycznym odświeżaniem
- **NOWE**: Test dostępności sieci przez API

### ApiClient
- Zapytania do Etherscan API
- Pobieranie cen z Dexscreener
- Kursy wymiany z CoinGecko
- Mechanizm retry z wykładniczym backoff

### WalletAnalyzer
- Analiza wzorców transakcji
- Sprawdzanie częstotliwości transakcji
- Symulacja salda portfeli
- Filtrowanie według kryteriów biznesowych

### ExcelReporter
- Generowanie raportów Excel
- Formatowanie danych
- Statystyki podsumowujące
- Auto-dopasowanie szerokości kolumn

### MainWindow
- Interface użytkownika
- Zarządzanie widgetami
- Walidacja formularzy
- Wielowątkowość (uruchamianie w tle)

### WalletFinder (main_refactored.py)
- Orkiestracja całego procesu
- Pomiar wydajności
- Obsługa błędów wysokiego poziomu

## Obsługa Błędów

### Typy Wyjątków

```python
ValidationError    # Błędy walidacji danych
ApiError          # Problemy z API
ConfigurationError # Błędy konfiguracji
```

### Logowanie

Logi są zapisywane w `Logs/error_log.txt` z informacjami:
- Znacznik czasu
- Poziom ważności (INFO, WARNING, ERROR)
- Szczegółowy opis błędu

## Wydajność

### Monitorowanie

```python
performance_monitor = PerformanceMonitor()
performance_monitor.start_timer("blockchain_fetch")
# ... operacja ...
duration = performance_monitor.end_timer("blockchain_fetch")
```

### Optymalizacje

- **Cache częstotliwości**: Zapisywanie wyników sprawdzania portfeli
- **Przetwarzanie wsadowe**: Grupowanie zapytań API
- **Lazy loading**: Pobieranie danych tylko gdy potrzebne

## Nowe API - Metody ConfigManager

### Pobieranie Dostępnych Sieci

```python
from config_manager import ConfigManager

cm = ConfigManager()

# Pobranie wszystkich dostępnych sieci
networks = cm.get_available_networks()
print(networks)
# {'ETH': 'Ethereum', 'BSC': 'BNB Smart Chain', 'BASE': 'Base', ...}

# Pobranie szczegółowej konfiguracji sieci
eth_config = cm.get_network_config()  # dla aktualnie wybranej sieci
print(eth_config)
# {'api_url': '...', 'chain_id': 1, 'native_token_name': 'ETH', ...}
```

### Wymuszenie Odświeżenia Cache

```python
# Usuń cache i pobierz świeże dane
import os
cache_file = os.path.join(cm.base_dir, "Cache", "networks_cache.json")
if os.path.exists(cache_file):
    os.remove(cache_file)

# Następne wywołanie pobierze dane z internetu
networks = cm.get_available_networks()
```

## Testowanie

Zalecane testy dla każdej klasy:

```bash
# Testowanie konfiguracji
python -c "from config_manager import ConfigManager; cm = ConfigManager(); print(cm.validate_config())"

# Testowanie dostępnych sieci
python -c "from config_manager import ConfigManager; cm = ConfigManager(); print(cm.get_available_networks())"

# Testowanie API
python -c "from api_client import ApiClient; from config_manager import ConfigManager; ac = ApiClient(ConfigManager()); print('API OK')"
```

## Migracja z Oryginalnej Wersji

1. **Zachowanie kompatybilności**: Stare pliki nadal działają
2. **Stopniowa migracja**: Można używać nowych klas w starym kodzie
3. **Konfiguracja**: Ten sam format `config.json`
4. **Wyniki**: Identyczne raporty Excel

## Rozszerzalność

### Dodanie Nowej Sieci

```python
# W config_manager.py
network_configs = {
    "ETH": {...},
    "BSC": {...},
    "BASE": {...},
    "POLYGON": {  # Nowa sieć
        "api_url": "https://...",
        "native_token_name": "MATIC",
        # ...
    }
}
```

### Dodanie Nowego Kryterium Filtracji

```python
# W wallet_analyzer.py
def new_filter_criteria(self, results):
    # Nowe kryteria filtracji
    pass
```

## Bezpieczeństwo

- **Walidacja wejść**: Wszystkie dane są walidowane
- **Rate limiting**: Ograniczenia zapytań API
- **Obsługa błędów**: Graceful degradation
- **Logowanie**: Audit trail wszystkich operacji

## Wsparcie

W przypadku problemów:
1. Sprawdź logi w `Logs/error_log.txt`
2. Zweryfikuj konfigurację w `config/config.json`
3. Sprawdź połączenie internetowe i dostępność API