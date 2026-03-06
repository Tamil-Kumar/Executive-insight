"""
Executive Insight - Legal Intelligence Platform
A premium, polished UI for legal research and legislative tracking.

Dependencies:
    pip install customtkinter
    pip install pillow  (optional, for enhanced visuals)

Note: This file contains only the frontend. 
      A `backend.py` with `ExecutiveInsightBackend` is required to run.
"""

import customtkinter as ctk
import threading
import time

# ── Appearance ─────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ── Design Tokens ──────────────────────────────────────────────────────────────
PALETTE = {
    "bg":           "#0D0F14",      # near-black navy
    "surface":      "#13161E",      # card surface
    "surface_2":    "#1B1F2B",      # slightly lighter panel
    "border":       "#252A38",      # subtle borders
    "accent":       "#C9A84C",      # gold accent
    "accent_dim":   "#8A6E2F",      # muted gold
    "text_primary": "#E8E6DF",      # warm white
    "text_secondary":"#7A8099",     # muted grey-blue
    "text_dim":     "#3D4357",      # very dim
    "positive":     "#3DAA72",      # green
    "warning":      "#C9A84C",      # gold/warning
    "danger":       "#C95C4C",      # red
    "blue_soft":    "#3A6EA8",      # soft blue for secondary actions
}

FONT_DISPLAY  = ("Georgia", )       # serif display — authoritative
FONT_HEADING  = ("Georgia", )
FONT_BODY     = ("Courier New", )   # monospaced body — legal/technical feel
FONT_UI       = ("Helvetica Neue", )

# ── Stub Backend (remove when real backend.py is present) ─────────────────────
try:
    from backend import ExecutiveInsightBackend
except ImportError:
    class ExecutiveInsightBackend:
        current_theme = "Executive Dark"
        def process_legal_question(self, q):
            return (
                f"[STUB RESPONSE]\n\nYour question: \"{q}\"\n\n"
                "Connect your backend.py to receive real legal analysis. "
                "This stub confirms the UI pipeline is functional."
            )
        def get_theme_names(self):
            return ["Executive Dark", "Slate", "Ivory"]
        def get_theme(self, name):
            return {"bg": PALETTE["bg"], "container": PALETTE["surface"], "accent": PALETTE["accent"]}
        def set_theme(self, name):
            self.current_theme = name

# ── Helpers ────────────────────────────────────────────────────────────────────
def make_divider(parent, color=None, height=1, padx=0, pady=(8, 8)):
    color = color or PALETTE["border"]
    line = ctk.CTkFrame(parent, height=height, fg_color=color, corner_radius=0)
    line.pack(fill="x", padx=padx, pady=pady)
    return line


def make_label(parent, text, size=13, weight="normal", color=None, anchor="w", **kwargs):
    color = color or PALETTE["text_primary"]
    return ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(family="Georgia", size=size, weight=weight),
        text_color=color,
        anchor=anchor,
        **kwargs
    )


