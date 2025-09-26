"""
GUI dla aplikacji Find Wallets.
Wykorzystuje ulepszone klasy pomocnicze i kod zgodny z dobrymi praktykami programowania.
"""
import json
import os
import threading
import sys
import tkinter as tk
from datetime import datetime
from tkinter import Text, messagebox

import ttkbootstrap as ttk

from constants import Constants
from datetime_helper import DateTimeHelper
from error_handler import ErrorHandler
from gui_helpers import GUIHelpers
from log_redirector import LogRedirector
from main import main


class WalletApp:
    """Aplikacja Find Wallets z wykorzystaniem dobrych praktyk programowania"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.base_dir, Constants.FOLDER_CONFIG, Constants.FILE_CONFIG)
        
        # Inicjalizacja głównego okna
        self._setup_main_window()
        self._setup_gui_components()
        self._load_config()
    
    def _setup_main_window(self):
        """Konfiguruje główne okno aplikacji"""
        self.root = ttk.Window(title=Constants.APP_TITLE, themename=Constants.GUI_THEME)
        
        # Ustawienie ikony
        icon_path = os.path.join(self.base_dir, Constants.FOLDER_IMAGES, Constants.FILE_APP_ICON)
        GUIHelpers.setup_icon(self.root, icon_path)
        
        # Konfiguracja okna
        self.root.minsize(Constants.GUI_MIN_WIDTH, Constants.GUI_MIN_HEIGHT)
        self.root.grid_columnconfigure(0, weight=1, uniform="equal")
        
        # Konfiguracja stylów
        GUIHelpers.configure_ttk_style()
    
    def _setup_gui_components(self):
        """Tworzy wszystkie komponenty GUI"""
        self._create_log_section()
        self._create_network_section()
        self._create_token_section()
        self._create_datetime_sections()
        self._create_control_buttons()
        
    def _create_log_section(self):
        """Tworzy sekcję logów"""
        self.log_widget = Text(self.root, height=Constants.GUI_LOG_HEIGHT, width=Constants.GUI_LOG_WIDTH)
        self.log_widget.grid(row=0, column=0, padx=Constants.GUI_PADDING_X, pady=5, 
                           columnspan=2, sticky="ew")
        self.log_widget.config(bg=Constants.GUI_LOG_BG_COLOR, fg=Constants.GUI_LOG_FG_COLOR,
                             insertbackground=Constants.GUI_LOG_INSERT_BG_COLOR)
        
        # Przekierowanie stdout do widgetu logów
        sys.stdout = LogRedirector(self.log_widget)
    
    def _create_network_section(self):
        """Tworzy sekcję wyboru sieci"""
        frame_network = ttk.Labelframe(self.root, text="Sieć blockchain")
        frame_network.grid(row=1, column=0, padx=Constants.GUI_PADDING_X, 
                         pady=Constants.GUI_PADDING_Y, sticky="ew")
        frame_network.grid_columnconfigure(1, weight=1)
        
        ttk.Label(frame_network, text="Wybierz sieć:").grid(
            row=0, column=0, padx=Constants.GUI_PADDING_X, 
            pady=Constants.GUI_PADDING_Y, sticky="w")
        
        self.network_var = tk.StringVar(value=Constants.DEFAULT_CONFIG["NETWORK"])
        network_combo = ttk.Combobox(frame_network, textvariable=self.network_var,
                                   values=Constants.get_supported_networks(),
                                   state="readonly", style="info.TCombobox")
        network_combo.grid(row=0, column=1, padx=Constants.GUI_PADDING_X,
                         pady=Constants.GUI_PADDING_Y, sticky="ew")
    
    def _create_token_section(self):
        """Tworzy sekcję adresu kontraktu tokena"""
        frame_contract = ttk.Labelframe(self.root, text="Token")
        frame_contract.grid(row=2, column=0, padx=Constants.GUI_PADDING_X,
                          pady=Constants.GUI_PADDING_Y, sticky="ew")
        frame_contract.grid_columnconfigure(1, weight=1)
        
        ttk.Label(frame_contract, text="Adres kontraktu:").grid(
            row=0, column=0, padx=Constants.GUI_PADDING_X,
            pady=Constants.GUI_PADDING_Y, sticky="w")
        
        self.token_contract_entry = ttk.Entry(frame_contract, width=40)
        self.token_contract_entry.grid(row=0, column=1, padx=Constants.GUI_PADDING_X,
                                     pady=Constants.GUI_PADDING_Y, sticky="ew")
        
        # Ustawienie domyślnej wartości
        self.token_contract_entry.insert(0, Constants.DEFAULT_CONFIG["TOKEN_CONTRACT_ADDRESS"])
    
    def _create_datetime_sections(self):
        """Tworzy sekcje do wyboru dat T1, T2, T3"""
        # T1 section
        frame_t1 = ttk.Labelframe(self.root, text="Data początkowa - T1")
        frame_t1.grid(row=3, column=0, padx=Constants.GUI_PADDING_X,
                     pady=Constants.GUI_PADDING_Y, sticky="ew")
        
        self.T1_widgets = GUIHelpers.create_datetime_section(
            frame_t1, "Wybierz T1:", row=0, 
            padx=Constants.GUI_PADDING_X, pady=Constants.GUI_PADDING_Y)
        
        # Przycisk kopiowania T1 do T2 i T3
        copy_t1_button = ttk.Button(frame_t1, text="Kopiuj do T2 i T3", width=17,
                                   command=self._copy_t1_to_all)
        copy_t1_button.grid(row=0, column=2, padx=Constants.GUI_PADDING_X,
                           pady=Constants.GUI_PADDING_Y, sticky="ew", columnspan=2)
        
        # T2 section  
        frame_t2 = ttk.Labelframe(self.root, text="Data końca zakupów - T2")
        frame_t2.grid(row=4, column=0, padx=Constants.GUI_PADDING_X,
                     pady=Constants.GUI_PADDING_Y, sticky="ew")
        
        self.T2_widgets = GUIHelpers.create_datetime_section(
            frame_t2, "Wybierz T2:", row=0,
            padx=Constants.GUI_PADDING_X, pady=Constants.GUI_PADDING_Y)
        
        # Przycisk kopiowania T1 do T2
        copy_t1_t2_button = ttk.Button(frame_t2, text="Kopiuj T1", width=17,
                                      command=self._copy_t1_to_t2)
        copy_t1_t2_button.grid(row=0, column=2, padx=Constants.GUI_PADDING_X,
                              pady=Constants.GUI_PADDING_Y, columnspan=2, sticky="ew")
        
        # T3 section
        frame_t3 = ttk.Labelframe(self.root, text="Data końca analizy - T3")
        frame_t3.grid(row=5, column=0, padx=Constants.GUI_PADDING_X,
                     pady=Constants.GUI_PADDING_Y, sticky="ew")
        
        self.T3_widgets = GUIHelpers.create_datetime_section(
            frame_t3, "Wybierz T3:", row=0,
            padx=Constants.GUI_PADDING_X, pady=Constants.GUI_PADDING_Y)
        
        # Przycisk kopiowania T2 do T3
        copy_t2_t3_button = ttk.Button(frame_t3, text="Kopiuj T2", width=17,
                                      command=self._copy_t2_to_t3)
        copy_t2_t3_button.grid(row=0, column=2, padx=Constants.GUI_PADDING_X,
                              pady=Constants.GUI_PADDING_Y, columnspan=2, sticky="ew")
    
    def _create_control_buttons(self):
        """Tworzy przyciski kontrolne"""
        # Frame dla przycisków
        frame_buttons = ttk.Frame(self.root)
        frame_buttons.grid(row=6, column=0, padx=Constants.GUI_PADDING_X,
                         pady=Constants.GUI_PADDING_Y, sticky="ew")
        frame_buttons.grid_columnconfigure((0, 1), weight=1)
        
        # Przycisk uruchomienia
        self.run_button = ttk.Button(frame_buttons, text="URUCHOM ANALIZĘ",
                                   command=self._save_and_run, bootstyle="success")
        self.run_button.grid(row=0, column=0, padx=Constants.GUI_PADDING_X,
                           pady=Constants.GUI_PADDING_Y, sticky="ew")
        
        # Przycisk zamykania
        close_button = ttk.Button(frame_buttons, text="ZAMKNIJ",
                                command=self.root.quit, bootstyle="danger")
        close_button.grid(row=0, column=1, padx=Constants.GUI_PADDING_X,
                         pady=Constants.GUI_PADDING_Y, sticky="ew")
    
    def _copy_t1_to_all(self):
        """Kopiuje T1 do T2 i T3"""
        GUIHelpers.copy_datetime_values(self.T1_widgets, self.T2_widgets)
        GUIHelpers.copy_datetime_values(self.T1_widgets, self.T3_widgets)
    
    def _copy_t1_to_t2(self):
        """Kopiuje T1 do T2"""
        GUIHelpers.copy_datetime_values(self.T1_widgets, self.T2_widgets)
    
    def _copy_t2_to_t3(self):
        """Kopiuje T2 do T3"""
        GUIHelpers.copy_datetime_values(self.T2_widgets, self.T3_widgets)
    
    def _save_and_run(self):
        """Zapisuje konfigurację i uruchamia analizę"""
        self.run_button.config(state="disabled")
        
        try:
            # Pobranie wartości z GUI
            network = self.network_var.get()
            T1_str = GUIHelpers.get_datetime_string(self.T1_widgets)
            T2_str = GUIHelpers.get_datetime_string(self.T2_widgets) 
            T3_str = GUIHelpers.get_datetime_string(self.T3_widgets)
            token_contract = self.token_contract_entry.get().strip()
            
            # Walidacja danych
            if not token_contract:
                messagebox.showerror("Błąd", "Adres kontraktu nie może być pusty!")
                return
            
            # Walidacja przedziałów czasowych T1 <= T2 <= T3
            try:
                DateTimeHelper.validate_date_range(T1_str, T2_str, T3_str)
            except ValueError as e:
                messagebox.showerror("Błąd walidacji dat", 
                                   f"Niepoprawne ustawienie dat:\n{str(e)}\n\n"
                                   "Upewnij się, że T1 ≤ T2 ≤ T3")
                return
            except Exception as e:
                messagebox.showerror("Błąd", f"Błąd podczas walidacji dat: {str(e)}")
                return
            
            # Utworzenie konfiguracji
            config = {
                "NETWORK": network,
                "T1_STR": T1_str,
                "T2_STR": T2_str, 
                "T3_STR": T3_str,
                "TOKEN_CONTRACT_ADDRESS": token_contract
            }
            
            # Zapisanie konfiguracji
            if ErrorHandler.safe_json_save(config, self.config_file):
                self.log_widget.insert(tk.END, "Konfiguracja zapisana\n")
                self.log_widget.yview(tk.END)
                
                # Uruchomienie analizy w osobnym wątku
                threading.Thread(target=self._run_analysis, daemon=True).start()
            else:
                messagebox.showerror("Błąd", "Nie udało się zapisać konfiguracji!")
                
        except ValueError as e:
            messagebox.showerror("Błąd walidacji", str(e))
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił nieoczekiwany błąd: {e}")
        finally:
            self.run_button.config(state="normal")
    
    def _run_analysis(self):
        """Uruchamia analizę w osobnym wątku"""
        try:
            main()  # Wywołanie głównej funkcji analizy
            self._show_success_message()
        except Exception as e:
            self._show_error_message(str(e))
    
    def _show_success_message(self):
        """Wyświetla komunikat o sukcesie"""
        self._play_sound(success=True)
        messagebox.showinfo("Sukces", "Operacja zakończona pomyślnie!")
    
    def _show_error_message(self, error_msg: str):
        """Wyświetla komunikat o błędzie"""
        self._play_sound(success=False) 
        messagebox.showerror("Błąd", f"Wystąpił błąd: {error_msg}")
    
    def _play_sound(self, success: bool = True):
        """Odtwarza dźwięk systemowy"""
        try:
            if os.name == 'nt':  # Windows
                import winsound
                freq, dur = (1000, 500) if success else (200, 500)
                winsound.Beep(freq, dur)
            else:  # macOS/Linux
                sound_file = ("/System/Library/Sounds/Pop.aiff" if success 
                            else "/System/Library/Sounds/Basso.aiff")
                os.system(f"afplay {sound_file}")
        except Exception:
            pass  # Ignoruj błędy dźwięku
    
    def _load_config(self):
        """Ładuje zapisaną konfigurację"""
        config = ErrorHandler.safe_json_load(self.config_file, Constants.DEFAULT_CONFIG)
        
        # Ustawienie wartości w GUI
        self.network_var.set(config.get("NETWORK", Constants.DEFAULT_CONFIG["NETWORK"]))
        
        token_address = config.get("TOKEN_CONTRACT_ADDRESS", Constants.DEFAULT_CONFIG["TOKEN_CONTRACT_ADDRESS"])
        self.token_contract_entry.delete(0, tk.END)
        self.token_contract_entry.insert(0, token_address)
        
        # Ładowanie dat (opcjonalne - można pozostawić domyślne)
        self._load_datetime_config("T1_STR", self.T1_widgets, config)
        self._load_datetime_config("T2_STR", self.T2_widgets, config)
        self._load_datetime_config("T3_STR", self.T3_widgets, config)
    
    def _load_datetime_config(self, config_key: str, widgets: tuple, config: dict):
        """Ładuje konfigurację daty dla konkretnego widget'u"""
        try:
            date_str = config.get(config_key, Constants.DEFAULT_CONFIG[config_key])
            date_obj = datetime.strptime(date_str, Constants.DATE_FORMAT)
            
            date_entry, hour_combo, minute_combo, second_combo = widgets
            
            # Ustawienie daty
            date_entry.entry.delete(0, tk.END)
            date_entry.entry.insert(0, date_obj.strftime("%Y-%m-%d"))
            
            # Ustawienie czasu
            hour_combo.set(f"{date_obj.hour:02d}")
            minute_combo.set(f"{date_obj.minute:02d}")
            second_combo.set(f"{date_obj.second:02d}")
            
        except Exception as e:
            print(f"Błąd podczas ładowania konfiguracji {config_key}: {e}")
    
    def run(self):
        """Uruchamia aplikację"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Błąd aplikacji: {e}")


def main_app():
    """Funkcja główna aplikacji"""
    try:
        app = WalletApp()
        app.run()
    except Exception as e:
        print(f"Krytyczny błąd aplikacji: {e}")


if __name__ == "__main__":
    main_app()