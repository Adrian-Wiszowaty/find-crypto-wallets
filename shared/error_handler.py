import json
import logging
import os
from typing import Optional

class ErrorHandler:

    @staticmethod
    def safe_json_load(file_path: str, default_return: Optional[dict] = None) -> dict:

        if default_return is None:
            default_return = {}

        try:
            if not os.path.exists(file_path):
                logging.warning(f"Plik nie istnieje: {file_path}")
                return default_return
                
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error in file {file_path}: {e}")
            return default_return
        except Exception as e:
            logging.error(f"Error loading file {file_path}: {e}")
            return default_return
    
    @staticmethod
    def safe_json_save(data: dict, file_path: str, create_dirs: bool = True) -> bool:
        
        try:
            if create_dirs:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            logging.error(f"Error saving file {file_path}: {e}")
            return False