import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from shared.constants import Constants

class ConfigManager:
    
    def __init__(self, config_file: Optional[str] = None):

        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_file = config_file or os.path.join(self.base_dir, Constants.FOLDER_CONFIG, Constants.FILE_CONFIG)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        
        from shared.error_handler import ErrorHandler
        return ErrorHandler.safe_json_load(self.config_file, {})
    
    def save_config(self, config_data: Dict[str, Any]) -> bool:
        
        from shared.error_handler import ErrorHandler
        if ErrorHandler.safe_json_save(config_data, self.config_file):
            self.config = config_data
            return True
        return False
    
    def get(self, key: str, default: Any = None) -> Any:
        
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        
        self.config[key] = value
    
    def get_network_config(self) -> Dict[str, str]:
        
        network = self.get("NETWORK", Constants.DEFAULT_CONFIG["NETWORK"])
        return self.get_network_config_by_name(network)
    
    @staticmethod
    def get_network_config_by_name(network: str) -> Dict[str, str]:
        """Pobiera konfigurację sieci na podstawie nazwy."""
        if network not in Constants.NETWORKS:
            raise ValueError(f"{Constants.ERROR_UNSUPPORTED_NETWORK}: {network}")
        return Constants.NETWORKS[network]
    
    @staticmethod
    def get_supported_networks() -> list:
        """Zwraca listę obsługiwanych sieci."""
        return list(Constants.NETWORKS.keys())
    
    def validate_config(self) -> bool:
        
        required_fields = list(Constants.DEFAULT_CONFIG.keys())
        
        for field in required_fields:
            if not self.get(field):
                logging.error(f"Brak wymaganego pola konfiguracji: {field}")
                return False
        
        date_fields = ["T1_STR", "T2_STR", "T3_STR"]
        for field in date_fields:
            try:
                datetime.strptime(self.get(field), Constants.DATE_FORMAT)
            except ValueError:
                logging.error(f"Nieprawidłowy format daty w polu {field}")
                return False
        
        supported_networks = self.get_supported_networks()
        if self.get("NETWORK") not in supported_networks:
            logging.error(f"{Constants.ERROR_UNSUPPORTED_NETWORK}: {self.get('NETWORK')}. Dostępne: {supported_networks}")
            return False
        
        return True
    
    def get_paths_config(self) -> Dict[str, str]:
        
        return {
            "base_dir": self.base_dir,
            "wallets_folder": os.path.join(self.base_dir, Constants.FOLDER_WALLETS),
            "cache_folder": os.path.join(self.base_dir, Constants.FOLDER_CACHE),
            "logs_folder": os.path.join(self.base_dir, Constants.FOLDER_LOGS),
            "cache_file": os.path.join(self.base_dir, Constants.FOLDER_CACHE, Constants.FILE_WALLET_CACHE),
            "log_file": os.path.join(self.base_dir, Constants.FOLDER_LOGS, Constants.FILE_ERROR_LOG)
        }
    
    def ensure_directories(self) -> None:
        
        paths = self.get_paths_config()
        directories = [paths["wallets_folder"], paths["cache_folder"], paths["logs_folder"]]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)