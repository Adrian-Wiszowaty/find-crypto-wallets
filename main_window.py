"""
Klasa głównego okna aplikacji GUI.
"""
import json
import os
import sys
import threading
import tkinter as tk
from datetime import datetime
from tkinter import Text, messagebox, PhotoImage
from typing import Tuple, Callable

import ttkbootstrap as ttk
from ttkbootstrap.widgets import DateEntry

from config_manager import ConfigManager
from log_redirector import LogRedirector
from constants import Constants
from datetime_helper import DateTimeHelper


class MainWindow:
    """Główne okno aplikacji GUI dla znajdowania portfeli krypto"""
    
    def __init__(self, main_function: Callable = None):
        self.config_manager = ConfigManager()
        self.main_function = main_function
        
        # Konfiguracja interfejsu
        self.padx = Constants.GUI_PADDING_X
        self.pady = Constants.GUI_PADDING_Y
        
        # Inicjalizacja głównego okna
        self._setup_main_window()
        self._setup_styles()
        self._setup_widgets()
        self._load_saved_config()
    
    def _setup_main_window(self) -> None:
        """Konfiguruje główne okno aplikacji"""
        self.root = ttk.Window(title="Find Wallets", themename="flatly")
        self.root.minsize(Constants.GUI_MIN_WIDTH, Constants.GUI_MIN_HEIGHT)
        self.root.grid_columnconfigure(0, weight=1, uniform="equal")
        
        # Dodanie ikony
        self._setup_icon()
    
    def _setup_icon(self) -> None:
        """Ustawia ikonę aplikacji"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, Constants.FOLDER_IMAGES, Constants.FILE_APP_ICON)
        
        if os.path.exists(icon_path):
            try:
                icon_image = PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon_image)
            except Exception as e:
                print(f"{Constants.ERROR_ICON_LOAD_FAILED}: {e}")
        else:
            print(Constants.ERROR_ICON_NOT_FOUND)
    
    def _setup_styles(self) -> None:
        """Konfiguruje style dla widgetów"""
        style = ttk.Style()
        style.configure(
            "info.TCombobox",
            fieldbackground="white",
            bordercolor=style.colors.info,
            arrowcolor=style.colors.info
        )
        style.map("info.TCombobox", fieldbackground=[("readonly", "white")])
    
    def _setup_widgets(self) -> None:
        """Tworzy wszystkie widgety interfejsu"""
        self._create_log_widget()
        self._create_token_section()
        self._create_datetime_sections()
        self._create_network_section()
    
    def _create_log_widget(self) -> None:
        """Tworzy widget do wyświetlania logów"""
        self.log_widget = Text(self.root, height=Constants.GUI_LOG_HEIGHT, width=Constants.GUI_LOG_WIDTH)
        self.log_widget.grid(row=0, column=0, padx=self.padx, pady=5, 
                           columnspan=2, sticky="ew")
        self.log_widget.config(bg=Constants.GUI_LOG_BG_COLOR, fg=Constants.GUI_LOG_FG_COLOR, 
                              insertbackground=Constants.GUI_LOG_INSERT_BG_COLOR)
        
        # Przekierowanie stdout do widgetu logów
        sys.stdout = LogRedirector(self.log_widget)
    
    def _create_token_section(self) -> None:
        """Tworzy sekcję adresu kontraktu tokena"""
        frame_contract = ttk.Labelframe(self.root, text="Token")
        frame_contract.grid(row=1, column=0, padx=self.padx, pady=self.pady, sticky="ew")
        frame_contract.grid_columnconfigure(1, weight=1)
        
        ttk.Label(frame_contract, text="Adres kontraktu:").grid(
            row=0, column=0, padx=self.padx, pady=self.pady, sticky="w"
        )
        
        self.token_contract_entry = ttk.Entry(frame_contract, width=40)
        self.token_contract_entry.grid(
            row=0, column=1, padx=self.padx, pady=self.pady, sticky="ew"
        )
    
    def _create_time_combobox(self, parent: ttk.Widget, values: list) -> ttk.Combobox:
        """Tworzy combobox do wyboru czasu"""
        combo = ttk.Combobox(
            parent, values=values, width=3, 
            state="readonly", style="info.TCombobox"
        )
        combo.current(0)
        return combo
    
    def _create_datetime_section(self, parent: ttk.Widget, row: int) -> Tuple[DateEntry, ttk.Combobox, ttk.Combobox, ttk.Combobox]:
        """Tworzy sekcję wyboru daty i czasu"""
        # Konfiguracja kolumn
        for col in range(5):
            parent.grid_columnconfigure(col, weight=0)
        
        # Widget wyboru daty
        date_entry = DateEntry(parent, dateformat="%d-%m-%Y")
        date_entry.grid(row=row, column=0, padx=self.padx, pady=self.pady, sticky="ew")
        
        # Combobox dla godzin (0-23)
        hour_values = [f"{i:02d}" for i in range(24)]
        hour_combo = self._create_time_combobox(parent, hour_values)
        hour_combo.grid(row=row, column=1, padx=self.padx, pady=self.pady)
        hour_combo.set("22")
        
        # Combobox dla minut (0-59)
        minute_values = [f"{i:02d}" for i in range(60)]
        minute_combo = self._create_time_combobox(parent, minute_values)
        minute_combo.grid(row=row, column=2, padx=self.padx, pady=self.pady)
        minute_combo.set("25")
        
        # Combobox dla sekund (0-59)
        second_values = [f"{i:02d}" for i in range(60)]
        second_combo = self._create_time_combobox(parent, second_values)
        second_combo.grid(row=row, column=3, padx=self.padx, pady=self.pady)
        second_combo.set("00")
        
        # Dodaj walidację w czasie rzeczywistym po utworzeniu wszystkich widgets
        def schedule_validation():
            self.root.after(100, self._validate_datetime_range_realtime)
        
        # Podłącz eventy zmiany do walidacji
        date_entry.entry.bind('<KeyRelease>', lambda e: schedule_validation())
        hour_combo.bind('<<ComboboxSelected>>', lambda e: schedule_validation())
        minute_combo.bind('<<ComboboxSelected>>', lambda e: schedule_validation())
        second_combo.bind('<<ComboboxSelected>>', lambda e: schedule_validation())
        
        return date_entry, hour_combo, minute_combo, second_combo
    
    def _copy_datetime(self, source: Tuple, target: Tuple) -> None:
        """Kopiuje ustawienia daty i czasu między sekcjami"""
        source_date, source_hour, source_minute, source_second = source
        target_date, target_hour, target_minute, target_second = target
        
        target_date.entry.set(source_date.entry.get())
        target_hour.set(source_hour.get())
        target_minute.set(source_minute.get())
        target_second.set(source_second.get())
    
    def _create_datetime_sections(self) -> None:
        """Tworzy wszystkie sekcje wyboru daty i czasu"""
        # Sekcja T1
        frame_t1 = ttk.Labelframe(self.root, text="T1 (Rozpoczęcie zakupów)")
        frame_t1.grid(row=2, column=0, padx=self.padx, pady=self.pady, sticky="ew")
        
        self.T1_widgets = self._create_datetime_section(frame_t1, 0)
        
        # Przycisk kopiowania T1 do T2 i T3
        copy_t1_button = ttk.Button(
            frame_t1, text="Kopiuj niżej", width=17, style="secondary.TButton",
            command=self._copy_t1_to_all
        )
        copy_t1_button.grid(row=0, column=4, padx=self.padx, pady=self.pady, sticky="ew")
        
        # Sekcja T2
        frame_t2 = ttk.Labelframe(self.root, text="T2 (Zakończenie zakupów)")
        frame_t2.grid(row=3, column=0, padx=self.padx, pady=self.pady, sticky="ew")
        
        self.T2_widgets = self._create_datetime_section(frame_t2, 0)
        
        # Przycisk kopiowania T1 do T2
        copy_t1_to_t2_button = ttk.Button(
            frame_t2, text="Kopiuj z T1", width=17, style="secondary.TButton",
            command=self._copy_t1_to_t2
        )
        copy_t1_to_t2_button.grid(row=0, column=4, padx=self.padx, pady=self.pady, sticky="ew")
        
        # Sekcja T3
        frame_t3 = ttk.Labelframe(self.root, text="T3 (Data graniczna posiadania tokenów)")
        frame_t3.grid(row=4, column=0, padx=self.padx, pady=self.pady, sticky="ew")
        
        self.T3_widgets = self._create_datetime_section(frame_t3, 0)
        
        # Przycisk kopiowania T2 do T3
        copy_t2_to_t3_button = ttk.Button(
            frame_t3, text="Kopiuj z T2", width=17, style="secondary.TButton",
            command=self._copy_t2_to_t3
        )
        copy_t2_to_t3_button.grid(row=0, column=4, padx=self.padx, pady=self.pady, sticky="ew")
    
    def _copy_t1_to_all(self) -> None:
        """Kopiuje T1 do T2 i T3"""
        self._copy_datetime(self.T1_widgets, self.T2_widgets)
        self._copy_datetime(self.T1_widgets, self.T3_widgets)
    
    def _copy_t1_to_t2(self) -> None:
        """Kopiuje T1 do T2"""
        self._copy_datetime(self.T1_widgets, self.T2_widgets)
    
    def _copy_t2_to_t3(self) -> None:
        """Kopiuje T2 do T3"""
        self._copy_datetime(self.T2_widgets, self.T3_widgets)
        
    def _validate_datetime_range_realtime(self) -> None:
        """Waliduje przedziały czasowe w czasie rzeczywistym i pokazuje ostrzeżenie"""
        try:
            t1_str = self._get_datetime_string(self.T1_widgets)
            t2_str = self._get_datetime_string(self.T2_widgets)
            t3_str = self._get_datetime_string(self.T3_widgets)
            
            DateTimeHelper.validate_date_range(t1_str, t2_str, t3_str)
            
            # Usuń ostrzeżenie jeśli wszystko jest OK
            if hasattr(self, '_warning_label'):
                self._warning_label.destroy()
                delattr(self, '_warning_label')
                
        except ValueError:
            # Pokaż ostrzeżenie
            if not hasattr(self, '_warning_label'):
                self._warning_label = ttk.Label(
                    self.root, 
                    text="⚠️ Uwaga: T1 musi być ≤ T2 ≤ T3", 
                    style="warning.TLabel",
                    foreground="red"
                )
                self._warning_label.grid(row=5, column=0, padx=self.padx, pady=5, sticky="ew")
        except Exception:
            # Ignoruj inne błędy (np. niepoprawny format daty)
            pass
    
    def _create_network_section(self) -> None:
        """Tworzy sekcję wyboru sieci i przycisk uruchomienia"""
        frame_network = ttk.Frame(self.root)
        frame_network.grid(row=5, column=0, padx=self.padx, pady=self.pady, sticky="ew")
        
        # Konfiguracja kolumn
        frame_network.grid_columnconfigure(0, weight=0)
        frame_network.grid_columnconfigure(1, weight=1)
        frame_network.grid_columnconfigure(2, weight=0)
        frame_network.grid_columnconfigure(3, weight=0)
        
        # Etykieta i combobox sieci
        ttk.Label(frame_network, text="Wybierz sieć:").grid(
            row=0, column=0, padx=self.padx, pady=self.pady, sticky="w"
        )
        
        # Lista dostępnych sieci
        self.network_var = ttk.StringVar()
        network_codes = Constants.get_supported_networks()
        
        self.network_combo = ttk.Combobox(
            frame_network, textvariable=self.network_var,
            values=network_codes, state="readonly", width=25
        )
        self.network_combo.grid(row=0, column=1, padx=self.padx, pady=self.pady, sticky="w")
        
        # Ustaw domyślną wartość
        self.network_combo.set(Constants.DEFAULT_CONFIG["NETWORK"])
        
        # Przycisk uruchomienia
        self.run_button = ttk.Button(
            frame_network, text="Uruchom", width=35, style="danger.TButton",
            command=self._on_run_clicked
        )
        self.run_button.grid(row=0, column=3, padx=self.padx, pady=self.pady, sticky="e")
    
    def _get_datetime_string(self, widgets: Tuple) -> str:
        """Konwertuje widgety daty i czasu na string"""
        date_entry, hour_combo, minute_combo, second_combo = widgets
        date_str = date_entry.entry.get()
        time_str = f"{hour_combo.get()}:{minute_combo.get()}:{second_combo.get()}"
        return f"{date_str} {time_str}"
    
    def _save_config(self) -> bool:
        """Zapisuje aktualną konfigurację"""
        try:
            config_data = {
                "TOKEN_CONTRACT_ADDRESS": self.token_contract_entry.get().strip(),
                "T1_STR": self._get_datetime_string(self.T1_widgets),
                "T2_STR": self._get_datetime_string(self.T2_widgets),
                "T3_STR": self._get_datetime_string(self.T3_widgets),
                "NETWORK": self.network_var.get()
            }
            
            return self.config_manager.save_config(config_data)
        except Exception as e:
            print(f"Błąd zapisywania konfiguracji: {e}")
            return False
    
    def _validate_input(self) -> bool:
        """Waliduje dane wejściowe"""
        if not self.token_contract_entry.get().strip():
            messagebox.showerror("Błąd", "Proszę podać adres kontraktu tokena!")
            return False
        
        # Walidacja przedziałów czasowych T1 <= T2 <= T3
        try:
            t1_str = self._get_datetime_string(self.T1_widgets)
            t2_str = self._get_datetime_string(self.T2_widgets)
            t3_str = self._get_datetime_string(self.T3_widgets)
            
            DateTimeHelper.validate_date_range(t1_str, t2_str, t3_str)
        except ValueError as e:
            messagebox.showerror("Błąd walidacji dat\n\n")
            return False
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas walidacji dat: {str(e)}")
            return False
        
        return True
    
    def _on_run_clicked(self) -> None:
        """Obsługuje kliknięcie przycisku uruchomienia"""
        if not self._validate_input():
            return
        
        if not self._save_config():
            messagebox.showerror("Błąd", "Nie udało się zapisać konfiguracji!")
            return
        
        # Wyczyść logi
        self.log_widget.delete(1.0, tk.END)
        
        # Uruchom proces w osobnym wątku
        if self.main_function:
            self._start_process_thread()
    
    def _start_process_thread(self) -> None:
        """Uruchamia główny proces w osobnym wątku"""
        self.run_button.config(state="disabled", text="Uruchomiono...")
        
        def run_process():
            try:
                self.main_function()
                self._show_completion_message(success=True)
            except Exception as e:
                print(f"Błąd podczas wykonywania: {e}")
                self._show_completion_message(success=False, error_msg=str(e))
            finally:
                # Przywróć przycisk w głównym wątku
                self.root.after(0, self._reset_run_button)
        
        thread = threading.Thread(target=run_process, daemon=True)
        thread.start()
    
    def _reset_run_button(self) -> None:
        """Przywraca stan przycisku uruchomienia"""
        self.run_button.config(state="normal", text="Uruchom")
    
    def _show_completion_message(self, success: bool = True, error_msg: str = "") -> None:
        """Pokazuje komunikat o zakończeniu procesu"""
        if success:
            print("\\n✅ Proces zakończony pomyślnie!")
        else:
            print(f"\\n❌ Proces zakończony błędem: {error_msg}")
    
    def _load_saved_config(self) -> None:
        """Ładuje zapisaną konfigurację do interfejsu"""
        try:
            config = self.config_manager.config
            
            # Adres kontraktu
            token_address = config.get("TOKEN_CONTRACT_ADDRESS", Constants.DEFAULT_CONFIG["TOKEN_CONTRACT_ADDRESS"])
            self.token_contract_entry.insert(0, token_address)
            
            # Sieć
            network = config.get("NETWORK", "ETH")
            self.network_combo.set(network)
            
            # Daty i czasy
            self._load_datetime_config("T1_STR", self.T1_widgets, Constants.DEFAULT_CONFIG["T1_STR"])
            self._load_datetime_config("T2_STR", self.T2_widgets, Constants.DEFAULT_CONFIG["T2_STR"])
            self._load_datetime_config("T3_STR", self.T3_widgets, Constants.DEFAULT_CONFIG["T3_STR"])
            
        except Exception as e:
            print(f"Błąd ładowania konfiguracji: {e}")
    
    def _load_datetime_config(self, config_key: str, widgets: Tuple, default: str) -> None:
        """Ładuje konfigurację daty i czasu dla danej sekcji"""
        try:
            datetime_str = self.config_manager.get(config_key, default)
            date_part, time_part = datetime_str.split(" ", 1)
            hour, minute, second = time_part.split(":")
            
            date_entry, hour_combo, minute_combo, second_combo = widgets
            
            date_entry.entry.set(date_part)
            hour_combo.set(hour)
            minute_combo.set(minute)
            second_combo.set(second)
            
        except Exception as e:
            print(f"Błąd ładowania {config_key}: {e}")
    
    def run(self) -> None:
        """Uruchamia główną pętlę aplikacji"""
        self.root.mainloop()