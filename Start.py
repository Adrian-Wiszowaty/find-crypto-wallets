import json
import os
import threading
import sys
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.widgets import DateEntry
from datetime import datetime
from tkinter import Text, messagebox
from FindWallets import main as find_wallets_main
from LogRedirector import LogRedirector

# ======================= KONFIGURACJA =======================
CONFIG_FILE = "config.json"
padx = 5
pady = 5

# ======================= FUNKCJE POMOCNICZE =======================
def create_time_combobox(parent, values):
    combo = ttk.Combobox(parent, values=values, width=3, state="readonly", bootstyle="info")
    combo.current(0)
    return combo

def create_datetime_section(parent, label_text, row, initial_date=None):
    frame = ttk.Frame(parent)
    frame.pack(padx=padx, pady=pady, fill="x")
    
    ttk.Label(frame, text=label_text).pack(side="left", padx=padx, pady=pady)
    
    date_entry = DateEntry(frame, width=12, firstweekday=1, dateformat="%Y-%m-%d", bootstyle="info")
    date_entry.pack(side="left", padx=padx, pady=pady)
    
    if initial_date:
        date_entry.entry.delete(0, 'end')
        date_entry.entry.insert(0, initial_date.strftime("%Y-%m-%d"))
        
    hours = [f"{i:02d}" for i in range(24)]
    minutes = [f"{i:02d}" for i in range(60)]
    seconds = [f"{i:02d}" for i in range(60)]
    hour_combo = create_time_combobox(frame, hours)
    hour_combo.pack(side="left", padx=padx, pady=pady)
    minute_combo = create_time_combobox(frame, minutes)
    minute_combo.pack(side="left", padx=padx, pady=pady)
    second_combo = create_time_combobox(frame, seconds)
    second_combo.pack(side="left", padx=padx, pady=pady)
    
    return date_entry, hour_combo, minute_combo, second_combo

def copy_datetime(source, target):
    source_date, source_hour, source_minute, source_second = source
    target_date, target_hour, target_minute, target_second = target
    target_date.entry.delete(0, 'end')
    target_date.entry.insert(0, source_date.entry.get())
    target_hour.set(source_hour.get())
    target_minute.set(source_minute.get())
    target_second.set(source_second.get())

# ======================= LOGIKA URUCHAMIANIA =======================
def save_and_run(log_widget):
    network = network_var.get()
    run_button.config(state="disabled")
    
    def get_datetime(date_entry, hour_combo, minute_combo, second_combo):
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
    
    log_widget.insert(tk.END, "Konfiguracja zapisana\n")
    log_widget.yview(tk.END)
    
    # Uruchomienie funkcji main w oddzielnym wątku, aby nie blokować GUI
    threading.Thread(target=run_process, args=(log_widget,), daemon=True).start()

def run_process(log_widget):
    try:
        # Uruchomienie funkcji main z FindWallets
        find_wallets_main()
        log_widget.insert(tk.END, "Operacja zakończona pomyślnie!\n")
        log_widget.yview(tk.END)
        
        # Dźwięk sukcesu
        if os.name == 'nt':
            import winsound
            winsound.Beep(1000, 500)
        else:
            os.system("afplay /System/Library/Sounds/Pop.aiff")
        
        messagebox.showinfo("Sukces", "Operacja zakończona pomyślnie!")
    except Exception as e:
        log_widget.insert(tk.END, f"Błąd: {str(e)}\n")
        log_widget.yview(tk.END)
        
        # Dźwięk błędu
        if os.name == 'nt':
            import winsound
            winsound.Beep(200, 500)
        else:
            os.system("afplay /System/Library/Sounds/Basso.aiff")
        
        messagebox.showerror("Błąd", f"Coś poszło nie tak: {str(e)}")
    run_button.config(state="normal")

# ======================= GŁÓWNE OKNO APLIKACJI =======================
root = ttk.Window(title="Konfiguracja skryptu blockchain", themename="flatly")
root.minsize(600, 400)

# --- Okno logów na górze ---
log_widget = Text(root, height=15, width=70)
log_widget.pack(padx=padx, pady=5, fill="x")
# Przekierowanie stdout do widgetu logów
sys.stdout = LogRedirector(log_widget)

