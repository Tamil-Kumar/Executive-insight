import customtkinter as ctk
import threading
import time
from backend import LegalEngine  # Imported your backend engine

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
        
        # Logo / Brand
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(fill="x", padx=20, pady=30)
        
        ctk.CTkLabel(
            brand_frame, text="EXECUTIVE", 
            font=("Playfair Display", 20, "bold"), 
            text_color=PALETTE["accent"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand_frame, text="INSIGHT", 
            font=("Inter", 12, "bold"), 
            text_color=PALETTE["text_secondary"]
        ).pack(anchor="w")

        # Nav
        self.btn_dash = SidebarButton(self, "Dashboard", lambda: on_select("Dashboard"))
        self.btn_dash.pack(fill="x", padx=10, pady=5)
        
        self.btn_qa = SidebarButton(self, "Legal Q&A", lambda: on_select("Legal Q&A"))
        self.btn_qa.pack(fill="x", padx=10, pady=5)
        
        self.btn_bills = SidebarButton(self, "Bills", lambda: on_select("Bills"))
        self.btn_bills.pack(fill="x", padx=10, pady=5)

        # Footer
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=10, pady=20)
        SidebarButton(footer, "Settings", lambda: on_select("Settings")).pack(fill="x")

# ── Panels ────────────────────────────────────────────────────────────────────

class DashboardPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="Market Overview", font=("Inter", 24, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w", padx=40, pady=(40, 20))

class LegalQAPanel(ctk.CTkFrame):
    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")
        self.engine = engine  # Reference to the AI engine

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(40, 20))
        
        ctk.CTkLabel(header, text="Legal Intelligence", font=("Inter", 24, "bold"), text_color=PALETTE["text_primary"]).pack(side="left")
        
        # Chat History
        self.chat_box = ctk.CTkTextbox(
            self, 
            fg_color=PALETTE["surface"], 
            border_color=PALETTE["border"],
            border_width=1,
            text_color=PALETTE["text_primary"],
            font=("Inter", 14),
            padx=20, pady=20
        )
        self.chat_box.pack(fill="both", expand=True, padx=40, pady=10)
        self.chat_box.configure(state="disabled")

        # Input Area
        input_container = ctk.CTkFrame(self, fg_color=PALETTE["surface"], height=100, border_color=PALETTE["border"], border_width=1)
        input_container.pack(fill="x", padx=40, pady=(10, 40))
        
        self.input_field = ctk.CTkEntry(
            input_container, 
            placeholder_text="Enter legal query or case citation...",
            fg_color="transparent",
            border_width=0,
            text_color=PALETTE["text_primary"],
            font=("Inter", 14)
        )
        self.input_field.pack(side="left", fill="both", expand=True, padx=20)
        
        self.submit_btn = ctk.CTkButton(
            input_container, 
            text="SUBMIT INQUIRY",
            fg_color=PALETTE["accent"],
            hover_color=PALETTE["accent_dim"],
            text_color=PALETTE["bg"],
            font=("Inter", 12, "bold"),
            width=140,
            command=self.handle_submission
        )
        self.submit_btn.pack(side="right", padx=10, pady=10)

    def handle_submission(self):
        query = self.input_field.get().strip()
        if not query:
            return
            
        # Clear input and show user message
        self.input_field.delete(0, 'end')
        self._append_to_chat(f"YOU: {query}\n")
        
        # Disable button while thinking
        self.submit_btn.configure(state="disabled", text="ANALYZING...")
        
        # Run AI logic in separate thread
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
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="Legislative Tracking", font=("Inter", 24, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w", padx=40, pady=40)

class SettingsPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="Preferences", font=("Inter", 24, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w", padx=40, pady=40)

# ── Main Application ──────────────────────────────────────────────────────────

class ExecutiveInsight(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Executive Insight")
        self.geometry("1280x800")
        self.configure(fg_color=PALETTE["bg"])

        # Init AI Backend
        self.engine = LegalEngine()

        # Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = Sidebar(body, on_select=self._show_panel)
        self.sidebar.pack(side="left", fill="y")

        # Vertical separator
        ctk.CTkFrame(body, width=1, fg_color=PALETTE["border"], corner_radius=0).pack(side="left", fill="y")

        # Content area
        self.content_area = ctk.CTkFrame(body, fg_color=PALETTE["bg"], corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)

        # Build panels
        self.panels = {
            "Dashboard": DashboardPanel(self.content_area),
            "Legal Q&A": LegalQAPanel(self.content_area, self.engine),
            "Bills":      BillsPanel(self.content_area),
            "Settings":   SettingsPanel(self.content_area),
        }

        self._show_panel("Legal Q&A")

    def _show_panel(self, name):
        for panel in self.panels.values():
            panel.pack_forget()
        if name in self.panels:
            self.panels[name].pack(fill="both", expand=True)

if __name__ == "__main__":
    app = ExecutiveInsight()
    app.mainloop()
