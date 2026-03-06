import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext
import threading
from backend import LegalEngine

class LegalApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialize Backend
        self.engine = LegalEngine()

        self.title("Executive Insight | Legal AI")
        self.geometry("700x850")
        
        self.colors = {
            "base": "#24273a", "surface": "#363a4f", "crust": "#181926",
            "blue": "#8aadf4", "yellow": "#eed49f", "text": "#cad3f5"
        }

        ctk.set_appearance_mode("dark")
        self.setup_ui()

    def setup_ui(self):
        self.configure(fg_color=self.colors["base"])

        # Tabs
        self.tabview = ctk.CTkTabview(self, fg_color=self.colors["surface"])
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        self.tab_chat = self.tabview.add(" Legal Chat ")
        self.tab_search = self.tabview.add(" Database Search ")

        # --- Chat Tab ---
        self.chat_display = scrolledtext.ScrolledText(
            self.tab_chat, font=("Georgia", 14), bg=self.colors["surface"], 
            fg=self.colors["text"], state='disabled'
        )
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)

        self.text_area = ctk.CTkTextbox(self.tab_chat, height=80, fg_color=self.colors["crust"])
        self.text_area.pack(fill="x", padx=10, pady=10)

        self.send_btn = ctk.CTkButton(
            self.tab_chat, text="SEND", command=self.send_message, 
            fg_color=self.colors["blue"], text_color="#1e2030"
        )
        self.send_btn.pack(pady=(0, 10))

        # --- Search Tab ---
        self.search_entry = ctk.CTkEntry(self.tab_search, placeholder_text="Search CSVs...")
        self.search_entry.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(self.tab_search, text="SEARCH", command=self.run_search).pack()

        self.search_display = scrolledtext.ScrolledText(
            self.tab_search, font=("Arial", 12), bg=self.colors["crust"], fg="white"
        )
        self.search_display.pack(fill="both", expand=True, padx=10, pady=10)

    def send_message(self):
        user_input = self.text_area.get("1.0", tk.END).strip()
        if user_input:
            self.update_display(f"CLIENT: {user_input}\n", self.chat_display)
            self.text_area.delete("1.0", tk.END)
            threading.Thread(target=self.run_ai, args=(user_input,), daemon=True).start()

    def run_ai(self, query):
        try:
            response = self.engine.query_ai(query)
            self.after(0, self.update_display, f"AI: {response}\n\n", self.chat_display)
        except Exception as e:
            self.after(0, self.update_display, f"ERROR: {e}\n\n", self.chat_display)

    def run_search(self):
        query = self.search_entry.get()
        results = self.engine.search_records(query)
        self.search_display.delete("1.0", tk.END)
        for r in results:
            self.search_display.insert(tk.END, f"{r}\n{'-'*30}\n")

    def update_display(self, message, widget):
        widget.config(state='normal')
        widget.insert(tk.END, message)
        widget.config(state='disabled')
        widget.yview(tk.END)

if __name__ == "__main__":
    app = LegalApp()
    app.mainloop()
