import json
import ttkbootstrap as ttk
import FindWallets
from ttkbootstrap.widgets import DateEntry
from datetime import datetime

CONFIG_FILE = "config.json"

def create_time_combobox(parent, values):
    combo = ttk.Combobox(parent, values=values, width=3, state="readonly", bootstyle="info")
    combo.current(0)
    return combo

def create_datetime_section(parent, label_text, row, initial_date=None):
    ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="e", padx=padx, pady=pady)
    
    # Ustaw format daty na "YYYY-MM-DD" i styl przycisku kalendarza
    date_entry = DateEntry(parent, width=12, firstweekday=1, dateformat="%Y-%m-%d", bootstyle="info")
    date_entry.grid(row=row, column=1, padx=padx, pady=pady)

    # Ustaw datę początkową, jeśli jest podana
    if initial_date:
        date_entry.entry.delete(0, 'end')
        date_entry.entry.insert(0, initial_date.strftime("%Y-%m-%d"))

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

def save_and_run():
    network = network_var.get()
    
    def get_datetime(date_entry, hour_combo, minute_combo, second_combo):
        # Pobierz datę jako tekst z pola DateEntry
        date_str = date_entry.entry.get()  # Użyj entry.get() zamiast get()
        try:
            # Parsuj datę z formatu "YYYY-MM-DD"
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Błędny format daty: {date_str}. Oczekiwano formatu YYYY-MM-DD.")
        
        hour = int(hour_combo.get())
        minute = int(minute_combo.get())
        second = int(second_combo.get())
        dt = datetime(date.year, date.month, date.day, hour, minute, second)
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

    

root = ttk.Window(title="Konfiguracja skryptu blockchain", themename="flatly")
root.minsize(600, 400)

padx = 5
pady = 5

# --- Adres kontraktu tokena (na górze) ---
ttk.Label(root, text="Adres kontraktu:").grid(row=0, column=0, sticky="e", padx=padx, pady=pady)
token_contract_entry = ttk.Entry(root, width=40)
token_contract_entry.grid(row=0, column=1, columnspan=4, padx=padx, pady=pady)

def copy_datetime(source, target):
    source_date, source_hour, source_minute, source_second = source
    target_date, target_hour, target_minute, target_second = target
    
    # Copy date
    target_date.entry.delete(0, 'end')
    target_date.entry.insert(0, source_date.entry.get())
    
    # Copy time
    target_hour.set(source_hour.get())
    target_minute.set(source_minute.get())
    target_second.set(source_second.get())

# --- Sekcja T1 ---
frame_t1 = ttk.Labelframe(root, text="T1 (Rozpoczęcie zakupów)")
frame_t1.grid(row=1, column=0, columnspan=5, padx=padx, pady=pady, sticky="ew")
T1_date, T1_hour, T1_minute, T1_second = create_datetime_section(frame_t1, "Wybierz T1:", row=0)

# Dodaj przycisk kopiowania daty i czasu z T1 do T2 i T3
copy_t1_to_t2_t3_button = ttk.Button(frame_t1, text="Kopiuj niżej", width=8, style="secondary.TButton", command=lambda: [
    copy_datetime((T1_date, T1_hour, T1_minute, T1_second), (T2_date, T2_hour, T2_minute, T2_second)),
    copy_datetime((T1_date, T1_hour, T1_minute, T1_second), (T3_date, T3_hour, T3_minute, T3_second))
])
copy_t1_to_t2_t3_button.grid(row=0, column=5, padx=padx, pady=pady)

# --- Sekcja T2 ---
frame_t2 = ttk.Labelframe(root, text="T2 (Zakończenie zakupów)")
frame_t2.grid(row=2, column=0, columnspan=5, padx=padx, pady=pady, sticky="ew")
T2_date, T2_hour, T2_minute, T2_second = create_datetime_section(frame_t2, "Wybierz T2:", row=0)

# Dodaj przycisk kopiowania daty i czasu z T1 do T2
copy_t1_to_t2_button = ttk.Button(frame_t2, text="Kopiuj z T1", width=8, style="secondary.TButton", command=lambda: copy_datetime(
    (T1_date, T1_hour, T1_minute, T1_second),
    (T2_date, T2_hour, T2_minute, T2_second)
))
copy_t1_to_t2_button.grid(row=0, column=5, padx=padx, pady=pady)

# --- Sekcja T3 ---
frame_t3 = ttk.Labelframe(root, text="T3 (Data graniczna posiadania tokenów)")
frame_t3.grid(row=3, column=0, columnspan=5, padx=padx, pady=pady, sticky="ew")
T3_date, T3_hour, T3_minute, T3_second = create_datetime_section(frame_t3, "Wybierz T3:", row=0)

# Dodaj przycisk kopiowania daty i czasu z T2 do T3
copy_t2_to_t3_button = ttk.Button(frame_t3, text="Kopiuj z T2", width=8, style="secondary.TButton", command=lambda: copy_datetime(
    (T2_date, T2_hour, T2_minute, T2_second),
    (T3_date, T3_hour, T3_minute, T3_second)
))
copy_t2_to_t3_button.grid(row=0, column=5, padx=padx, pady=pady)

# --- Sieć i przycisk Uruchom (na dole) ---
ttk.Label(root, text="Wybierz sieć:").grid(row=4, column=0, sticky="e", padx=padx, pady=pady)
network_var = ttk.StringVar()
network_combo = ttk.Combobox(root, textvariable=network_var, values=["ETH", "BASE", "BNB"], state="readonly", width=10)
network_combo.grid(row=4, column=1, padx=padx, pady=pady, sticky="w")  # Przesunięcie bardziej w lewo
network_combo.current(0)

run_button = ttk.Button(root, text="Uruchom", width=20, style="danger.TButton", command=save_and_run)
run_button.grid(row=4, column=2, padx=padx, pady=pady, sticky="w")  # Przycisk obok wyboru sieci

try:
    with open(CONFIG_FILE, "r") as f:
        saved_config = json.load(f)
        network_var.set(saved_config.get("NETWORK", "ETH"))
        
        for (date_entry, hour_c, min_c, sec_c), key in zip(
            [(T1_date, T1_hour, T1_minute, T1_second),
             (T2_date, T2_hour, T2_minute, T2_second),
             (T3_date, T3_hour, T3_minute, T3_second)],
            ["T1_STR", "T2_STR", "T3_STR"]
        ):
            dt_str = saved_config.get(key)
            if dt_str:
                try:
                    dt = datetime.strptime(dt_str, "%d-%m-%Y %H:%M:%S")
                    date_entry.entry.delete(0, 'end')  # Wyczyść pole daty
                    date_entry.entry.insert(0, dt.strftime("%Y-%m-%d"))  # Wstaw datę w odpowiednim formacie
                    hour_c.set(f"{dt.hour:02d}")
                    min_c.set(f"{dt.minute:02d}")
                    sec_c.set(f"{dt.second:02d}")
                except ValueError:
                    print(f"Błędny format daty dla {key}: {dt_str}")
        
        token_contract_entry.delete(0, 'end')
        token_contract_entry.insert(0, saved_config.get("TOKEN_CONTRACT_ADDRESS", ""))
        
except FileNotFoundError:
    print("Plik config.json nie istnieje. Ustawienia domyślne.")
except Exception as e:
    print("Nieoczekiwany błąd:", e)

root.mainloop()
