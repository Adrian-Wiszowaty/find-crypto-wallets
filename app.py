import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'frontend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from frontend.gui_app import WalletApp

def main():
    app = WalletApp()
    app.run()

if __name__ == "__main__":
    main()
