import json
import os
os.environ["TK_SILENCE_DEPRECATION"] = "1"
import threading
import sys
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.widgets import DateEntry
from datetime import datetime
from tkinter import Text,  messagebox
from FindWallets import main as find_wallets_main
from LogRedirector import LogRedirector
from ttkbootstrap.window import Icon
import os

# Ścieżka do katalogu, w którym znajduje się aktualny skrypt
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Utworzenie ścieżki do config.json w tym samym katalogu co skrypt
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# ======================= KONFIGURACJA =======================
padx = 5
pady = 5

# ======================= GŁÓWNE OKNO APLIKACJI =======================
minimal_gif = "R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="

Icon.icon = minimal_gif
root = ttk.Window(title="Find Wallets", themename="flatly")
root.minsize(600, 400)
root.grid_columnconfigure(0, weight=1, uniform="equal")  # Sprawia, że kolumna 0 (gdzie znajdują się widgety) jest elastyczna
style = ttk.Style()
style.configure("info.TCombobox",
                fieldbackground="white",
                bordercolor=style.colors.info,
                arrowcolor=style.colors.info)
style.map("info.TCombobox", fieldbackground=[("readonly", "white")])



# ======================= FUNKCJE POMOCNICZE =======================
def create_time_combobox(parent, values):
    combo = ttk.Combobox(parent, values=values, width=3, state="readonly", style="info.TCombobox")
    combo.current(0)
    return combo

def create_datetime_section(parent, label_text, row, initial_date=None):
    frame = ttk.Frame(parent)
    frame.grid(row=row, column=0, padx=padx, pady=pady, sticky="ew")
    
    # Konfiguracja kolumn w ramce, aby tylko DateEntry rozciągało się na całą szerokość
    frame.grid_columnconfigure(0, weight=0)  # Stała szerokość dla labela
    frame.grid_columnconfigure(1, weight=1)  # Elastyczna szerokość dla DateEntry
    frame.grid_columnconfigure(2, weight=0)  # Stała szerokość dla godzin
    frame.grid_columnconfigure(3, weight=0)  # Stała szerokość dla minut
    frame.grid_columnconfigure(4, weight=0)  # Stała szerokość dla sekund

    ttk.Label(frame, text=label_text).grid(row=0, column=0, padx=padx, pady=pady, sticky="w")
    
    date_entry = DateEntry(frame, width=12, firstweekday=1, dateformat="%Y-%m-%d", bootstyle="info")
    date_entry.grid(row=0, column=1, padx=padx, pady=pady, sticky="ew")  # Zmieniono sticky na "ew"
    
    if initial_date:
        date_entry.entry.delete(0, 'end')
        date_entry.entry.insert(0, initial_date.strftime("%Y-%m-%d"))
        
    hours = [f"{i:02d}" for i in range(24)]
    minutes = [f"{i:02d}" for i in range(60)]
    seconds = [f"{i:02d}" for i in range(60)]
    hour_combo = create_time_combobox(frame, hours)
    hour_combo.grid(row=0, column=2, padx=padx, pady=pady, sticky="w")
    minute_combo = create_time_combobox(frame, minutes)
    minute_combo.grid(row=0, column=3, padx=padx, pady=pady, sticky="w")
    second_combo = create_time_combobox(frame, seconds)
    second_combo.grid(row=0, column=4, padx=padx, pady=pady, sticky="w")
    
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

def play_sound(success=True):
    """ Odtwarza dźwięk w zależności od wyniku operacji """
    if os.name == 'nt':
        import winsound
        freq, dur = (1000, 500) if success else (200, 500)
        winsound.Beep(freq, dur)
    else:
        sound_file = "/System/Library/Sounds/Pop.aiff" if success else "/System/Library/Sounds/Basso.aiff"
        os.system(f"afplay {sound_file}")

def show_message(success=True, error_msg=""):
    """ Wyświetla komunikat i odtwarza dźwięk jednocześnie """
    threading.Thread(target=play_sound, args=(success,), daemon=True).start()
    if success:
        messagebox.showinfo("Sukces", "Operacja zakończona pomyślnie!")
    else:
        messagebox.showerror("Błąd", f"Coś poszło nie tak: {error_msg}")

