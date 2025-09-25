"""
Klasa odpowiedzialna za zarządzanie konfiguracją aplikacji.
"""
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from constants import Constants


class ConfigManager:
    """Zarządza konfiguracją aplikacji z pliku config.json"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = config_file or os.path.join(self.base_dir, Constants.FOLDER_CONFIG, Constants.FILE_CONFIG)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Ładuje konfigurację z pliku config.json"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except FileNotFoundError:
            logging.warning(f"Plik konfiguracji {self.config_file} nie został znaleziony")
        except json.JSONDecodeError as e:
            logging.error(f"Błąd parsowania JSON w pliku {self.config_file}: {e}")
        except Exception as e:
            logging.error(f"Błąd ładowania konfiguracji z {self.config_file}: {e}")
        
        return {}
    
    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """Zapisuje konfigurację do pliku"""
        try:
            # Tworzenie katalogu config jeśli nie istnieje
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            self.config = config_data
            return True
        except Exception as e:
            logging.error(f"Błąd zapisu konfiguracji do {self.config_file}: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Pobiera wartość z konfiguracji"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Ustawia wartość w konfiguracji"""
        self.config[key] = value
    
    def get_network_config(self) -> Dict[str, str]:
        """Zwraca konfigurację dla wybranej sieci"""
        network = self.get("NETWORK", Constants.DEFAULT_CONFIG["NETWORK"])
        return Constants.get_network_config(network)
    
    def validate_config(self) -> bool:
        """Waliduje konfigurację"""
        required_fields = list(Constants.DEFAULT_CONFIG.keys())
        
        for field in required_fields:
            if not self.get(field):
                logging.error(f"Brak wymaganego pola konfiguracji: {field}")
                return False
        
        # Walidacja dat
        date_fields = ["T1_STR", "T2_STR", "T3_STR"]
        for field in date_fields:
            try:
                datetime.strptime(self.get(field), Constants.DATE_FORMAT)
            except ValueError:
                logging.error(f"Nieprawidłowy format daty w polu {field}")
                return False
        
        # Walidacja sieci
        supported_networks = Constants.get_supported_networks()
        if self.get("NETWORK") not in supported_networks:
            logging.error(f"{Constants.ERROR_UNSUPPORTED_NETWORK}: {self.get('NETWORK')}. Dostępne: {supported_networks}")
            return False
        
        return True
    
    def get_paths_config(self) -> Dict[str, str]:
        """Zwraca konfigurację ścieżek"""
        return {
            "base_dir": self.base_dir,
            "wallets_folder": os.path.join(self.base_dir, Constants.FOLDER_WALLETS),
            "cache_folder": os.path.join(self.base_dir, Constants.FOLDER_CACHE),
            "logs_folder": os.path.join(self.base_dir, Constants.FOLDER_LOGS),
            "cache_file": os.path.join(self.base_dir, Constants.FOLDER_CACHE, Constants.FILE_WALLET_CACHE),
            "log_file": os.path.join(self.base_dir, Constants.FOLDER_LOGS, Constants.FILE_ERROR_LOG)
        }
    
    def ensure_directories(self) -> None:
        """Tworzy wymagane katalogi jeśli nie istnieją"""
        paths = self.get_paths_config()
        directories = [paths["wallets_folder"], paths["cache_folder"], paths["logs_folder"]]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)