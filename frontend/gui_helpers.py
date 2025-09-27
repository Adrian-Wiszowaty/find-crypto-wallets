"""
Funkcje pomocnicze dla interfejsu graficznego.
Centralizuje wspólne operacje GUI między różnymi widokami.
"""
import os
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.widgets import DateEntry
from datetime import datetime
from typing import Tuple, List
from shared.constants import Constants
from shared.datetime_helper import DateTimeHelper


class GUIHelpers:
    """Klasa z funkcjami pomocniczymi dla interfejsu graficznego"""
    
    @staticmethod
    def create_time_combobox(parent: tk.Widget, values: List[str]) -> ttk.Combobox:
        """Tworzy combobox dla wyboru czasu (godziny, minuty, sekundy)"""
        combo = ttk.Combobox(parent, values=values, width=3, state="readonly", style="info.TCombobox")
        combo.current(0)
        return combo
    
    @staticmethod
    def create_datetime_section(parent: tk.Widget, label_text: str, row: int, 
                              initial_date: datetime = None, padx: int = 5, pady: int = 5) -> Tuple[DateEntry, ttk.Combobox, ttk.Combobox, ttk.Combobox]:
        """
        Tworzy sekcję do wyboru daty i czasu.
        
        Returns:
            Tuple[DateEntry, hour_combo, minute_combo, second_combo]
        """
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, padx=padx, pady=pady, sticky="ew")
        
        # Konfiguracja kolumn w ramce
        frame.grid_columnconfigure(0, weight=0)  # Label
        frame.grid_columnconfigure(1, weight=1)  # DateEntry - elastyczna
        frame.grid_columnconfigure(2, weight=0)  # Godziny
        frame.grid_columnconfigure(3, weight=0)  # Minuty
        frame.grid_columnconfigure(4, weight=0)  # Sekundy

        ttk.Label(frame, text=label_text).grid(row=0, column=0, padx=padx, pady=pady, sticky="w")
        
        date_entry = DateEntry(frame, width=12, firstweekday=1, dateformat="%Y-%m-%d", bootstyle="info")
        date_entry.grid(row=0, column=1, padx=padx, pady=pady, sticky="ew")
        
        if initial_date:
            date_entry.entry.delete(0, 'end')
            date_entry.entry.insert(0, initial_date.strftime("%Y-%m-%d"))
            
        # Tworzenie combobox'ów dla czasu
        hours = [f"{i:02d}" for i in range(24)]
        minutes = [f"{i:02d}" for i in range(60)]
        seconds = [f"{i:02d}" for i in range(60)]
        
        hour_combo = GUIHelpers.create_time_combobox(frame, hours)
        hour_combo.grid(row=0, column=2, padx=padx, pady=pady, sticky="w")
        
        minute_combo = GUIHelpers.create_time_combobox(frame, minutes)
        minute_combo.grid(row=0, column=3, padx=padx, pady=pady, sticky="w")
        
        second_combo = GUIHelpers.create_time_combobox(frame, seconds)
        second_combo.grid(row=0, column=4, padx=padx, pady=pady, sticky="w")
        
        return date_entry, hour_combo, minute_combo, second_combo

    @staticmethod
    def copy_datetime_values(source: Tuple, target: Tuple) -> None:
        """
        Kopiuje wartości datetime między widget'ami.
        
        Args:
            source: Tupla (date_entry, hour_combo, minute_combo, second_combo)
            target: Tupla (date_entry, hour_combo, minute_combo, second_combo)
        """
        source_date, source_hour, source_minute, source_second = source
        target_date, target_hour, target_minute, target_second = target
        
        target_date.entry.delete(0, 'end')
        target_date.entry.insert(0, source_date.entry.get())
        target_hour.set(source_hour.get())
        target_minute.set(source_minute.get())
        target_second.set(source_second.get())

    @staticmethod
    def get_datetime_string(widgets: Tuple) -> str:
        """
        Konwertuje wartości z widget'ów datetime na string.
        
        Args:
            widgets: Tupla (date_entry, hour_combo, minute_combo, second_combo)
            
        Returns:
            str: Data w formacie DD-MM-YYYY HH:MM:SS
            
        Raises:
            ValueError: Gdy format daty jest niepoprawny
        """
        date_entry, hour_combo, minute_combo, second_combo = widgets
        date_str = date_entry.entry.get()
        
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Błędny format daty: {date_str}. Oczekiwano formatu YYYY-MM-DD.")
        
        hour = int(hour_combo.get())
        minute = int(minute_combo.get())
        second = int(second_combo.get())
        
        dt = datetime(date.year, date.month, date.day, hour, minute, second)
        return dt.strftime("%d-%m-%Y %H:%M:%S")
    
    @staticmethod
    def setup_icon(window: tk.Tk, icon_path: str) -> bool:
        """
        Ustawia ikonę dla okna aplikacji.
        
        Args:
            window: Okno aplikacji
            icon_path: Ścieżka do pliku ikony
            
        Returns:
            bool: True jeśli ikona została ustawiona pomyślnie
        """
        try:
            if os.path.exists(icon_path):
                from tkinter import PhotoImage
                icon_image = PhotoImage(file=icon_path)
                window.iconphoto(True, icon_image)
                return True
            else:
                print(f"Plik ikony nie został znaleziony: {icon_path}")
                return False
        except Exception as e:
            print(f"Błąd podczas ustawiania ikony: {e}")
            return False
    
    @staticmethod
    def configure_ttk_style() -> None:
        """Konfiguruje style dla ttkbootstrap"""
        style = ttk.Style()
        style.configure("info.TCombobox",
                       fieldbackground="white",
                       bordercolor=style.colors.info,
                       arrowcolor=style.colors.info)
        style.map("info.TCombobox", fieldbackground=[("readonly", "white")])
    
    @staticmethod
    def validate_datetime_widgets(t1_widgets: Tuple, t2_widgets: Tuple, t3_widgets: Tuple) -> bool:
        """
        Waliduje czy przedziały czasowe T1, T2, T3 spełniają warunek T1 <= T2 <= T3.
        
        Args:
            t1_widgets: Tupla (date_entry, hour_combo, minute_combo, second_combo) dla T1
            t2_widgets: Tupla (date_entry, hour_combo, minute_combo, second_combo) dla T2
            t3_widgets: Tupla (date_entry, hour_combo, minute_combo, second_combo) dla T3
            
        Returns:
            bool: True jeśli walidacja przeszła pomyślnie
            
        Raises:
            ValueError: Gdy przedziały są niepoprawne
        """
        try:
            t1_str = GUIHelpers.get_datetime_string(t1_widgets)
            t2_str = GUIHelpers.get_datetime_string(t2_widgets)
            t3_str = GUIHelpers.get_datetime_string(t3_widgets)
            
            return DateTimeHelper.validate_date_range(t1_str, t2_str, t3_str)
        except Exception as e:
            raise ValueError(f"Błąd walidacji GUI: {e}")