# --- Adres kontraktu tokena ---
frame_contract = ttk.Frame(root)
frame_contract.pack(fill="x", padx=padx, pady=pady)
ttk.Label(frame_contract, text="Adres kontraktu:").pack(side="left", padx=padx, pady=pady)
token_contract_entry = ttk.Entry(frame_contract, width=40)
token_contract_entry.pack(side="left", padx=padx, pady=pady)

# --- Sekcja T1 ---
frame_t1 = ttk.Labelframe(root, text="T1 (Rozpoczęcie zakupów)")
frame_t1.pack(padx=padx, pady=pady, fill="x")
T1_date, T1_hour, T1_minute, T1_second = create_datetime_section(frame_t1, "Wybierz T1:", row=0)
copy_t1_to_t2_t3_button = ttk.Button(
    frame_t1, text="Kopiuj niżej", width=8, style="secondary.TButton",
    command=lambda: [
        copy_datetime((T1_date, T1_hour, T1_minute, T1_second), (T2_date, T2_hour, T2_minute, T2_second)),
        copy_datetime((T1_date, T1_hour, T1_minute, T1_second), (T3_date, T3_hour, T3_minute, T3_second))
    ]
)
copy_t1_to_t2_t3_button.pack(side="left", padx=padx, pady=pady)

# --- Sekcja T2 ---
frame_t2 = ttk.Labelframe(root, text="T2 (Zakończenie zakupów)")
frame_t2.pack(padx=padx, pady=pady, fill="x")
T2_date, T2_hour, T2_minute, T2_second = create_datetime_section(frame_t2, "Wybierz T2:", row=0)
copy_t1_to_t2_button = ttk.Button(
    frame_t2, text="Kopiuj z T1", width=8, style="secondary.TButton",
    command=lambda: copy_datetime(
        (T1_date, T1_hour, T1_minute, T1_second),
        (T2_date, T2_hour, T2_minute, T2_second)
    )
)
copy_t1_to_t2_button.pack(side="left", padx=padx, pady=pady)

# --- Sekcja T3 ---
frame_t3 = ttk.Labelframe(root, text="T3 (Data graniczna posiadania tokenów)")
frame_t3.pack(padx=padx, pady=pady, fill="x")
T3_date, T3_hour, T3_minute, T3_second = create_datetime_section(frame_t3, "Wybierz T3:", row=0)
copy_t2_to_t3_button = ttk.Button(
    frame_t3, text="Kopiuj z T2", width=8, style="secondary.TButton",
    command=lambda: copy_datetime(
        (T2_date, T2_hour, T2_minute, T2_second),
        (T3_date, T3_hour, T3_minute, T3_second)
    )
)
copy_t2_to_t3_button.pack(side="left", padx=padx, pady=pady)

# --- Wybór sieci i przycisk Uruchom ---
frame_network = ttk.Frame(root)
frame_network.pack(fill="x", padx=padx, pady=pady)
ttk.Label(frame_network, text="Wybierz sieć:").pack(side="left", padx=padx, pady=pady)
network_var = ttk.StringVar()
network_combo = ttk.Combobox(
    frame_network, textvariable=network_var,
    values=["ETH", "BASE", "BNB"], state="readonly", width=10
)
network_combo.pack(side="left", padx=padx, pady=pady)
network_combo.current(0)

run_button = ttk.Button(
    root, text="Uruchom", width=20, style="danger.TButton",
    command=lambda: save_and_run(log_widget)
)
run_button.pack(padx=padx, pady=pady)

# --- Wczytanie zapisanej konfiguracji, jeśli istnieje ---
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
                    date_entry.entry.delete(0, 'end')
                    date_entry.entry.insert(0, dt.strftime("%Y-%m-%d"))
                    hour_c.set(f"{dt.hour:02d}")
                    min_c.set(f"{dt.minute:02d}")
                    sec_c.set(f"{dt.second:02d}")
                except ValueError:
                    log_widget.insert(tk.END, f"Błędny format daty dla {key}: {dt_str}\n")
                    log_widget.yview(tk.END)
        token_contract_entry.delete(0, 'end')
        token_contract_entry.insert(0, saved_config.get("TOKEN_CONTRACT_ADDRESS", ""))
except FileNotFoundError:
    log_widget.insert(tk.END, "Plik config.json nie istnieje. Ustawienia domyślne.\n")
    log_widget.yview(tk.END)
except Exception as e:
    log_widget.insert(tk.END, f"Nieoczekiwany błąd: {e}\n")
    log_widget.yview(tk.END)

# Uruchomienie GUI
root.mainloop()