def make_badge(parent, text, color=None, bg=None):
    bg    = bg    or PALETTE["border"]
    color = color or PALETTE["text_secondary"]
    badge = ctk.CTkFrame(parent, fg_color=bg, corner_radius=4)
    lbl   = ctk.CTkLabel(
        badge, text=text,
        font=ctk.CTkFont(family="Courier New", size=10, weight="bold"),
        text_color=color
    )
    lbl.pack(padx=8, pady=2)
    return badge


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR NAV
# ══════════════════════════════════════════════════════════════════════════════
class Sidebar(ctk.CTkFrame):
    NAV_ITEMS = [
        ("⬛", "Dashboard"),
        ("⚖",  "Legal Q&A"),
        ("📄", "Bills"),
        ("⚙",  "Settings"),
    ]

    def __init__(self, master, on_select, **kwargs):
        super().__init__(
            master,
            width=220,
            corner_radius=0,
            fg_color=PALETTE["surface"],
            **kwargs
        )
        self.on_select   = on_select
        self.nav_buttons = {}
        self._active     = None
        self._build()

    def _build(self):
        self.pack_propagate(False)

        # ── Logo area ──────────────────────────────────────────────────────────
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(28, 20), padx=20)

        ctk.CTkLabel(
            logo_frame,
            text="EXECUTIVE",
            font=ctk.CTkFont(family="Georgia", size=11, weight="bold"),
            text_color=PALETTE["accent"],
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            logo_frame,
            text="INSIGHT",
            font=ctk.CTkFont(family="Georgia", size=22, weight="bold"),
            text_color=PALETTE["text_primary"],
            anchor="w",
        ).pack(fill="x")

        make_divider(self, padx=20, pady=(0, 16))

        # ── Nav label ──────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="NAVIGATION",
            font=ctk.CTkFont(family="Courier New", size=9, weight="bold"),
            text_color=PALETTE["text_dim"],
            anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 8))

        # ── Nav buttons ────────────────────────────────────────────────────────
        for icon, label in self.NAV_ITEMS:
            btn = self._nav_button(icon, label)
            self.nav_buttons[label] = btn

        # ── Status pill at bottom ──────────────────────────────────────────────
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.pack(side="bottom", fill="x", padx=20, pady=24)

        make_divider(status_frame, pady=(0, 12))

        dot = ctk.CTkFrame(status_frame, width=8, height=8,
                           corner_radius=4, fg_color=PALETTE["positive"])
        dot.pack(side="left", padx=(0, 6))
        dot.pack_propagate(False)

        ctk.CTkLabel(
            status_frame,
            text="System Online",
            font=ctk.CTkFont(family="Courier New", size=10),
            text_color=PALETTE["text_secondary"],
            anchor="w"
        ).pack(side="left")

    def _nav_button(self, icon, label):
        frame = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        frame.pack(fill="x", padx=12, pady=2)

        inner = ctk.CTkFrame(frame, fg_color="transparent", corner_radius=8)
        inner.pack(fill="x")

        icon_lbl = ctk.CTkLabel(
            inner, text=icon,
            font=ctk.CTkFont(size=14),
            text_color=PALETTE["text_secondary"],
            width=28, anchor="center"
        )
        icon_lbl.pack(side="left", padx=(12, 4), pady=10)

        text_lbl = ctk.CTkLabel(
            inner, text=label,
            font=ctk.CTkFont(family="Georgia", size=13),
            text_color=PALETTE["text_secondary"],
            anchor="w"
        )
        text_lbl.pack(side="left", fill="x", expand=True, pady=10)

        def activate(e=None):
            self.set_active(label)
            self.on_select(label)

        for w in (frame, inner, icon_lbl, text_lbl):
            w.bind("<Button-1>", activate)

        return {"frame": frame, "inner": inner, "icon": icon_lbl, "text": text_lbl}

    def set_active(self, label):
        if self._active and self._active in self.nav_buttons:
            prev = self.nav_buttons[self._active]
            prev["inner"].configure(fg_color="transparent")
            prev["icon"].configure(text_color=PALETTE["text_secondary"])
            prev["text"].configure(text_color=PALETTE["text_secondary"],
                                   font=ctk.CTkFont(family="Georgia", size=13))

        if label in self.nav_buttons:
            cur = self.nav_buttons[label]
            cur["inner"].configure(fg_color=PALETTE["bg"])
            cur["icon"].configure(text_color=PALETTE["accent"])
            cur["text"].configure(text_color=PALETTE["text_primary"],
                                  font=ctk.CTkFont(family="Georgia", size=13, weight="bold"))
        self._active = label


