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

        # UI Setup
        self.title("Executive Insight | Professional Legal AI")
        self.geometry("700x850")
        
        self.colors = {
            "base": "#24273a", "surface": "#363a4f", "crust": "#181926",
            "blue": "#8aadf4", "yellow": "#eed49f", "text": "#cad3f5",
            "subtext": "#b8c0e0", "mantle": "#1e2030"
        }

        self.serif_font = ("Georgia", 18)
        self.serif_bold = ("Georgia", 18, "bold")
        self.header_font = ("Georgia", 22, "bold")

        ctk.set_appearance_mode("dark")
        self.setup_ui()

    def setup_ui(self):
        self.configure(fg_color=self.colors["base"])

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color=self.colors["mantle"], corner_radius=0, height=120)
        self.header_frame.pack(side="top", fill="x")
        
        ctk.CTkLabel(self.header_frame, text="EXECUTIVE INSIGHT", font=self.header_font, text_color=self.colors["yellow"]).pack(pady=(20, 0))
        ctk.CTkLabel(self.header_frame, text="AI-Powered Preliminary Legal Research", font=("Helvetica", 11), text_color="white").pack(pady=(0, 20))

        # Tabs
        self.tabview = ctk.CTkTabview(self, corner_radius=15, fg_color=self.colors["surface"])
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tab_chat = self.tabview.add(" Legal Consult ")
        self.tab_orders = self.tabview.add(" Executive Orders ")
        
        self.setup_chat_tab()
        self.setup_orders_tab()

    def setup_chat_tab(self):
        self.chat_display = scrolledtext.ScrolledText(self.tab_chat, font=self.serif_font, bg=self.colors["surface"], fg=self.colors["text"])
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)
        self.chat_display.tag_config("user", foreground=self.colors["yellow"], font=self.serif_bold)
        self.chat_display.config(state='disabled')

        self.text_area = ctk.CTkTextbox(self.tab_chat, height=80, fg_color=self.colors["crust"])
        self.text_area.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(self.tab_chat, text="SUBMIT INQUIRY", command=self.send_message, fg_color=self.colors["blue"]).pack(anchor="e", padx=15, pady=(0, 15))

    def setup_orders_tab(self):
        search_frame = ctk.CTkFrame(self.tab_orders, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=10)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search orders...", expand=True)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(search_frame, text="SEARCH", command=self.filter_orders).pack(side="right")

        self.orders_display = scrolledtext.ScrolledText(self.tab_orders, font=("Arial", 15), bg=self.colors["crust"], fg=self.colors["subtext"])
        self.orders_display.pack(fill="both", expand=True, padx=10, pady=10)

    def send_message(self):
        user_input = self.text_area.get("1.0", tk.END).strip()
        if user_input:
            self.update_chat(f"CLIENT: {user_input}\n", "user")
            self.text_area.delete("1.0", tk.END)
            threading.Thread(target=self.run_ai, args=(user_input,), daemon=True).start()

    def run_ai(self, query):
        try:
            response = self.engine.query_ai(query)
            self.after(0, self.update_chat, f"EXECUTIVE INSIGHT: {response}\n\n", "bot")
        except Exception as e:
            self.after(0, self.update_chat, f"SYSTEM ERROR: {e}\n\n", "bot")

    def update_chat(self, message, tag):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, message, tag)
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)

    def filter_orders(self):
        query = self.search_entry.get()
        results = self.engine.search_records(query)
        self.orders_display.config(state='normal')
        self.orders_display.delete("1.0", tk.END)
        for i, res in enumerate(results):
            self.orders_display.insert(tk.END, f"MATCH #{i+1}\n{res}\n{'-'*40}\n")
        self.orders_display.config(state='disabled')

if __name__ == "__main__":
    app = LegalApp()
    app.mainloop()
