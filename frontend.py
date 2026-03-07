import customtkinter as ctk
import threading
import tkinter as tk
from backend import LegalEngine  

# ── Appearance ─────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ── Design Tokens ──────────────────────────────────────────────────────────────
PALETTE = {
    "bg":           "#0D0F14",      
    "surface":      "#13161E",      
    "surface_2":    "#1B1F2B",      
    "border":       "#252A38",      
    "accent":       "#C9A84C",      
    "accent_dim":   "#8A6E2F",      
    "text_primary": "#E8E6DF",      
    "text_secondary":"#7A8099",     
    "text_dim":     "#3D4357",      
    "positive":     "#3DAA72",      
    "warning":      "#C9A84C",      
}

# ── Components ─────────────────────────────────────────────────────────────────

class SidebarButton(ctk.CTkButton):
    def __init__(self, master, text, command, **kwargs):
        super().__init__(
            master, 
            text=text, 
            command=command,
            corner_radius=8,
            height=45,
            fg_color="transparent",
            text_color=PALETTE["text_secondary"],
            hover_color=PALETTE["surface_2"],
            anchor="w",
            font=("Inter", 13, "bold"),
            **kwargs
        )

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_select):
        super().__init__(master, fg_color=PALETTE["surface"], width=240, corner_radius=0)
        self.on_select = on_select
        
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(fill="x", padx=20, pady=30)
        
        ctk.CTkLabel(brand_frame, text="EXECUTIVE", font=("Playfair Display", 20, "bold"), text_color=PALETTE["accent"]).pack(anchor="w")
        ctk.CTkLabel(brand_frame, text="INSIGHT", font=("Inter", 12, "bold"), text_color=PALETTE["text_secondary"]).pack(anchor="w")

        self.btn_dash = SidebarButton(self, "Dashboard", lambda: on_select("Dashboard"))
        self.btn_dash.pack(fill="x", padx=10, pady=5)
        
        self.btn_qa = SidebarButton(self, "Legal Q&A", lambda: on_select("Legal Q&A"))
        self.btn_qa.pack(fill="x", padx=10, pady=5)
        
        self.btn_bills = SidebarButton(self, "Bills", lambda: on_select("Bills"))
        self.btn_bills.pack(fill="x", padx=10, pady=5)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=10, pady=20)
        SidebarButton(footer, "Settings", lambda: on_select("Settings")).pack(fill="x")

# ── Panels ────────────────────────────────────────────────────────────────────

class DashboardPanel(ctk.CTkFrame):
    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")
        
        # Title
        ctk.CTkLabel(self, text="Platform Overview", font=("Inter", 24, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w", padx=40, pady=(40, 20))
        
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=40)

        # Quick Stats Widgets
        self.create_stat_card(stats_frame, "DATABASE RECORDS", str(len(engine.all_data_content)), 0)
        self.create_stat_card(stats_frame, "ACTIVE LIBRARIES", str(len(engine.csv_files)), 1)
        self.create_stat_card(stats_frame, "AI STATUS", "CONNECTED", 2)

    def create_stat_card(self, master, title, value, col):
        card = ctk.CTkFrame(master, fg_color=PALETTE["surface"], border_color=PALETTE["border"], border_width=1, height=120)
        card.grid(row=0, column=col, padx=(0, 20), sticky="nsew")
        master.grid_columnconfigure(col, weight=1)
        
        ctk.CTkLabel(card, text=title, font=("Inter", 10, "bold"), text_color=PALETTE["text_secondary"]).pack(pady=(20, 5))
        ctk.CTkLabel(card, text=value, font=("Inter", 20, "bold"), text_color=PALETTE["accent"]).pack(pady=(0, 20))

class LegalQAPanel(ctk.CTkFrame):
    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")
        self.engine = engine

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(40, 20))
        ctk.CTkLabel(header, text="Legal Intelligence", font=("Inter", 24, "bold"), text_color=PALETTE["text_primary"]).pack(side="left")
        
        self.chat_box = ctk.CTkTextbox(self, fg_color=PALETTE["surface"], border_color=PALETTE["border"], border_width=1, text_color=PALETTE["text_primary"], font=("Inter", 14), padx=20, pady=20)
        self.chat_box.pack(fill="both", expand=True, padx=40, pady=10)
        self.chat_box.configure(state="disabled")

        input_container = ctk.CTkFrame(self, fg_color=PALETTE["surface"], border_color=PALETTE["border"], border_width=1)
        input_container.pack(fill="x", padx=40, pady=(10, 40))
        
        self.input_field = ctk.CTkEntry(input_container, placeholder_text="Query the executive record...", fg_color="transparent", border_width=0, text_color=PALETTE["text_primary"], font=("Inter", 14))
        self.input_field.pack(side="left", fill="both", expand=True, padx=20)
        self.input_field.bind("<Return>", lambda e: self.handle_submission())
        
        self.submit_btn = ctk.CTkButton(input_container, text="SUBMIT INQUIRY", fg_color=PALETTE["accent"], hover_color=PALETTE["accent_dim"], text_color=PALETTE["bg"], font=("Inter", 12, "bold"), width=140, command=self.handle_submission)
        self.submit_btn.pack(side="right", padx=10, pady=10)

    def handle_submission(self):
        query = self.input_field.get().strip()
        if not query: return
        self.input_field.delete(0, 'end')
        self._append_to_chat(f"YOU: {query}\n")
        self.submit_btn.configure(state="disabled", text="ANALYZING...")
        threading.Thread(target=self.run_ai, args=(query,), daemon=True).start()

    def run_ai(self, query):
        try:
            response = self.engine.query_ai(query)
            self.after(0, self._append_to_chat, f"EXECUTIVE INSIGHT: {response}\n\n")
        except Exception as e:
            self.after(0, self._append_to_chat, f"SYSTEM ERROR: {str(e)}\n\n")
        finally:
            self.after(0, lambda: self.submit_btn.configure(state="normal", text="SUBMIT INQUIRY"))

    def _append_to_chat(self, message):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", message)
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

