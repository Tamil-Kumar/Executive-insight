import customtkinter as ctk
import threading
import tkinter as tk
from backend import LegalEngine  

# ── Appearance ─────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ── Design Tokens ──────────────────────────────────────────────────────────────
PALETTE = {
    "bg":            "#0D0F14",
    "surface":       "#13161E",
    "surface_2":     "#1B1F2B",
    "border":        "#252A38",
    "accent":        "#C9A84C",
    "accent_dim":    "#8A6E2F",
    "text_primary":  "#E8E6DF",
    "text_secondary":"#7A8099",
    "text_dim":      "#3D4357",
    "positive":      "#3DAA72",
    "warning":       "#C9A84C",
    "dem_blue":      "#1A4F8A",
    "dem_light":     "#4A90D9",
    "rep_red":       "#8A1A1A",
    "rep_light":     "#D94A4A",
    "ind_purple":    "#5A3A8A",
    "ind_light":     "#9B72D4",
}

# ── Party Data ────────────────────────────────────────────────────────────────

PARTY_DATA = {
    "Democrat": {
        "color":     PALETTE["dem_light"],
        "dim_color": PALETTE["dem_blue"],
        "symbol":    "🫏",
        "tagline":   "Progress, Equity & Opportunity",
        "description": (
            "The Democratic Party, founded in 1828, is one of the two major "
            "contemporary political parties in the United States. It broadly "
            "advocates for social justice, regulated markets, and an active "
            "federal government role in addressing inequality."
        ),
        "core_goals": [
            ("Healthcare",        "Universal or expanded access; protect and strengthen the ACA."),
            ("Climate",           "Aggressive transition to clean energy; rejoin Paris Agreement."),
            ("Economy",           "Higher minimum wage, tax increases on corporations and wealthy."),
            ("Education",         "Expand public education funding, reduce student debt burden."),
            ("Civil Rights",      "Protect voting rights, LGBTQ+ equality, racial equity policies."),
            ("Immigration",       "Path to citizenship for undocumented residents; DACA protection."),
            ("Gun Policy",        "Universal background checks, assault weapons restrictions."),
            ("Social Safety Net", "Expand Medicaid, Social Security, and housing assistance."),
        ],
        "recent_impacts": [
            ("Inflation Reduction Act (2022)",  "~$369B in climate & energy investment; extended ACA subsidies."),
            ("American Rescue Plan (2021)",     "$1.9T COVID relief; child tax credit cut child poverty by ~30%."),
            ("Infrastructure Law (2021)",       "$1.2T for roads, bridges, broadband, and clean water."),
            ("Student Debt Relief",             "Ongoing efforts to cancel and restructure federal student loans."),
            ("CHIPS & Science Act (2022)",      "~$53B to revive domestic semiconductor manufacturing."),
        ],
    },
    "Republican": {
        "color":     PALETTE["rep_light"],
        "dim_color": PALETTE["rep_red"],
        "symbol":    "🐘",
        "tagline":   "Freedom, Free Markets & Traditional Values",
        "description": (
            "The Republican Party, founded in 1854, is the other major U.S. "
            "political party. It generally advocates for lower taxes, reduced "
            "government regulation, free-market economics, strong national "
            "defence, and traditional social values."
        ),
        "core_goals": [
            ("Economy",       "Cut taxes, reduce regulation, prioritise business growth."),
            ("Immigration",   "Secure borders; enforce existing law; reduce illegal immigration."),
            ("Gun Rights",    "Protect Second Amendment rights; oppose new firearms restrictions."),
            ("Military",      "Increase defence spending; project strength internationally."),
            ("Energy",        "Expand domestic fossil fuel production; energy independence."),
            ("Healthcare",    "Repeal ACA mandates; promote market-based health solutions."),
            ("Education",     "School choice, charter schools, parental curriculum rights."),
            ("Judicial",      "Appoint originalist judges; limit federal judicial overreach."),
        ],
        "recent_impacts": [
            ("Tax Cuts & Jobs Act (2017)",   "Cut corporate tax rate from 35% to 21%; individual rate reductions."),
            ("Three Supreme Court Seats",    "Confirmed Gorsuch, Kavanaugh, and Barrett — shifting court balance."),
            ("Dobbs v. Jackson (2022)",      "Overturned Roe v. Wade, returning abortion regulation to states."),
            ("Abraham Accords (2020)",       "Brokered Israel–UAE, Israel–Bahrain, and other normalisation deals."),
            ("Operation Warp Speed (2020)",  "Accelerated COVID-19 vaccine development in under 12 months."),
        ],
    },
    "Independent / Third Party": {
        "color":     PALETTE["ind_light"],
        "dim_color": PALETTE["ind_purple"],
        "symbol":    "⚖",
        "tagline":   "Beyond the Two-Party System",
        "description": (
            "Third parties and independents occupy a wide ideological spectrum "
            "outside the two-party duopoly. Notable parties include the Libertarian "
            "Party, Green Party, and Constitution Party, each offering distinct "
            "policy visions often ignored by the major parties."
        ),
        "core_goals": [
            ("Libertarian: Liberty",   "Maximise individual freedom; drastically shrink federal government."),
            ("Libertarian: Economy",   "Free markets, end the Federal Reserve, legalise victimless crimes."),
            ("Green: Environment",     "Green New Deal, 100% renewables, end fossil fuel subsidies."),
            ("Green: Justice",         "Social and economic justice; universal healthcare; demilitarise police."),
            ("Constitution: Founding", "Strict constitutional originalism; return power to states."),
            ("Constitution: Fiscal",   "End deficit spending, return to commodity-backed currency."),
            ("Reform: Electoral",      "Ranked-choice voting, campaign finance reform, term limits."),
            ("Common Goal",            "Break the duopoly; give voters more meaningful choices."),
        ],
        "recent_impacts": [
            ("2024 Spoiler Effect",      "Independent candidates influenced outcomes in several Senate races."),
            ("Ranked-Choice Adoption",   "Alaska and Maine now use RCV for federal elections."),
            ("Libertarian Ballot Access","Libertarians achieved ballot access in all 50 states in 2024 cycle."),
            ("Green Policy Influence",   "Green New Deal language adopted into mainstream Democratic platform."),
            ("Ross Perot Legacy",        "1992 independent run (19% popular vote) reshaped debate on deficits."),
        ],
    },
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
            font=("Georgia", 13, "bold"),
            **kwargs
        )


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_select):
        super().__init__(master, fg_color=PALETTE["surface"], width=240, corner_radius=0)
        self.on_select = on_select

        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(fill="x", padx=20, pady=30)

        ctk.CTkLabel(brand_frame, text="EXECUTIVE", font=("Georgia", 20, "bold"),
                     text_color=PALETTE["accent"]).pack(anchor="w")
        ctk.CTkLabel(brand_frame, text="INSIGHT", font=("Courier New", 12, "bold"),
                     text_color=PALETTE["text_secondary"]).pack(anchor="w")

        ctk.CTkFrame(self, height=1, fg_color=PALETTE["border"]).pack(fill="x", padx=16, pady=(0, 10))

        self.btn_dash  = SidebarButton(self, "  Dashboard",    lambda: on_select("Dashboard"))
        self.btn_dash.pack(fill="x", padx=10, pady=3)

        self.btn_qa    = SidebarButton(self, "  Legal Q&A",    lambda: on_select("Legal Q&A"))
        self.btn_qa.pack(fill="x", padx=10, pady=3)

        self.btn_bills = SidebarButton(self, "  Bills",         lambda: on_select("Bills"))
        self.btn_bills.pack(fill="x", padx=10, pady=3)

        self.btn_party = SidebarButton(self, "  Party Impact",  lambda: on_select("Party Impact"))
        self.btn_party.pack(fill="x", padx=10, pady=3)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=10, pady=20)
        ctk.CTkFrame(footer, height=1, fg_color=PALETTE["border"]).pack(fill="x", pady=(0, 10))
        SidebarButton(footer, "  Settings", lambda: on_select("Settings")).pack(fill="x")


