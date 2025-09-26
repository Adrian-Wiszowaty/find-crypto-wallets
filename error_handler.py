"""
Centralna klasa do obsługi błędów i wyjątków w aplikacji.
"""
import logging
from typing import Any, Callable, Optional, Type, Union
from functools import wraps


class ErrorHandler:
    """Klasa zarządzająca centralną obsługą błędów"""
    
    @staticmethod
    def safe_execute(func: Callable, *args, default_return=None, 
                    log_error: bool = True, error_message: str = None, **kwargs) -> Any:
        """
        Bezpieczne wykonanie funkcji z obsługą błędów.
        
        Args:
            func: Funkcja do wykonania
            *args: Argumenty pozycyjne
            default_return: Wartość zwracana w przypadku błędu
            log_error: Czy logować błąd
            error_message: Niestandardowy komunikat błędu
            **kwargs: Argumenty nazwane
            
        Returns:
            Wynik funkcji lub default_return w przypadku błędu
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_error:
                msg = error_message or f"Błąd podczas wykonywania {func.__name__}: {e}"
                logging.error(msg)
            return default_return
    
    @staticmethod
    def safe_json_load(file_path: str, default_return: dict = None) -> dict:
        """
        Bezpieczne ładowanie pliku JSON.
        
        Args:
            file_path: Ścieżka do pliku JSON
            default_return: Wartość zwracana w przypadku błędu
            
        Returns:
            dict: Zawartość pliku lub default_return
        """
        if default_return is None:
            default_return = {}
            
        try:
            import json
            import os
            
            if not os.path.exists(file_path):
                logging.warning(f"Plik nie istnieje: {file_path}")
                return default_return
                
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except json.JSONDecodeError as e:
            logging.error(f"Błąd parsowania JSON w pliku {file_path}: {e}")
            return default_return
        except Exception as e:
            logging.error(f"Błąd podczas ładowania pliku {file_path}: {e}")
            return default_return
    
    @staticmethod
    def safe_json_save(data: dict, file_path: str, create_dirs: bool = True) -> bool:
        """
        Bezpieczne zapisywanie do pliku JSON.
        
        Args:
            data: Dane do zapisania
            file_path: Ścieżka do pliku
            create_dirs: Czy tworzyć brakujące katalogi
            
        Returns:
            bool: True jeśli zapis się powiódł
        """
        try:
            import json
            import os
            
            if create_dirs:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            logging.error(f"Błąd podczas zapisywania pliku {file_path}: {e}")
            return False
    
    @staticmethod
    def retry_on_exception(max_retries: int = 3, delay: float = 0.1, 
                          exceptions: tuple = (Exception,)) -> Callable:
        """
        Dekorator do ponawiania wykonania funkcji w przypadku błędu.
        
        Args:
            max_retries: Maksymalna liczba prób
            delay: Opóźnienie między próbami (w sekundach)
            exceptions: Typy wyjątków do obsługi
            
        Returns:
            Dekorator funkcji
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                import time
                
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_retries:
                            logging.warning(f"Próba {attempt + 1} nieudana dla {func.__name__}: {e}")
                            time.sleep(delay * (attempt + 1))  # Zwiększanie delay
                        else:
                            logging.error(f"Wszystkie próby nieudane dla {func.__name__}")
                            
                raise last_exception
            return wrapper
        return decorator
    
    @staticmethod
    def validate_numeric_input(value: Any, min_value: float = None, 
                             max_value: float = None) -> Optional[float]:
        """
        Waliduje i konwertuje wartość numeryczną.
        
        Args:
            value: Wartość do walidacji
            min_value: Minimalna wartość (opcjonalna)
            max_value: Maksymalna wartość (opcjonalna)
            
        Returns:
            float lub None jeśli walidacja nie powiodła się
        """
        try:
            num_value = float(value)
            
            if min_value is not None and num_value < min_value:
                logging.error(f"Wartość {num_value} jest mniejsza od minimum {min_value}")
                return None
                
            if max_value is not None and num_value > max_value:
                logging.error(f"Wartość {num_value} jest większa od maksimum {max_value}")
                return None
                
            return num_value
            
        except (ValueError, TypeError) as e:
            logging.error(f"Błąd konwersji wartości '{value}' do liczby: {e}")
            return None