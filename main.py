#!/usr/bin/env python3
"""
Główny punkt wejścia aplikacji Find Crypto Wallets.
Uruchamia interfejs graficzny aplikacji.
"""

import sys
import os

# Dodaj katalogi do ścieżki Python
sys.path.append(os.path.join(os.path.dirname(__file__), 'frontend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

# Import głównej aplikacji
from frontend.app import WalletApp

def main():
    """Uruchamia aplikację"""
    app = WalletApp()
    app.run()

if __name__ == "__main__":
    main()
