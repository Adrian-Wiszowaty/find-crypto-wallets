import json
import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime

# Zakładamy, że funkcja main() z Twojego głównego skryptu jest dostępna.
# Jeśli jest w tym samym module, nie musisz importować; inaczej dostosuj import.
from FindWallets import main  # <-- zamień 'your_main_module' na nazwę modułu z funkcją main()

CONFIG_FILE = "config.json"

# Funkcja pomocnicza do tworzenia comboboxu z zakresu wartości (np. godziny, minuty, sekundy)
def create_time_combobox(parent, values):
    combo = ttk.Combobox(parent, values=values, width=3, state="readonly")
    combo.current(0)
    return combo

def save_and_run():
    # Pobieramy sieć
    network = network_var.get()
    
    # Pobieramy daty i czasy dla T1, T2, T3
    # Używamy DateEntry z tkcalendar do wyboru daty
    def get_datetime(date_entry, hour_combo, minute_combo, second_combo):
        # pobieramy datę z widgetu DateEntry i łączymy z wybranymi wartościami czasu
        date = date_entry.get_date()  # typ date
        hour = int(hour_combo.get())
        minute = int(minute_combo.get())
        second = int(second_combo.get())
        dt = datetime(date.year, date.month, date.day, hour, minute, second)
        # Format wyjściowy zgodny z wcześniejszym zapisem (np. DD-MM-YYYY HH:MM:SS)
        return dt.strftime("%d-%m-%Y %H:%M:%S")
    
    T1_str = get_datetime(T1_date, T1_hour, T1_minute, T1_second)
    T2_str = get_datetime(T2_date, T2_hour, T2_minute, T2_second)
    T3_str = get_datetime(T3_date, T3_hour, T3_minute, T3_second)
    
    token_contract = token_contract_entry.get().strip()
    
    config = {
        "NETWORK": network,
        "T1_STR": T1_str,
        "T2_STR": T2_str,
        "T3_STR": T3_str,
        "TOKEN_CONTRACT_ADDRESS": token_contract
    }
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    
    print("Konfiguracja zapisana w", CONFIG_FILE)
    # Wywołujemy funkcję main() z głównego skryptu
    main()

# Główne okno
root = tk.Tk()
root.title("Konfiguracja skryptu blockchain")

# Definiujemy padding do rozmieszczenia widgetów
padx = 5
pady = 5

# --- Sieć ---
tk.Label(root, text="Wybierz sieć:").grid(row=0, column=0, sticky="e", padx=padx, pady=pady)
network_var = tk.StringVar()
network_combo = ttk.Combobox(root, textvariable=network_var, values=["ETH", "BASE", "BNB"], state="readonly", width=10)
network_combo.grid(row=0, column=1, padx=padx, pady=pady)
network_combo.current(0)

# Funkcja pomocnicza do tworzenia sekcji daty/czasu
def create_datetime_section(parent, label_text, row):
    tk.Label(parent, text=label_text).grid(row=row, column=0, sticky="e", padx=padx, pady=pady)
    # DateEntry z tkcalendar – pamiętaj, żeby mieć zainstalowany moduł tkcalendar (pip install tkcalendar)
    date_entry = DateEntry(parent, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd-mm-yyyy')
    date_entry.grid(row=row, column=1, padx=padx, pady=pady)
    
    # Comboboxy dla godziny, minuty, sekundy
    hours = [f"{i:02d}" for i in range(24)]
    minutes = [f"{i:02d}" for i in range(60)]
    seconds = [f"{i:02d}" for i in range(60)]
    
    hour_combo = create_time_combobox(parent, hours)
    hour_combo.grid(row=row, column=2, padx=padx, pady=pady)
    minute_combo = create_time_combobox(parent, minutes)
    minute_combo.grid(row=row, column=3, padx=padx, pady=pady)
    second_combo = create_time_combobox(parent, seconds)
    second_combo.grid(row=row, column=4, padx=padx, pady=pady)
    
    return date_entry, hour_combo, minute_combo, second_combo

# --- T1 ---
T1_date, T1_hour, T1_minute, T1_second = create_datetime_section(root, "T1 (data i czas):", row=1)

# --- T2 ---
T2_date, T2_hour, T2_minute, T2_second = create_datetime_section(root, "T2 (data i czas):", row=2)

# --- T3 ---
T3_date, T3_hour, T3_minute, T3_second = create_datetime_section(root, "T3 (data i czas):", row=3)

# --- Kontrakt tokena ---
tk.Label(root, text="Adres kontraktu tokena:").grid(row=4, column=0, sticky="e", padx=padx, pady=pady)
token_contract_entry = tk.Entry(root, width=30)
token_contract_entry.grid(row=4, column=1, columnspan=4, padx=padx, pady=pady)

# --- Przycisk Uruchom ---
run_button = tk.Button(root, text="Uruchom", command=save_and_run, width=20)
run_button.grid(row=5, column=0, columnspan=5, pady=15)

# Jeśli chcesz, możesz załadować poprzednio zapisane ustawienia, jeśli plik config.json istnieje
try:
    with open(CONFIG_FILE, "r") as f:
        saved_config = json.load(f)
        network_var.set(saved_config.get("NETWORK", "ETH"))
        # Dla dat – zakładamy, że format to "DD-MM-YYYY HH:MM:SS"
        for dt_entry, key in zip([T1_date, T2_date, T3_date], ["T1_STR", "T2_STR", "T3_STR"]):
            dt_str = saved_config.get(key)
            if dt_str:
                dt = datetime.strptime(dt_str, "%d-%m-%Y %H:%M:%S")
                dt_entry.set_date(dt)
        # Dla czasu – musimy ustawić comboboxy oddzielnie
        def set_time(dt_str, hour_combo, minute_combo, second_combo):
            if dt_str:
                dt = datetime.strptime(dt_str, "%d-%m-%Y %H:%M:%S")
                hour_combo.set(f"{dt.hour:02d}")
                minute_combo.set(f"{dt.minute:02d}")
                second_combo.set(f"{dt.second:02d}")
        set_time(saved_config.get("T1_STR"), T1_hour, T1_minute, T1_second)
        set_time(saved_config.get("T2_STR"), T2_hour, T2_minute, T2_second)
        set_time(saved_config.get("T3_STR"), T3_hour, T3_minute, T3_second)
        
        token_contract_entry.insert(0, saved_config.get("TOKEN_CONTRACT_ADDRESS", ""))
except Exception as e:
    print("Brak zapisanego pliku konfiguracyjnego lub błąd podczas odczytu:", e)

root.mainloop()