class BillsPanel(ctk.CTkFrame):
    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")
        self.engine = engine
        
        ctk.CTkLabel(self, text="Legislative Tracking", font=("Inter", 24, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w", padx=40, pady=(40, 20))
        
        search_frame = ctk.CTkFrame(self, fg_color=PALETTE["surface"], border_color=PALETTE["border"], border_width=1)
        search_frame.pack(fill="x", padx=40, pady=10)
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Filter database by keywords (e.g. 'Sanctions', 'Space')...", fg_color="transparent", border_width=0)
        self.search_entry.pack(side="left", fill="both", expand=True, padx=20)
        
        ctk.CTkButton(search_frame, text="SEARCH RECORDS", fg_color=PALETTE["accent"], text_color=PALETTE["bg"], width=150, command=self.do_search).pack(side="right", padx=10, pady=10)

        self.results_box = ctk.CTkTextbox(self, fg_color=PALETTE["surface"], border_color=PALETTE["border"], border_width=1, text_color=PALETTE["text_secondary"])
        self.results_box.pack(fill="both", expand=True, padx=40, pady=(10, 40))

    def do_search(self):
        query = self.search_entry.get()
        results = self.engine.search_records(query, limit=20)
        self.results_box.delete("1.0", "end")
        if not results:
            self.results_box.insert("end", "No matching records found.")
        for r in results:
            self.results_box.insert("end", f"• {r}\n\n")

class SettingsPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        ctk.CTkLabel(self, text="Preferences", font=("Inter", 24, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w", padx=40, pady=(40, 20))
        
        container = ctk.CTkFrame(self, fg_color=PALETTE["surface"], border_color=PALETTE["border"], border_width=1)
        container.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        
        # Appearance Toggle
        ctk.CTkLabel(container, text="Appearance Mode", font=("Inter", 14, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w", padx=30, pady=(30, 10))
        self.mode_switch = ctk.CTkOptionMenu(container, values=["Dark", "Light"], fg_color=PALETTE["surface_2"], button_color=PALETTE["accent"], button_hover_color=PALETTE["accent_dim"], command=lambda m: ctk.set_appearance_mode(m))
        self.mode_switch.pack(anchor="w", padx=30)
        
        # Connection Status
        ctk.CTkLabel(container, text="AI Core Engine", font=("Inter", 14, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w", padx=30, pady=(30, 10))
        ctk.CTkLabel(container, text="Connected via OpenAI API (gpt-3.5-turbo-instruct)", text_color=PALETTE["positive"]).pack(anchor="w", padx=30)

# ── Main Application ──────────────────────────────────────────────────────────

class ExecutiveInsight(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Executive Insight")
        self.geometry("1280x800")
        self.configure(fg_color=PALETTE["bg"])

        self.engine = LegalEngine()

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        self.sidebar = Sidebar(body, on_select=self._show_panel)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkFrame(body, width=1, fg_color=PALETTE["border"], corner_radius=0).pack(side="left", fill="y")

        self.content_area = ctk.CTkFrame(body, fg_color=PALETTE["bg"], corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)

        self.panels = {
            "Dashboard": DashboardPanel(self.content_area, self.engine),
            "Legal Q&A": LegalQAPanel(self.content_area, self.engine),
            "Bills":      BillsPanel(self.content_area, self.engine),
            "Settings":   SettingsPanel(self.content_area),
        }

        self._show_panel("Dashboard")

    def _show_panel(self, name):
        for panel in self.panels.values():
            panel.pack_forget()
        if name in self.panels:
            self.panels[name].pack(fill="both", expand=True)

if __name__ == "__main__":
    app = ExecutiveInsight()
    app.mainloop()