# ══════════════════════════════════════════════════════════════════════════════
#  STAT CARD
# ══════════════════════════════════════════════════════════════════════════════
class StatCard(ctk.CTkFrame):
    def __init__(self, master, label, value, sub="", accent=None, **kwargs):
        super().__init__(
            master,
            corner_radius=10,
            fg_color=PALETTE["surface_2"],
            border_width=1,
            border_color=PALETTE["border"],
            **kwargs
        )
        accent = accent or PALETTE["accent"]
        ctk.CTkFrame(self, width=3, fg_color=accent, corner_radius=2).pack(
            side="left", fill="y", padx=(0, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=16)

        ctk.CTkLabel(
            body, text=label.upper(),
            font=ctk.CTkFont(family="Courier New", size=9, weight="bold"),
            text_color=PALETTE["text_dim"], anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            body, text=value,
            font=ctk.CTkFont(family="Georgia", size=28, weight="bold"),
            text_color=PALETTE["text_primary"], anchor="w"
        ).pack(fill="x")

        if sub:
            ctk.CTkLabel(
                body, text=sub,
                font=ctk.CTkFont(family="Courier New", size=10),
                text_color=PALETTE["text_secondary"], anchor="w"
            ).pack(fill="x")


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD PANEL
# ══════════════════════════════════════════════════════════════════════════════
class DashboardPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()

    def _build(self):
        # ── Page header ─────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=36, pady=(32, 0))

        ctk.CTkLabel(
            hdr,
            text="Executive Overview",
            font=ctk.CTkFont(family="Georgia", size=28, weight="bold"),
            text_color=PALETTE["text_primary"],
            anchor="w"
        ).pack(side="left")

        make_badge(hdr, "LIVE", color=PALETTE["positive"], bg=PALETTE["surface_2"]).pack(
            side="right", pady=6)

        ctk.CTkLabel(
            self,
            text="Real-time legal intelligence and legislative monitoring.",
            font=ctk.CTkFont(family="Courier New", size=11),
            text_color=PALETTE["text_secondary"],
            anchor="w"
        ).pack(fill="x", padx=36, pady=(4, 24))

        # ── Stat cards row ────────────────────────────────────────────────
        cards_row = ctk.CTkFrame(self, fg_color="transparent")
        cards_row.pack(fill="x", padx=36, pady=(0, 28))
        cards_row.columnconfigure((0, 1, 2), weight=1, uniform="card")

        StatCard(cards_row, "Active Bills",   "247",  sub="↑ 12 this week",   accent=PALETTE["accent"]).grid(
            row=0, column=0, sticky="nsew", padx=(0, 10))
        StatCard(cards_row, "Legal Queries",  "1,483", sub="This session",    accent=PALETTE["blue_soft"]).grid(
            row=0, column=1, sticky="nsew", padx=5)
        StatCard(cards_row, "Jurisdictions", "52",    sub="All US states",    accent=PALETTE["positive"]).grid(
            row=0, column=2, sticky="nsew", padx=(10, 0))

        # ── Recent activity ───────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="RECENT ACTIVITY",
            font=ctk.CTkFont(family="Courier New", size=9, weight="bold"),
            text_color=PALETTE["text_dim"],
            anchor="w"
        ).pack(fill="x", padx=36, pady=(0, 8))

        feed = ctk.CTkScrollableFrame(
            self,
            fg_color=PALETTE["surface_2"],
            corner_radius=10,
            border_width=1,
            border_color=PALETTE["border"],
            scrollbar_fg_color=PALETTE["surface_2"],
            scrollbar_button_color=PALETTE["border"],
        )
        feed.pack(fill="both", expand=True, padx=36, pady=(0, 32))

        activities = [
            ("⚖",  "Contract law query resolved",      "2 min ago",  PALETTE["accent"]),
            ("📄", "SB 2041 status updated to Passed",  "14 min ago", PALETTE["positive"]),
            ("⚖",  "GDPR compliance analysis complete", "1 hr ago",   PALETTE["blue_soft"]),
            ("📄", "HB 1187 introduced in committee",   "3 hrs ago",  PALETTE["warning"]),
            ("⚖",  "Tort liability brief generated",    "Yesterday",  PALETTE["accent"]),
            ("📄", "AB 345 signed into law",            "2 days ago", PALETTE["positive"]),
        ]

        for icon, desc, when, color in activities:
            row = ctk.CTkFrame(feed, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)

            dot = ctk.CTkFrame(row, width=6, height=6, corner_radius=3, fg_color=color)
            dot.pack(side="left", padx=(0, 12))
            dot.pack_propagate(False)

            ctk.CTkLabel(
                row, text=desc,
                font=ctk.CTkFont(family="Georgia", size=12),
                text_color=PALETTE["text_primary"], anchor="w"
            ).pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                row, text=when,
                font=ctk.CTkFont(family="Courier New", size=10),
                text_color=PALETTE["text_dim"], anchor="e"
            ).pack(side="right")

            make_divider(feed, padx=0, pady=(0, 0))