def run_process(log_widget):
    """ Uruchamia główną operację i obsługuje logi oraz powiadomienia """
    try:
        # Wyłączenie przycisku, aby zapobiec ponownemu kliknięciu
        run_button.config(state="disabled")

        # Uruchomienie funkcji main z FindWallets
        find_wallets_main()

        log_widget.insert(tk.END, "Operacja zakończona pomyślnie!\n")
        log_widget.yview(tk.END)

        show_message(success=True)
    except Exception as e:
        log_widget.insert(tk.END, f"Błąd: {str(e)}\n")
        log_widget.yview(tk.END)

        show_message(success=False, error_msg=str(e))
    
    # Ponowne włączenie przycisku po zakończeniu operacji
    run_button.config(state="normal")

def start_process_thread(log_widget, run_button):
    """ Uruchamia funkcję w osobnym wątku """
    threading.Thread(target=run_process, args=(log_widget, run_button), daemon=True).start()

# --- Okno logów na górze z czarnym tłem i białym tekstem ---
log_widget = Text(root, height=15, width=70)
log_widget.grid(row=0, column=0, padx=padx, pady=5, columnspan=2, sticky="ew")
log_widget.config(bg="black", fg="white", insertbackground="white")

# Przekierowanie stdout do widgetu logów
sys.stdout = LogRedirector(log_widget)

# --- Sekcja Adres kontraktu tokena (analogicznie jak T1, T2, T3) ---
frame_contract = ttk.Labelframe(root, text="Token")
frame_contract.grid(row=1, column=0, padx=padx, pady=pady, sticky="ew")
frame_contract.grid_columnconfigure(1, weight=1)  # Kolumna z polem edycji

ttk.Label(frame_contract, text="Adres kontraktu:").grid(row=0, column=0, padx=padx, pady=pady, sticky="w")
token_contract_entry = ttk.Entry(frame_contract, width=40)
token_contract_entry.grid(row=0, column=1, padx=padx, pady=pady, sticky="ew")

# Sekcja T1
frame_t1 = ttk.Labelframe(root, text="T1 (Rozpoczęcie zakupów)")
frame_t1.grid(row=2, column=0, padx=padx, pady=pady, sticky="ew")
frame_t1.grid_columnconfigure(0, weight=0)  # Kolumna 0 bez wagi
frame_t1.grid_columnconfigure(1, weight=0)  # Kolumna 1 bez wagi
frame_t1.grid_columnconfigure(2, weight=0)  # Kolumna 2 bez wagi
frame_t1.grid_columnconfigure(3, weight=0)  # Kolumna 3 bez wagi
frame_t1.grid_columnconfigure(4, weight=0)  # Kolumna 4 bez wagi

T1_date, T1_hour, T1_minute, T1_second = create_datetime_section(frame_t1, "Wybierz T1:", row=0)

# Przyciski kopiowania
copy_t1_to_t2_t3_button = ttk.Button(
    frame_t1, text="Kopiuj niżej", width=17, style="secondary.TButton",  # Stała szerokość
    command=lambda: [
        copy_datetime((T1_date, T1_hour, T1_minute, T1_second), (T2_date, T2_hour, T2_minute, T2_second)),
        copy_datetime((T1_date, T1_hour, T1_minute, T1_second), (T3_date, T3_hour, T3_minute, T3_second))
    ]
)
copy_t1_to_t2_t3_button.grid(row=0, column=2, padx=padx, pady=pady, sticky="ew", columnspan=2)  # Wyśrodkowanie w kolumnie


# Sekcja T2
frame_t2 = ttk.Labelframe(root, text="T2 (Zakończenie zakupów)")
frame_t2.grid(row=3, column=0, padx=padx, pady=pady, sticky="ew")
frame_t2.grid_columnconfigure(0, weight=0)  # Kolumna 0 bez wagi
frame_t2.grid_columnconfigure(1, weight=0)  # Kolumna 1 bez wagi
frame_t2.grid_columnconfigure(2, weight=0)  # Kolumna 2 bez wagi
frame_t2.grid_columnconfigure(3, weight=0)  # Kolumna 3 bez wagi
frame_t2.grid_columnconfigure(4, weight=0)  # Kolumna 4 bez wagi

