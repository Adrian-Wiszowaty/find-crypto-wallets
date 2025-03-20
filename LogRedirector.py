import sys
import tkinter as tk

class LogRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        def append():
            if message.strip():
                self.text_widget.insert(tk.END, message.strip() + '\n')
                self.text_widget.yview(tk.END)
        self.text_widget.after(0, append)

    def flush(self):
        pass