# ══════════════════════════════════════════════════════════════════════════════
#  LEGAL Q&A PANEL
# ══════════════════════════════════════════════════════════════════════════════
class LegalQAPanel(ctk.CTkFrame):
    def __init__(self, master, backend, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.backend = backend
        self._history = []
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=36, pady=(32, 0))

        ctk.CTkLabel(
            hdr,
            text="Legal Research Assistant",
            font=ctk.CTkFont(family="Georgia", size=28, weight="bold"),
            text_color=PALETTE["text_primary"], anchor="w"
        ).pack(side="left")

        make_badge(hdr, "AI-POWERED", color=PALETTE["accent"], bg=PALETTE["surface_2"]).pack(
            side="right", pady=6)

        ctk.CTkLabel(
            self,
            text="Ask any legal question — statutes, case law, compliance, contracts.",
            font=ctk.CTkFont(family="Courier New", size=11),
            text_color=PALETTE["text_secondary"], anchor="w"
        ).pack(fill="x", padx=36, pady=(4, 20))

        # ── Conversation area ────────────────────────────────────────────
        self.chat_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=PALETTE["surface_2"],
            corner_radius=10,
            border_width=1,
            border_color=PALETTE["border"],
            scrollbar_button_color=PALETTE["border"],
        )
        self.chat_scroll.pack(fill="both", expand=True, padx=36, pady=(0, 16))

        self._add_system_msg(
            "Welcome to Executive Insight Legal. "
            "Ask any legal question below and receive AI-assisted analysis. "
            "This tool does not constitute legal advice."
        )

        # ── Input bar ─────────────────────────────────────────────────────
        input_frame = ctk.CTkFrame(
            self,
            fg_color=PALETTE["surface_2"],
            corner_radius=12,
            border_width=1,
            border_color=PALETTE["border"]
        )
        input_frame.pack(fill="x", padx=36, pady=(0, 32))

        self.entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your legal question…",
            placeholder_text_color=PALETTE["text_dim"],
            fg_color="transparent",
            border_width=0,
            text_color=PALETTE["text_primary"],
            font=ctk.CTkFont(family="Georgia", size=13),
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=16, pady=12)
        self.entry.bind("<Return>", lambda e: self._submit())

        self.submit_btn = ctk.CTkButton(
            input_frame,
            text="Submit  ↵",
            width=120,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(family="Courier New", size=11, weight="bold"),
            fg_color=PALETTE["accent"],
            hover_color=PALETTE["accent_dim"],
            text_color="#0D0F14",
            command=self._submit
        )
        self.submit_btn.pack(side="right", padx=12, pady=10)

    # ── Chat helpers ───────────────────────────────────────────────────────────
    def _add_system_msg(self, text):
        bubble = ctk.CTkFrame(self.chat_scroll, fg_color=PALETTE["bg"], corner_radius=8)
        bubble.pack(fill="x", padx=8, pady=(12, 4))

        ctk.CTkLabel(
            bubble,
            text="SYSTEM",
            font=ctk.CTkFont(family="Courier New", size=9, weight="bold"),
            text_color=PALETTE["text_dim"], anchor="w"
        ).pack(fill="x", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            bubble, text=text,
            font=ctk.CTkFont(family="Georgia", size=12),
            text_color=PALETTE["text_secondary"],
            wraplength=700, anchor="w", justify="left"
        ).pack(fill="x", padx=14, pady=(0, 10))

    def _add_user_msg(self, text):
        bubble = ctk.CTkFrame(self.chat_scroll, fg_color=PALETTE["surface"], corner_radius=8,
                              border_width=1, border_color=PALETTE["border"])
        bubble.pack(fill="x", padx=8, pady=4)

        ctk.CTkLabel(
            bubble,
            text="YOU",
            font=ctk.CTkFont(family="Courier New", size=9, weight="bold"),
            text_color=PALETTE["accent"], anchor="w"
        ).pack(fill="x", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            bubble, text=text,
            font=ctk.CTkFont(family="Georgia", size=13),
            text_color=PALETTE["text_primary"],
            wraplength=700, anchor="w", justify="left"
        ).pack(fill="x", padx=14, pady=(0, 10))

    def _add_response_msg(self, text):
        bubble = ctk.CTkFrame(self.chat_scroll, fg_color=PALETTE["surface"], corner_radius=8,
                              border_width=1, border_color=PALETTE["accent_dim"])
        bubble.pack(fill="x", padx=8, pady=(4, 12))

        hdr_row = ctk.CTkFrame(bubble, fg_color="transparent")
        hdr_row.pack(fill="x", padx=14, pady=(10, 4))

        ctk.CTkLabel(
            hdr_row,
            text="LEGAL ANALYSIS",
            font=ctk.CTkFont(family="Courier New", size=9, weight="bold"),
            text_color=PALETTE["accent"], anchor="w"
        ).pack(side="left")

        make_badge(hdr_row, "AI", color=PALETTE["accent_dim"], bg=PALETTE["border"]).pack(side="right")

        ctk.CTkLabel(
            bubble, text=text,
            font=ctk.CTkFont(family="Courier New", size=12),
            text_color=PALETTE["text_primary"],
            wraplength=700, anchor="w", justify="left"
        ).pack(fill="x", padx=14, pady=(0, 12))

    def _add_thinking(self):
        frame = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        frame.pack(fill="x", padx=8, pady=4)
        lbl = ctk.CTkLabel(
            frame,
            text="● Analyzing…",
            font=ctk.CTkFont(family="Courier New", size=11),
            text_color=PALETTE["text_dim"], anchor="w"
        )
        lbl.pack(padx=14)
        return frame

    # ── Submission ─────────────────────────────────────────────────────────────
    def _submit(self):
        q = self.entry.get().strip()
        if not q:
            return

        self.entry.delete(0, "end")
        self.submit_btn.configure(state="disabled", text="Analyzing…")
        self._add_user_msg(q)
        thinking = self._add_thinking()

        def worker():
            response = self.backend.process_legal_question(q)
            self.after(0, lambda: self._handle_response(thinking, response))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_response(self, thinking_widget, response):
        thinking_widget.destroy()
        self._add_response_msg(response)
        self.submit_btn.configure(state="normal", text="Submit  ↵")
        # Auto-scroll to bottom
        self.chat_scroll._parent_canvas.yview_moveto(1.0)