# ── Panels ────────────────────────────────────────────────────────────────────

class DashboardPanel(ctk.CTkFrame):
    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")

        ctk.CTkLabel(self, text="Platform Overview", font=("Georgia", 24, "bold"),
                     text_color=PALETTE["text_primary"]).pack(anchor="w", padx=40, pady=(40, 20))

        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=40)

        self.create_stat_card(stats_frame, "DATABASE RECORDS", str(len(engine.all_data_content)), 0)
        self.create_stat_card(stats_frame, "ACTIVE LIBRARIES", str(len(engine.csv_files)),        1)
        self.create_stat_card(stats_frame, "AI STATUS",        "CONNECTED",                       2)

    def create_stat_card(self, master, title, value, col):
        card = ctk.CTkFrame(master, fg_color=PALETTE["surface"],
                            border_color=PALETTE["border"], border_width=1, height=120)
        card.grid(row=0, column=col, padx=(0, 20), sticky="nsew")
        master.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(card, text=title, font=("Courier New", 10, "bold"),
                     text_color=PALETTE["text_secondary"]).pack(pady=(20, 5))
        ctk.CTkLabel(card, text=value, font=("Georgia", 20, "bold"),
                     text_color=PALETTE["accent"]).pack(pady=(0, 20))


class LegalQAPanel(ctk.CTkFrame):
    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")
        self.engine = engine

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(40, 20))
        ctk.CTkLabel(header, text="Legal Intelligence", font=("Georgia", 24, "bold"),
                     text_color=PALETTE["text_primary"]).pack(side="left")

        self.chat_box = ctk.CTkTextbox(
            self, fg_color=PALETTE["surface"], border_color=PALETTE["border"],
            border_width=1, text_color=PALETTE["text_primary"],
            font=("Courier New", 13), padx=20, pady=20
        )
        self.chat_box.pack(fill="both", expand=True, padx=40, pady=10)
        self.chat_box.configure(state="disabled")

        input_container = ctk.CTkFrame(self, fg_color=PALETTE["surface"],
                                        border_color=PALETTE["border"], border_width=1)
        input_container.pack(fill="x", padx=40, pady=(10, 40))

        self.input_field = ctk.CTkEntry(
            input_container, placeholder_text="Query the executive record...",
            fg_color="transparent", border_width=0,
            text_color=PALETTE["text_primary"], font=("Georgia", 14)
        )
        self.input_field.pack(side="left", fill="both", expand=True, padx=20)
        self.input_field.bind("<Return>", lambda e: self.handle_submission())

        self.submit_btn = ctk.CTkButton(
            input_container, text="SUBMIT INQUIRY",
            fg_color=PALETTE["accent"], hover_color=PALETTE["accent_dim"],
            text_color=PALETTE["bg"], font=("Courier New", 12, "bold"),
            width=140, command=self.handle_submission
        )
        self.submit_btn.pack(side="right", padx=10, pady=10)

    def handle_submission(self):
        query = self.input_field.get().strip()
        if not query:
            return
        self.input_field.delete(0, "end")
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

        ctk.CTkLabel(self, text="Legislative Tracking", font=("Georgia", 24, "bold"),
                     text_color=PALETTE["text_primary"]).pack(anchor="w", padx=40, pady=(40, 20))

        search_frame = ctk.CTkFrame(self, fg_color=PALETTE["surface"],
                                     border_color=PALETTE["border"], border_width=1)
        search_frame.pack(fill="x", padx=40, pady=10)

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Filter database by keywords (e.g. 'Sanctions', 'Space')...",
            fg_color="transparent", border_width=0, font=("Georgia", 13)
        )
        self.search_entry.pack(side="left", fill="both", expand=True, padx=20)

        ctk.CTkButton(
            search_frame, text="SEARCH RECORDS",
            fg_color=PALETTE["accent"], text_color=PALETTE["bg"],
            font=("Courier New", 11, "bold"), width=150, command=self.do_search
        ).pack(side="right", padx=10, pady=10)

        self.results_box = ctk.CTkTextbox(
            self, fg_color=PALETTE["surface"], border_color=PALETTE["border"],
            border_width=1, text_color=PALETTE["text_secondary"], font=("Courier New", 12)
        )
        self.results_box.pack(fill="both", expand=True, padx=40, pady=(10, 40))

    def do_search(self):
        query = self.search_entry.get()
        results = self.engine.search_records(query, limit=20)
        self.results_box.delete("1.0", "end")
        if not results:
            self.results_box.insert("end", "No matching records found.")
        for r in results:
            self.results_box.insert("end", f"• {r}\n\n")


