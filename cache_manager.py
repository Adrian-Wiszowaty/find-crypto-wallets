"""
Klasa odpowiedzialna za zarządzanie cache'em aplikacji.
"""
import json
import os
import logging
from typing import Dict, Any, Optional
from config_manager import ConfigManager


class CacheManager:
    """Zarządza operacjami cache'owania danych aplikacji"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        paths = config_manager.get_paths_config()
        
        # Ścieżki do plików cache
        self.cache_folder = paths["cache_folder"]
        self.frequency_cache_file = paths["cache_file"]
        
        # Zapewniamy istnienie folderu cache
        os.makedirs(self.cache_folder, exist_ok=True)
    
    def load_frequency_cache(self) -> Dict[str, bool]:
        """
        Ładuje cache weryfikacji częstotliwości transakcji z pliku.
        
        Returns:
            Dict[str, bool]: Cache z flagami portfeli odrzuconych za częste transakcje
        """
        if os.path.exists(self.frequency_cache_file):
            try:
                with open(self.frequency_cache_file, "r") as f:
                    cache_data = json.load(f)
                    logging.info(f"Załadowano cache częstotliwości: {len(cache_data)} wpisów")
                    return cache_data
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Błąd ładowania cache z {self.frequency_cache_file}: {e}")
                return {}
        else:
            logging.info("Plik cache częstotliwości nie istnieje, tworzę nowy")
            return {}
    
    def save_frequency_cache(self, cache: Dict[str, bool]) -> None:
        """
        Zapisuje cache weryfikacji częstotliwości do pliku.
        
        Args:
            cache: Słownik z flagami portfeli do zapisania
        """
        try:
            with open(self.frequency_cache_file, "w") as f:
                json.dump(cache, f, indent=2)
            logging.info(f"Zapisano cache częstotliwości: {len(cache)} wpisów")
        except (IOError, json.JSONEncodeError) as e:
            logging.error(f"Błąd zapisu cache do {self.frequency_cache_file}: {e}")
    
    def load_generic_cache(self, cache_filename: str) -> Dict[str, Any]:
        """
        Ładuje dowolny plik cache JSON.
        
        Args:
            cache_filename: Nazwa pliku cache (bez ścieżki)
            
        Returns:
            Dict[str, Any]: Załadowane dane cache lub pusty słownik
        """
        cache_path = os.path.join(self.cache_folder, cache_filename)
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cache_data = json.load(f)
                    logging.info(f"Załadowano cache {cache_filename}: {len(cache_data)} wpisów")
                    return cache_data
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Błąd ładowania cache z {cache_path}: {e}")
                return {}
        else:
            logging.info(f"Plik cache {cache_filename} nie istnieje")
            return {}
    
    def save_generic_cache(self, cache: Dict[str, Any], cache_filename: str) -> None:
        """
        Zapisuje dowolny cache do pliku JSON.
        
        Args:
            cache: Dane do zapisania
            cache_filename: Nazwa pliku cache (bez ścieżki)
        """
        cache_path = os.path.join(self.cache_folder, cache_filename)
        
        try:
            with open(cache_path, "w") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
            logging.info(f"Zapisano cache {cache_filename}: {len(cache)} wpisów")
        except (IOError, json.JSONEncodeError) as e:
            logging.error(f"Błąd zapisu cache do {cache_path}: {e}")
    
    def clear_cache(self, cache_filename: Optional[str] = None) -> None:
        """
        Czyści cache - usuwa plik lub wszystkie pliki cache.
        
        Args:
            cache_filename: Nazwa konkretnego pliku do usunięcia, 
                          None = usuń wszystkie pliki cache
        """
        if cache_filename:
            # Usuń konkretny plik
            cache_path = os.path.join(self.cache_folder, cache_filename)
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                    logging.info(f"Usunięto plik cache: {cache_filename}")
                except OSError as e:
                    logging.error(f"Błąd usuwania cache {cache_filename}: {e}")
            else:
                logging.warning(f"Plik cache {cache_filename} nie istnieje")
        else:
            # Usuń wszystkie pliki cache
            try:
                if os.path.exists(self.cache_folder):
                    for filename in os.listdir(self.cache_folder):
                        if filename.endswith('.json'):
                            file_path = os.path.join(self.cache_folder, filename)
                            os.remove(file_path)
                            logging.info(f"Usunięto plik cache: {filename}")
                    logging.info("Wyczyszczono wszystkie pliki cache")
            except OSError as e:
                logging.error(f"Błąd czyszczenia cache: {e}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Zwraca informacje o aktualnym stanie cache.
        
        Returns:
            Dict[str, Any]: Informacje o plikach cache
        """
        info = {
            "cache_folder": self.cache_folder,
            "cache_files": [],
            "total_size_bytes": 0
        }
        
        try:
            if os.path.exists(self.cache_folder):
                for filename in os.listdir(self.cache_folder):
                    if filename.endswith('.json'):
                        file_path = os.path.join(self.cache_folder, filename)
                        file_size = os.path.getsize(file_path)
                        file_modified = os.path.getmtime(file_path)
                        
                        info["cache_files"].append({
                            "filename": filename,
                            "size_bytes": file_size,
                            "modified_timestamp": file_modified
                        })
                        info["total_size_bytes"] += file_size
                        
            info["total_files"] = len(info["cache_files"])
            
        except OSError as e:
            logging.error(f"Błąd podczas sprawdzania cache: {e}")
        
        return info
    
    def is_wallet_in_frequency_cache(self, wallet_address: str) -> bool:
        """
        Sprawdza czy portfel znajduje się w cache częstotliwości (został odrzucony).
        
        Args:
            wallet_address: Adres portfela do sprawdzenia
            
        Returns:
            bool: True jeśli portfel jest w cache (został odrzucony)
        """
        cache = self.load_frequency_cache()
        return wallet_address.lower() in cache
    
    def add_wallet_to_frequency_cache(self, wallet_address: str) -> None:
        """
        Dodaje portfel do cache częstotliwości (oznacza jako odrzucony).
        
        Args:
            wallet_address: Adres portfela do dodania
        """
        cache = self.load_frequency_cache()
        cache[wallet_address.lower()] = True
        self.save_frequency_cache(cache)