T2_date, T2_hour, T2_minute, T2_second = create_datetime_section(frame_t2, "Wybierz T2:", row=0)

# Przyciski kopiowania
copy_t1_to_t2_button = ttk.Button(
    frame_t2, text="Kopiuj z T1", width=17, style="secondary.TButton",  # Stała szerokość
    command=lambda: copy_datetime(
        (T1_date, T1_hour, T1_minute, T1_second),
        (T2_date, T2_hour, T2_minute, T2_second)
    )
)
copy_t1_to_t2_button.grid(row=0, column=2, padx=padx, pady=pady, sticky="ew", columnspan=2)  # Wyśrodkowanie w kolumnie


# Sekcja T3
frame_t3 = ttk.Labelframe(root, text="T3 (Data graniczna posiadania tokenów)")
frame_t3.grid(row=4, column=0, padx=padx, pady=pady, sticky="ew")
frame_t3.grid_columnconfigure(0, weight=0)  # Kolumna 0 bez wagi
frame_t3.grid_columnconfigure(1, weight=0)  # Kolumna 1 bez wagi
frame_t3.grid_columnconfigure(2, weight=0)  # Kolumna 2 bez wagi
frame_t3.grid_columnconfigure(3, weight=0)  # Kolumna 3 bez wagi
frame_t3.grid_columnconfigure(4, weight=0)  # Kolumna 4 bez wagi

T3_date, T3_hour, T3_minute, T3_second = create_datetime_section(frame_t3, "Wybierz T3:", row=0)

# Przyciski kopiowania
copy_t2_to_t3_button = ttk.Button(
    frame_t3, text="Kopiuj z T2", width=17, style="secondary.TButton",  # Stała szerokość
    command=lambda: copy_datetime(
        (T2_date, T2_hour, T2_minute, T2_second),
        (T3_date, T3_hour, T3_minute, T3_second)
    )
)
copy_t2_to_t3_button.grid(row=0, column=2, padx=padx, pady=pady, sticky="ew", columnspan=2)  # Wyśrodkowanie w kolumnie


# Sekcja Wybór sieci
frame_network = ttk.Frame(root)
frame_network.grid(row=5, column=0, padx=padx, pady=pady, sticky="ew")

# Etykieta i Combobox w jednej kolumnie
ttk.Label(frame_network, text="Wybierz sieć:").grid(row=0, column=0, padx=padx, pady=pady, sticky="w")
network_var = ttk.StringVar()
network_combo = ttk.Combobox(
    frame_network, textvariable=network_var,
    values=["ETH", "BASE", "BNB"], state="readonly", width=13
)
network_combo.grid(row=0, column=1, padx=padx, pady=pady, sticky="w")
network_combo.current(0)

# Ustawienie elastyczności kolumn
frame_network.grid_columnconfigure(0, weight=0)  # Etykieta nie rośnie
frame_network.grid_columnconfigure(1, weight=1)  # Combobox rośnie

# Kolumna z przyciskiem "Uruchom"
run_button = ttk.Button(
    frame_network, text="Uruchom", width=39, style="danger.TButton", 
    command=lambda: save_and_run(log_widget)
)

# Przycisk "Uruchom" w osobnej kolumnie, przypięty do prawej strony
run_button.grid(row=0, column=2, padx=padx, pady=pady, sticky="e")

# Konfiguracja kolumn: 0 i 1 dla etykiety i comboboxa oraz 2 dla przycisku
frame_network.grid_columnconfigure(2, weight=0)  # Kolumna z przyciskiem ma stałą szerokość

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
                    pass
        token_contract_entry.insert(0, saved_config.get("TOKEN_CONTRACT_ADDRESS", ""))
except FileNotFoundError:
    pass

# Uruchomienie aplikacji
root.mainloop()