# ══════════════════════════════════════════════════════════════════════════════
#  PARTY IMPACT PANEL
# ══════════════════════════════════════════════════════════════════════════════

class PartyCard(ctk.CTkFrame):
    """Expandable card showing goals and impact for a single political party."""

    def __init__(self, master, party_name, data, **kwargs):
        super().__init__(
            master,
            fg_color=PALETTE["surface"],
            border_color=data["dim_color"],
            border_width=1,
            corner_radius=10,
            **kwargs
        )
        self.data       = data
        self.party_name = party_name
        self._expanded  = False
        self._build_header()
        self._build_body()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        hdr.pack(fill="x", padx=20, pady=16)

        # Coloured left stripe
        stripe = ctk.CTkFrame(self, width=4, fg_color=self.data["color"], corner_radius=0)
        stripe.place(x=0, y=0, relheight=1)

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        top_row = ctk.CTkFrame(left, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(
            top_row, text=self.party_name,
            font=("Georgia", 17, "bold"),
            text_color=self.data["color"], anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            top_row, text=f"  {self.data['symbol']}",
            font=("Georgia", 18),
            text_color=self.data["color"]
        ).pack(side="left")

        ctk.CTkLabel(
            left, text=self.data["tagline"],
            font=("Courier New", 10),
            text_color=PALETTE["text_secondary"], anchor="w"
        ).pack(fill="x")

        self.toggle_btn = ctk.CTkButton(
            hdr, text="▼  Expand", width=110, height=28,
            corner_radius=6,
            fg_color=PALETTE["surface_2"],
            hover_color=PALETTE["border"],
            text_color=PALETTE["text_secondary"],
            font=("Courier New", 10, "bold"),
            command=self._toggle
        )
        self.toggle_btn.pack(side="right")

        for w in (hdr, left, top_row):
            w.bind("<Button-1>", lambda e: self._toggle())

    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        # hidden until expanded

        # Description
        ctk.CTkLabel(
            self.body,
            text=self.data["description"],
            font=("Georgia", 12),
            text_color=PALETTE["text_secondary"],
            wraplength=820, justify="left", anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 16))

        # Two-column: Goals | Impact
        cols = ctk.CTkFrame(self.body, fg_color="transparent")
        cols.pack(fill="x", padx=24, pady=(0, 20))
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)

        self._build_column(
            cols, 0, "CORE GOALS", self.data["core_goals"]
        )
        self._build_column(
            cols, 1, "RECENT LEGISLATIVE IMPACT", self.data["recent_impacts"]
        )

    def _build_column(self, parent, col, heading, items):
        frame = ctk.CTkFrame(
            parent, fg_color=PALETTE["surface_2"],
            corner_radius=8, border_width=1, border_color=PALETTE["border"]
        )
        frame.grid(
            row=0, column=col, sticky="nsew",
            padx=(0, 10) if col == 0 else (10, 0)
        )

        ctk.CTkLabel(
            frame, text=heading,
            font=("Courier New", 9, "bold"),
            text_color=self.data["color"]
        ).pack(anchor="w", padx=16, pady=(14, 8))

        for label, detail in items:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)

            dot = ctk.CTkFrame(row, width=6, height=6, corner_radius=3,
                               fg_color=self.data["color"])
            dot.pack(side="left", padx=(0, 10))
            dot.pack_propagate(False)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                inner, text=label,
                font=("Georgia", 12, "bold"),
                text_color=PALETTE["text_primary"], anchor="w"
            ).pack(fill="x")

            ctk.CTkLabel(
                inner, text=detail,
                font=("Courier New", 10),
                text_color=PALETTE["text_secondary"],
                wraplength=330, justify="left", anchor="w"
            ).pack(fill="x")

        ctk.CTkFrame(frame, height=12, fg_color="transparent").pack()

    def _toggle(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.body.pack(fill="x", pady=(0, 12))
            self.toggle_btn.configure(text="▲  Collapse")
        else:
            self.body.pack_forget()
            self.toggle_btn.configure(text="▼  Expand")


class PartyImpactPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(40, 4))

        ctk.CTkLabel(
            hdr, text="Party Impact & Goals",
            font=("Georgia", 24, "bold"),
            text_color=PALETTE["text_primary"], anchor="w"
        ).pack(side="left")

        badge = ctk.CTkFrame(hdr, fg_color=PALETTE["surface_2"],
                              corner_radius=4, border_width=1,
                              border_color=PALETTE["border"])
        badge.pack(side="right", pady=6)
        ctk.CTkLabel(
            badge, text="NON-PARTISAN  •  INFORMATIONAL",
            font=("Courier New", 9, "bold"),
            text_color=PALETTE["text_dim"]
        ).pack(padx=10, pady=4)

        ctk.CTkLabel(
            self,
            text="An objective overview of U.S. political parties — their goals, values, and recent legislative impact.",
            font=("Courier New", 11),
            text_color=PALETTE["text_secondary"], anchor="w"
        ).pack(fill="x", padx=40, pady=(0, 16))

        # Disclaimer banner
        disc = ctk.CTkFrame(self, fg_color=PALETTE["surface_2"],
                             corner_radius=8, border_width=1,
                             border_color=PALETTE["border"])
        disc.pack(fill="x", padx=40, pady=(0, 20))
        ctk.CTkLabel(
            disc,
            text=(
                "⚠   This panel presents factual policy positions and legislative records. "
                "It does not endorse any party or candidate."
            ),
            font=("Courier New", 10),
            text_color=PALETTE["text_dim"], anchor="w"
        ).pack(fill="x", padx=16, pady=10)

        # Scrollable party cards
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=PALETTE["border"],
            scrollbar_fg_color=PALETTE["surface"],
        )
        scroll.pack(fill="both", expand=True, padx=40, pady=(0, 32))

        for party_name, data in PARTY_DATA.items():
            PartyCard(scroll, party_name, data).pack(fill="x", pady=(0, 16))


class SettingsPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        ctk.CTkLabel(self, text="Preferences", font=("Georgia", 24, "bold"),
                     text_color=PALETTE["text_primary"]).pack(anchor="w", padx=40, pady=(40, 20))

        container = ctk.CTkFrame(self, fg_color=PALETTE["surface"],
                                  border_color=PALETTE["border"], border_width=1)
        container.pack(fill="both", expand=True, padx=40, pady=(0, 40))

        ctk.CTkLabel(container, text="Appearance Mode",
                     font=("Georgia", 14, "bold"),
                     text_color=PALETTE["text_primary"]).pack(anchor="w", padx=30, pady=(30, 10))
        self.mode_switch = ctk.CTkOptionMenu(
            container, values=["Dark", "Light"],
            fg_color=PALETTE["surface_2"],
            button_color=PALETTE["accent"],
            button_hover_color=PALETTE["accent_dim"],
            command=lambda m: ctk.set_appearance_mode(m)
        )
        self.mode_switch.pack(anchor="w", padx=30)

        ctk.CTkLabel(container, text="AI Core Engine",
                     font=("Georgia", 14, "bold"),
                     text_color=PALETTE["text_primary"]).pack(anchor="w", padx=30, pady=(30, 10))
        ctk.CTkLabel(
            container,
            text="Connected via OpenAI API (gpt-3.5-turbo-instruct)",
            text_color=PALETTE["positive"],
            font=("Courier New", 12)
        ).pack(anchor="w", padx=30)


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

        ctk.CTkFrame(body, width=1, fg_color=PALETTE["border"],
                     corner_radius=0).pack(side="left", fill="y")

        self.content_area = ctk.CTkFrame(body, fg_color=PALETTE["bg"], corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)

        self.panels = {
            "Dashboard":    DashboardPanel(self.content_area, self.engine),
            "Legal Q&A":    LegalQAPanel(self.content_area, self.engine),
            "Bills":        BillsPanel(self.content_area, self.engine),
            "Party Impact": PartyImpactPanel(self.content_area),
            "Settings":     SettingsPanel(self.content_area),
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