# ══════════════════════════════════════════════════════════════════════════════
#  BILLS PANEL
# ══════════════════════════════════════════════════════════════════════════════
class BillsPanel(ctk.CTkFrame):
    SAMPLE_BILLS = [
        ("SB 2041", "Digital Privacy Protection Act",      "PASSED",   "Federal",    PALETTE["positive"]),
        ("HB 1187", "Small Business Tax Relief Amendment", "COMMITTEE", "California", PALETTE["warning"]),
        ("AB 345",  "AI Accountability Framework",         "SIGNED",   "Federal",    PALETTE["positive"]),
        ("SB 089",  "Healthcare Data Interoperability",    "FLOOR",    "New York",   PALETTE["blue_soft"]),
        ("HR 2209", "Cybersecurity Infrastructure Bill",   "INTRODUCED","Federal",   PALETTE["text_dim"]),
        ("AB 912",  "Consumer Protection Modernisation",   "HEARING",  "Texas",      PALETTE["warning"]),
    ]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=36, pady=(32, 0))

        ctk.CTkLabel(
            hdr,
            text="Legislative Bills",
            font=ctk.CTkFont(family="Georgia", size=28, weight="bold"),
            text_color=PALETTE["text_primary"], anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            self,
            text="Track bills across federal and state legislatures in real time.",
            font=ctk.CTkFont(family="Courier New", size=11),
            text_color=PALETTE["text_secondary"], anchor="w"
        ).pack(fill="x", padx=36, pady=(4, 20))

        # ── Search bar ────────────────────────────────────────────────────
        search_bar = ctk.CTkFrame(self, fg_color=PALETTE["surface_2"], corner_radius=10,
                                   border_width=1, border_color=PALETTE["border"])
        search_bar.pack(fill="x", padx=36, pady=(0, 16))

        ctk.CTkEntry(
            search_bar,
            placeholder_text="Search bills by title, number, or keyword…",
            placeholder_text_color=PALETTE["text_dim"],
            fg_color="transparent",
            border_width=0,
            text_color=PALETTE["text_primary"],
            font=ctk.CTkFont(family="Georgia", size=13),
        ).pack(side="left", fill="x", expand=True, padx=16, pady=10)

        ctk.CTkButton(
            search_bar, text="Search",
            width=90, height=32, corner_radius=6,
            fg_color=PALETTE["border"],
            hover_color=PALETTE["surface"],
            text_color=PALETTE["text_secondary"],
            font=ctk.CTkFont(family="Courier New", size=10, weight="bold"),
        ).pack(side="right", padx=10, pady=8)

        # ── Table header ─────────────────────────────────────────────────
        col_hdr = ctk.CTkFrame(self, fg_color="transparent")
        col_hdr.pack(fill="x", padx=36, pady=(0, 4))
        col_hdr.columnconfigure(0, weight=1)
        col_hdr.columnconfigure(1, weight=3)
        col_hdr.columnconfigure(2, weight=1)
        col_hdr.columnconfigure(3, weight=1)

        for i, col in enumerate(("BILL NO.", "TITLE", "STATUS", "JURISDICTION")):
            ctk.CTkLabel(
                col_hdr, text=col,
                font=ctk.CTkFont(family="Courier New", size=9, weight="bold"),
                text_color=PALETTE["text_dim"], anchor="w"
            ).grid(row=0, column=i, sticky="w", padx=6)

        # ── Bill rows ─────────────────────────────────────────────────────
        table = ctk.CTkScrollableFrame(
            self, fg_color=PALETTE["surface_2"], corner_radius=10,
            border_width=1, border_color=PALETTE["border"],
            scrollbar_button_color=PALETTE["border"],
        )
        table.pack(fill="both", expand=True, padx=36, pady=(0, 32))

        for num, title, status, juris, color in self.SAMPLE_BILLS:
            row = ctk.CTkFrame(table, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)
            row.columnconfigure(0, weight=1)
            row.columnconfigure(1, weight=3)
            row.columnconfigure(2, weight=1)
            row.columnconfigure(3, weight=1)

            ctk.CTkLabel(
                row, text=num,
                font=ctk.CTkFont(family="Courier New", size=12, weight="bold"),
                text_color=PALETTE["accent"], anchor="w"
            ).grid(row=0, column=0, sticky="w", padx=6, pady=10)

            ctk.CTkLabel(
                row, text=title,
                font=ctk.CTkFont(family="Georgia", size=12),
                text_color=PALETTE["text_primary"], anchor="w"
            ).grid(row=0, column=1, sticky="w", padx=6, pady=10)

            status_frame = ctk.CTkFrame(row, fg_color=PALETTE["bg"], corner_radius=4)
            status_frame.grid(row=0, column=2, sticky="w", padx=6, pady=10)
            ctk.CTkLabel(
                status_frame, text=status,
                font=ctk.CTkFont(family="Courier New", size=9, weight="bold"),
                text_color=color
            ).pack(padx=8, pady=3)

            ctk.CTkLabel(
                row, text=juris,
                font=ctk.CTkFont(family="Courier New", size=11),
                text_color=PALETTE["text_secondary"], anchor="w"
            ).grid(row=0, column=3, sticky="w", padx=6, pady=10)

            make_divider(table, padx=0, pady=0)


# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS PANEL
# ══════════════════════════════════════════════════════════════════════════════
class SettingsPanel(ctk.CTkFrame):
    def __init__(self, master, backend, on_theme_change, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.backend         = backend
        self.on_theme_change = on_theme_change
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self,
            text="Application Settings",
            font=ctk.CTkFont(family="Georgia", size=28, weight="bold"),
            text_color=PALETTE["text_primary"], anchor="w"
        ).pack(fill="x", padx=36, pady=(32, 4))

        ctk.CTkLabel(
            self,
            text="Configure appearance, data sources, and AI behaviour.",
            font=ctk.CTkFont(family="Courier New", size=11),
            text_color=PALETTE["text_secondary"], anchor="w"
        ).pack(fill="x", padx=36, pady=(0, 28))

        # ── Section: Appearance ────────────────────────────────────────────
        self._section_label("APPEARANCE")

        card = self._card()

        self._setting_row(card, "Theme",
                          "Choose the application colour theme.",
                          self._make_theme_menu(card))
        make_divider(card, padx=16)
        self._setting_row(card, "Colour Mode",
                          "System-wide light / dark mode.",
                          self._make_mode_menu(card))

        # ── Section: AI Configuration ──────────────────────────────────────
        self._section_label("AI CONFIGURATION")

        card2 = self._card()
        self._setting_row(card2, "Response Detail",
                          "Amount of explanation included in AI responses.",
                          self._make_detail_menu(card2))
        make_divider(card2, padx=16)
        self._setting_row(card2, "Jurisdiction Default",
                          "Assume this jurisdiction when none is specified.",
                          self._make_juris_menu(card2))

        # ── Section: About ─────────────────────────────────────────────────
        self._section_label("ABOUT")
        about = self._card()
        for k, v in [("Version", "2.4.1"), ("Build", "2026-03-04"), ("License", "Enterprise")]:
            row = ctk.CTkFrame(about, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=6)
            ctk.CTkLabel(row, text=k,
                         font=ctk.CTkFont(family="Courier New", size=11),
                         text_color=PALETTE["text_secondary"], anchor="w", width=160).pack(side="left")
            ctk.CTkLabel(row, text=v,
                         font=ctk.CTkFont(family="Georgia", size=12),
                         text_color=PALETTE["text_primary"], anchor="w").pack(side="left")

    def _section_label(self, text):
        ctk.CTkLabel(
            self, text=text,
            font=ctk.CTkFont(family="Courier New", size=9, weight="bold"),
            text_color=PALETTE["text_dim"], anchor="w"
        ).pack(fill="x", padx=36, pady=(16, 6))

    def _card(self):
        card = ctk.CTkFrame(self, fg_color=PALETTE["surface_2"], corner_radius=10,
                             border_width=1, border_color=PALETTE["border"])
        card.pack(fill="x", padx=36, pady=(0, 4))
        return card

    def _setting_row(self, parent, label, desc, widget):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(info, text=label,
                     font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
                     text_color=PALETTE["text_primary"], anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=desc,
                     font=ctk.CTkFont(family="Courier New", size=10),
                     text_color=PALETTE["text_secondary"], anchor="w").pack(fill="x")

        widget.pack(side="right")

    # ── Widgets ──────────────────────────────────────────────────────────────
    def _option_menu(self, parent, values, command=None):
        return ctk.CTkOptionMenu(
            parent, values=values,
            width=160, height=32, corner_radius=8,
            fg_color=PALETTE["surface"],
            button_color=PALETTE["border"],
            button_hover_color=PALETTE["accent_dim"],
            dropdown_fg_color=PALETTE["surface_2"],
            dropdown_text_color=PALETTE["text_primary"],
            dropdown_hover_color=PALETTE["border"],
            text_color=PALETTE["text_primary"],
            font=ctk.CTkFont(family="Courier New", size=11),
            command=command,
        )

    def _make_theme_menu(self, parent):
        return self._option_menu(parent, self.backend.get_theme_names(), self.on_theme_change)

    def _make_mode_menu(self, parent):
        def change_mode(v):
            ctk.set_appearance_mode(v.lower())
        return self._option_menu(parent, ["Dark", "Light", "System"], change_mode)

    def _make_detail_menu(self, parent):
        return self._option_menu(parent, ["Concise", "Standard", "Detailed", "Comprehensive"])

    def _make_juris_menu(self, parent):
        return self._option_menu(parent, ["Federal (US)", "California", "New York", "Texas",
                                           "Florida", "UK", "EU", "Other"])


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════
class ExecutiveInsightApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.backend = ExecutiveInsightBackend()

        self.title("Executive Insight — Legal Intelligence Platform")
        self.geometry("1200x780")
        self.minsize(1000, 680)
        self.configure(fg_color=PALETTE["bg"])

        self._build_layout()
        self._show_panel("Dashboard")
        self.sidebar.set_active("Dashboard")

    # ── Layout ─────────────────────────────────────────────────────────────────
    def _build_layout(self):
        # Top bar (1px gold line)
        accent_bar = ctk.CTkFrame(self, height=2, fg_color=PALETTE["accent"], corner_radius=0)
        accent_bar.pack(fill="x", side="top")

        # Main horizontal split
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = Sidebar(body, on_select=self._show_panel)
        self.sidebar.pack(side="left", fill="y")

        # Vertical separator
        ctk.CTkFrame(body, width=1, fg_color=PALETTE["border"], corner_radius=0).pack(
            side="left", fill="y")

        # Content area
        self.content_area = ctk.CTkFrame(body, fg_color=PALETTE["bg"], corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)

        # Pre-build panels (hide all except active)
        self.panels = {
            "Dashboard": DashboardPanel(self.content_area),
            "Legal Q&A":  LegalQAPanel(self.content_area, self.backend),
            "Bills":       BillsPanel(self.content_area),
            "Settings":    SettingsPanel(self.content_area, self.backend,
                                          on_theme_change=self._change_theme),
        }

    def _show_panel(self, name):
        for panel in self.panels.values():
            panel.pack_forget()
        if name in self.panels:
            self.panels[name].pack(fill="both", expand=True)

    def _change_theme(self, choice):
        self.backend.set_theme(choice)

# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = ExecutiveInsightApp()
    app.mainloop()
