#!/usr/bin/env python3
"""
Nowy plik startowy wykorzystujący zrefaktoryzowane klasy.
"""
from main_window import MainWindow
from main_refactored import main


if __name__ == "__main__":
    # Tworzenie i uruchamianie głównego okna aplikacji
    app = MainWindow(main_function=main)
    app.run()