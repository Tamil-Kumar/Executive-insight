import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext
import threading
from backend import LegalEngine

class LegalApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialize the Backend Engine
        self.engine = LegalEngine()

        self.title("Executive Insight | Professional Legal AI")
        self.geometry("700x850")
        
        # UI Styling
        self.colors = {
            "base": "#24273a",
            "surface": "#363a4f",
            "crust": "#181926",
            "blue": "#8aadf4",
            "yellow": "#eed49f",
            "text": "#cad3f5",
            "subtext": "#b8c0e0",
            "mantle": "#1e2030"
        }

        self.serif_font = ("Georgia", 18)
        self.serif_bold = ("Georgia", 18, "bold")
        self.header_font = ("Georgia", 22, "bold")

        ctk.set_appearance_mode("dark")
        self.setup_ui()

    def setup_ui(self):
        self.configure(fg_color=self.colors["base"])

        # --- Header Section ---
        self.header_frame = ctk.CTkFrame(self, fg_color=self.colors["mantle"], corner_radius=0, height=120)
        self.header_frame.pack(side="top", fill="x")
        
        self.header_title = ctk.CTkLabel(self.header_frame, text="EXECUTIVE INSIGHT", font=self.header_font, text_color=self.colors["yellow"])
        self.header_title.pack(pady=(20, 0))
        self.header_subtitle = ctk.CTkLabel(self.header_frame, text="AI-Powered Preliminary Legal Research", font=("Helvetica", 11), text_color="white")
        self.header_subtitle.pack(pady=(0, 20))

        # --- Tabview ---
        self.tabview = ctk.CTkTabview(
            self, 
            corner_radius=15, 
            fg_color=self.colors["surface"], 
            segmented_button_selected_color=self.colors["blue"],
            segmented_button_unselected_hover_color=self.colors["blue"]
        )
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tab_chat = self.tabview.add(" Legal Consult ")
        self.tab_orders = self.tabview.add(" Executive Orders ")
        self.tab_settings = self.tabview.add(" Settings ")

        self.setup_chat_tab()
        self.setup_orders_tab()
        self.setup_settings_tab()

    def setup_chat_tab(self):
        chat_container = ctk.CTkFrame(self.tab_chat, fg_color="transparent")
        chat_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.chat_display = scrolledtext.ScrolledText(
            chat_container, font=self.serif_font, relief="flat", highlightthickness=0, 
            bg=self.colors["surface"], fg=self.colors["text"], insertbackground="white"
        )
        self.chat_display.pack(fill="both", expand=True, padx=5, pady=5)
        self.chat_display.tag_config("user", foreground=self.colors["yellow"], font=self.serif_bold)
        self.chat_display.tag_config("bot", foreground=self.colors["subtext"])
        self.chat_display.config(state='disabled')

        self.text_area = ctk.CTkTextbox(
            self.tab_chat, height=80, corner_radius=10, border_width=1, 
            font=self.serif_font, fg_color=self.colors["crust"], 
            text_color=self.colors["text"], border_color=self.colors["blue"]
        )
        self.text_area.pack(fill="x", padx=15, pady=10)

        self.submit_btn = ctk.CTkButton(
            self.tab_chat, text="SUBMIT INQUIRY", command=self.send_message,
            fg_color=self.colors["blue"], hover_color="#7aa2f7", text_color="#1e2030",
            corner_radius=8, font=("Helvetica", 12, "bold"), height=40
        )
        self.submit_btn.pack(anchor="e", padx=15, pady=(0, 15))

    def setup_orders_tab(self):
        orders_container = ctk.CTkFrame(self.tab_orders, fg_color="transparent")
        orders_container.pack(fill="both", expand=True, padx=10, pady=10)

        search_frame = ctk.CTkFrame(orders_container, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))

        # FIXED: Removed 'expand=True' from constructor and moved to .pack()
        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Search orders by keyword or President...", 
            height=35, fg_color=self.colors["crust"], border_color=self.colors["blue"]
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.search_btn = ctk.CTkButton(
            search_frame, text="SEARCH", width=80, command=self.filter_orders,
            fg_color=self.colors["blue"], text_color=self.colors["mantle"]
        )
        self.search_btn.pack(side="right")

        self.orders_display = scrolledtext.ScrolledText(
            orders_container, font=("Arial", 15), relief="flat", highlightthickness=0, 
            bg=self.colors["crust"], fg=self.colors["subtext"]
        )
        self.orders_display.pack(fill="both", expand=True)
        self.orders_display.tag_config("match_header", foreground=self.colors["blue"], font=("Arial", 12, "bold"))
        
        self.filter_orders()

    def setup_settings_tab(self):
        self.settings_title = ctk.CTkLabel(self.tab_settings, text="System Preferences", font=self.serif_bold, text_color=self.colors["yellow"])
        self.settings_title.pack(pady=20)
        
        self.theme_menu = ctk.CTkOptionMenu(
            self.tab_settings, 
            values=["Catppuccin Macchiato", "Executive Blue"],
            command=self.change_theme,
            fg_color=self.colors["blue"],
            button_color=self.colors["blue"],
            text_color="#1e2030"
        )
        self.theme_menu.pack(anchor="w", padx=40, pady=(5, 20))

    def change_theme(self, choice):
        if choice == "Catppuccin Macchiato":
            ctk.set_appearance_mode("dark")
            self.orders_display.configure(bg=self.colors["crust"], fg=self.colors["subtext"])
        else:
            ctk.set_appearance_mode("light")
            self.orders_display.configure(bg="white", fg="black")

    def filter_orders(self):
        query = self.search_entry.get()
        results = self.engine.search_records(query)
        
        self.orders_display.config(state='normal')
        self.orders_display.delete("1.0", tk.END)

        if not results:
            self.orders_display.insert(tk.END, "No matching records found in database.")
        else:
            for i, record in enumerate(results):
                self.orders_display.insert(tk.END, f"DATABASE MATCH #{i + 1}\n", "match_header")
                self.orders_display.insert(tk.END, f"{record}\n" + "-"*40 + "\n")
            
        self.orders_display.config(state='disabled')

    def send_message(self):
        user_input = self.text_area.get("1.0", tk.END).strip()
        if user_input:
            self.update_chat(f"CLIENT: {user_input}\n", "user")
            self.text_area.delete("1.0", tk.END)
            threading.Thread(target=self.get_ai_response, args=(user_input,), daemon=True).start()

    def get_ai_response(self, user_query):
        try:
            response = self.engine.query_ai(user_query)
            self.after(0, self.update_chat, f"EXECUTIVE INSIGHT: {response}\n\n", "bot")
        except Exception as e:
            self.after(0, self.update_chat, f"SYSTEM ERROR: Unable to reach AI. {e}\n\n", "bot")

    def update_chat(self, message, tag):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, message, tag)
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)

if __name__ == "__main__":
    app = LegalApp()
    app.mainloop()
