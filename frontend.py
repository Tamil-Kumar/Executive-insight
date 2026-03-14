"""
scraper_panels.py
─────────────────
Drop-in replacement panel classes for Executive Insight.
Replaces: USWarsPanel, ElectionHistoryPanel, EconomyPanel,
          CongressPanel, ScotusPanel

Dependencies (install once):
    pip install requests beautifulsoup4 googlesearch-python

Usage: place this file in the same folder as frontend.py, then
add this near the top of frontend.py (after all data variables):

    from scraper_panels import (
        USWarsPanel, ElectionHistoryPanel, EconomyPanel,
        CongressPanel, ScotusPanel
    )

Then delete the original five class definitions from frontend.py.
"""

import threading
import time
import random

import requests
from bs4 import BeautifulSoup

import customtkinter as ctk


# ── Shared scraper helpers ─────────────────────────────────────────────────────

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


def _google_search_results(query, num=8):
    results = []

    # Strategy 1: googlesearch-python
    try:
        from googlesearch import search as _gsearch
        urls = list(_gsearch(query, num_results=num, lang="en", sleep_interval=1))
        for url in urls:
            results.append({"title": url, "url": url, "snippet": ""})
        if results:
            enriched = []
            for item in results[:num]:
                try:
                    r = requests.get(
                        item["url"], timeout=4,
                        headers={"User-Agent": random.choice(_USER_AGENTS)},
                        allow_redirects=True,
                    )
                    soup = BeautifulSoup(r.text, "html.parser")
                    title = soup.find("title")
                    meta = soup.find("meta", attrs={"name": "description"})
                    enriched.append({
                        "title":   title.get_text(strip=True) if title else item["url"],
                        "url":     item["url"],
                        "snippet": meta["content"][:220] if meta and meta.get("content") else "",
                    })
                except Exception:
                    enriched.append(item)
                time.sleep(0.3)
            return enriched
    except ImportError:
        pass
    except Exception:
        pass

    # Strategy 2: Direct Google HTML scrape
    try:
        headers = {
            "User-Agent": random.choice(_USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
        }
        params = {"q": query, "num": num, "hl": "en", "gl": "us"}
        resp = requests.get(
            "https://www.google.com/search",
            params=params, headers=headers, timeout=8,
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        for div in soup.select("div.g, div.tF2Cxc, div.kvH3mc"):
            a_tag  = div.find("a", href=True)
            h3_tag = div.find("h3")
            snip   = div.find("div", attrs={"data-sncf": True}) or \
                     div.find("span", class_="aCOpRe")
            if not a_tag:
                continue
            results.append({
                "title":   h3_tag.get_text(strip=True) if h3_tag else a_tag["href"],
                "url":     a_tag["href"],
                "snippet": snip.get_text(strip=True)[:220] if snip else "",
            })
            if len(results) >= num:
                break
    except Exception:
        pass

    return results


def _make_scraper_section(parent_frame, default_query, palette):
    outer = ctk.CTkFrame(
        parent_frame,
        fg_color=palette["surface"],
        corner_radius=10,
        border_width=1,
        border_color=palette["accent"],
    )
    outer.pack(fill="x", padx=0, pady=(0, 16))

    hdr = ctk.CTkFrame(outer, fg_color="transparent")
    hdr.pack(fill="x", padx=16, pady=(12, 8))
    ctk.CTkLabel(hdr, text="🔍  LIVE GOOGLE SEARCH",
                 font=("Courier New", 9, "bold"),
                 text_color=palette["accent"], anchor="w").pack(side="left")
    status_lbl = ctk.CTkLabel(hdr, text="", font=("Courier New", 9),
                               text_color=palette["text_dim"])
    status_lbl.pack(side="right")

    bar = ctk.CTkFrame(outer, fg_color=palette["surface_2"],
                       corner_radius=8, border_width=1, border_color=palette["border"])
    bar.pack(fill="x", padx=16, pady=(0, 10))

    entry = ctk.CTkEntry(bar, placeholder_text="Enter search query...",
                         fg_color="transparent", border_width=0,
                         text_color=palette["text_primary"], font=("Georgia", 12))
    entry.pack(side="left", fill="x", expand=True, padx=12, pady=8)
    entry.insert(0, default_query)

    search_btn = ctk.CTkButton(
        bar, text="Search", width=80, height=30, corner_radius=6,
        fg_color=palette["accent"], hover_color=palette["accent_dim"],
        text_color=palette["bg"], font=("Courier New", 10, "bold"),
    )
    search_btn.pack(side="right", padx=(0, 8), pady=6)

    results_scroll = ctk.CTkScrollableFrame(
        outer, fg_color="transparent", height=280,
        scrollbar_button_color=palette["border"],
    )
    results_scroll.pack(fill="x", padx=16, pady=(0, 12))

    ctk.CTkLabel(results_scroll,
                 text='Press "Search" to fetch live results from Google.',
                 font=("Courier New", 10),
                 text_color=palette["text_dim"]).pack(pady=20)

    def _run_search(query=None):
        q = query or entry.get().strip()
        if not q:
            return
        for w in results_scroll.winfo_children():
            w.destroy()
        ctk.CTkLabel(results_scroll, text="Fetching results...",
                     font=("Courier New", 10),
                     text_color=palette["warning"]).pack(pady=20)
        status_lbl.configure(text="searching...")
        search_btn.configure(state="disabled")

        def _fetch():
            data = _google_search_results(q, num=8)
            outer.after(0, _render_results, data)

        def _render_results(data):
            for w in results_scroll.winfo_children():
                w.destroy()
            status_lbl.configure(text=f"{len(data)} results")
            search_btn.configure(state="normal")
            if not data:
                ctk.CTkLabel(
                    results_scroll,
                    text=(
                        "No results returned.\n\n"
                        "Possible causes:\n"
                        "  - No internet connection\n"
                        "  - Google blocked the request (try again in 60s)\n"
                        "  - googlesearch-python not installed\n\n"
                        "Install with:  pip install googlesearch-python"
                    ),
                    font=("Courier New", 10), text_color=palette["danger"],
                    justify="left",
                ).pack(pady=16, padx=8, anchor="w")
                return
            for item in data:
                _make_result_card(results_scroll, item, palette)

        threading.Thread(target=_fetch, daemon=True).start()

    search_btn.configure(command=_run_search)
    entry.bind("<Return>", lambda e: _run_search())
    return outer, _run_search


def _make_result_card(parent, item, palette):
    card = ctk.CTkFrame(parent, fg_color=palette["surface_2"],
                        corner_radius=8, border_width=1,
                        border_color=palette["border"])
    card.pack(fill="x", pady=(0, 6))

    title_text = item["title"] or item["url"]
    if len(title_text) > 90:
        title_text = title_text[:87] + "..."

    ctk.CTkLabel(card, text=title_text, font=("Georgia", 11, "bold"),
                 text_color=palette["accent"], anchor="w",
                 wraplength=740, justify="left").pack(fill="x", padx=12, pady=(8, 2))
    ctk.CTkLabel(card,
                 text=item["url"][:80] + ("..." if len(item["url"]) > 80 else ""),
                 font=("Courier New", 8), text_color=palette["positive"],
                 anchor="w").pack(fill="x", padx=12)
    if item["snippet"]:
        ctk.CTkLabel(card, text=item["snippet"], font=("Courier New", 9),
                     text_color=palette["text_secondary"], anchor="w",
                     wraplength=740, justify="left").pack(fill="x", padx=12, pady=(4, 8))
    else:
        ctk.CTkFrame(card, height=6, fg_color="transparent").pack()


# ══════════════════════════════════════════════════════════════════════════════
#  US WARS PANEL
# ══════════════════════════════════════════════════════════════════════════════

class USWarsPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(40, 4))
        ctk.CTkLabel(hdr, text="U.S. Wars & Military Conflicts",
                     font=("Georgia", 24, "bold"),
                     text_color=PALETTE["text_primary"], anchor="w").pack(side="left")
        ongoing = sum(1 for w in WARS_DATA if w["status"] == "ongoing")
        badge = ctk.CTkFrame(hdr, fg_color="#8A1A1A", corner_radius=4)
        badge.pack(side="right", pady=6)
        ctk.CTkLabel(badge,
                     text=f"  {ongoing} ACTIVE CONFLICT{'S' if ongoing != 1 else ''}  ",
                     font=("Courier New", 9, "bold"),
                     text_color="#D94A4A").pack(pady=4)
        ctk.CTkLabel(self,
                     text="Search Google for live updates, or browse the historical record below.",
                     font=("Courier New", 11),
                     text_color=PALETTE["text_secondary"], anchor="w").pack(fill="x", padx=40, pady=(0, 12))

        outer_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                               scrollbar_button_color=PALETTE["border"])
        outer_scroll.pack(fill="both", expand=True, padx=40, pady=(0, 32))

        _make_scraper_section(outer_scroll,
                              default_query="US military conflicts 2025 2026 latest news",
                              palette=PALETTE)

        disc = ctk.CTkFrame(outer_scroll, fg_color=PALETTE["surface_2"],
                            corner_radius=8, border_width=1, border_color=PALETTE["border"])
        disc.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(disc,
                     text="⚠  Figures below are historically documented totals. "
                          "Iran War deaths reflect confirmed US KIA as of March 8, 2026.",
                     font=("Courier New", 10), text_color=PALETTE["text_dim"],
                     wraplength=900, justify="left", anchor="w").pack(fill="x", padx=16, pady=10)

        filter_row = ctk.CTkFrame(outer_scroll, fg_color="transparent")
        filter_row.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(filter_row, text="FILTER:", font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"]).pack(side="left", padx=(0, 10))
        self._cards = []
        for label in ("All", "Ongoing", "Historical"):
            ctk.CTkButton(filter_row, text=label, width=90, height=26, corner_radius=6,
                          fg_color=PALETTE["surface_2"], hover_color=PALETTE["border"],
                          text_color=PALETTE["text_secondary"], font=("Courier New", 10, "bold"),
                          command=lambda l=label: self._apply_filter(l)).pack(side="left", padx=(0, 6))

        ctk.CTkLabel(outer_scroll, text="HISTORICAL & ONGOING CONFLICTS  —  STATIC DATABASE",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"], anchor="w").pack(fill="x", pady=(4, 8))

        for war in WARS_DATA:
            card = WarCard(outer_scroll, war)
            card.pack(fill="x", pady=(0, 12))
            self._cards.append((war["status"], card))

    def _apply_filter(self, label):
        for status, card in self._cards:
            if label == "All":
                card.pack(fill="x", pady=(0, 12))
            elif label == "Ongoing" and status == "ongoing":
                card.pack(fill="x", pady=(0, 12))
            elif label == "Historical" and status == "historical":
                card.pack(fill="x", pady=(0, 12))
            else:
                card.pack_forget()


# ══════════════════════════════════════════════════════════════════════════════
#  ELECTION HISTORY PANEL
# ══════════════════════════════════════════════════════════════════════════════

class ElectionHistoryPanel(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(32, 4))
        ctk.CTkLabel(hdr, text="U.S. Presidential Election History",
                     font=("Georgia", 24, "bold"),
                     text_color=PALETTE["text_primary"], anchor="w").pack(side="left")
        badge = ctk.CTkFrame(hdr, fg_color=PALETTE["surface_2"], corner_radius=4,
                             border_width=1, border_color=PALETTE["border"])
        badge.pack(side="right", pady=6)
        r_wins = sum(1 for e in ELECTION_DATA if e["winner_party"] == "R")
        d_wins = len(ELECTION_DATA) - r_wins
        ctk.CTkLabel(badge,
                     text=f"  🔴 R: {r_wins}  |  🔵 D: {d_wins}  ({len(ELECTION_DATA)} elections)  ",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"]).pack(pady=4)
        ctk.CTkLabel(self,
                     text="Search Google for live election news, or browse the historical record below.",
                     font=("Courier New", 11),
                     text_color=PALETTE["text_secondary"], anchor="w").pack(fill="x", padx=40, pady=(0, 12))

        frow = ctk.CTkFrame(self, fg_color="transparent")
        frow.pack(fill="x", padx=40, pady=(0, 8))
        ctk.CTkLabel(frow, text="FILTER:", font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"]).pack(side="left", padx=(0, 10))
        for label in ("All", "Republican wins", "Democrat wins"):
            ctk.CTkButton(frow, text=label, width=130, height=26, corner_radius=6,
                          fg_color=PALETTE["surface_2"], hover_color=PALETTE["border"],
                          text_color=PALETTE["text_secondary"], font=("Courier New", 10, "bold"),
                          command=lambda l=label: self._filter(l)).pack(side="left", padx=(0, 6))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        scrollbar_button_color=PALETTE["border"])
        scroll.pack(fill="both", expand=True, padx=40, pady=(0, 32))
        self._scroll = scroll

        _make_scraper_section(scroll,
                              default_query="US presidential election results 2024 news",
                              palette=PALETTE)

        ctk.CTkLabel(scroll, text="ELECTION HISTORY DATABASE",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"], anchor="w").pack(fill="x", pady=(4, 8))

        self._election_cards = []
        for e in ELECTION_DATA:
            card = ElectionCard(scroll, e)
            self._election_cards.append((e["winner_party"], card))
        self._filter("All")

    def _filter(self, label):
        for party, card in self._election_cards:
            if label == "Republican wins" and party != "R":
                card.pack_forget()
            elif label == "Democrat wins" and party != "D":
                card.pack_forget()
            else:
                card.pack(fill="x", pady=(0, 10))


# ══════════════════════════════════════════════════════════════════════════════
#  ECONOMY PANEL
# ══════════════════════════════════════════════════════════════════════════════

class EconomyPanel(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._build()

    def _build(self):
        cur = ECON_DATA["current"]

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(32, 4))
        ctk.CTkLabel(hdr, text="U.S. Economic Dashboard",
                     font=("Georgia", 24, "bold"),
                     text_color=PALETTE["text_primary"], anchor="w").pack(side="left")
        ctk.CTkLabel(hdr, text=f"  as of {cur['as_of']}",
                     font=("Courier New", 10),
                     text_color=PALETTE["text_dim"]).pack(side="left", pady=(8, 0))
        ctk.CTkLabel(self,
                     text="Search for live economic data, or browse the historical record below.",
                     font=("Courier New", 11),
                     text_color=PALETTE["text_secondary"], anchor="w").pack(fill="x", padx=40, pady=(0, 12))

        irow = ctk.CTkFrame(self, fg_color="transparent")
        irow.pack(fill="x", padx=40, pady=(0, 16))
        indicators = [
            ("GDP GROWTH",      cur["gdp_growth"],           "positive"),
            ("INFLATION (CPI)", cur["inflation"],            "warning"),
            ("UNEMPLOYMENT",    cur["unemployment"],         "text_secondary"),
            ("FED FUNDS RATE",  cur["fed_rate"],             "accent"),
            ("S&P 500",         cur["sp500"],                "positive"),
            ("NATIONAL DEBT",   f"${cur['debt_trillion']}T", "danger"),
        ]
        for i, (label, val, col) in enumerate(indicators):
            card = ctk.CTkFrame(irow, fg_color=PALETTE["surface"], corner_radius=8,
                                border_width=1, border_color=PALETTE["border"])
            card.grid(row=0, column=i, padx=(0, 10) if i < 5 else 0, sticky="nsew")
            irow.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=label, font=("Courier New", 8, "bold"),
                         text_color=PALETTE["text_dim"]).pack(pady=(12, 2))
            ctk.CTkLabel(card, text=val, font=("Georgia", 14, "bold"),
                         text_color=PALETTE[col]).pack(pady=(0, 12))

        debt_frame = ctk.CTkFrame(self, fg_color=PALETTE["surface_2"],
                                  corner_radius=8, border_width=1, border_color=PALETTE["border"])
        debt_frame.pack(fill="x", padx=40, pady=(0, 12))
        debt_inner = ctk.CTkFrame(debt_frame, fg_color="transparent")
        debt_inner.pack(fill="x", padx=16, pady=10)
        ctk.CTkLabel(debt_inner, text="⚠  National Debt Clock: ",
                     font=("Courier New", 10, "bold"),
                     text_color=PALETTE["warning"]).pack(side="left")
        ctk.CTkLabel(debt_inner,
                     text="$36.2 Trillion USD  •  ~$107,000 per citizen  •  ~130% of GDP",
                     font=("Courier New", 10),
                     text_color=PALETTE["text_secondary"]).pack(side="left")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        scrollbar_button_color=PALETTE["border"])
        scroll.pack(fill="both", expand=True, padx=40, pady=(0, 32))

        _make_scraper_section(scroll,
                              default_query="US economy GDP inflation unemployment 2025 2026",
                              palette=PALETTE)

        ctk.CTkLabel(scroll, text="ECONOMIC RECORD BY ADMINISTRATION",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"], anchor="w").pack(fill="x", pady=(4, 8))

        for era in ECON_DATA["eras"]:
            ec = PALETTE.get(era["color"], PALETTE["accent"])
            card = ctk.CTkFrame(scroll, fg_color=PALETTE["surface"], corner_radius=10,
                                border_width=1, border_color=PALETTE["border"])
            card.pack(fill="x", pady=(0, 10))
            stripe = ctk.CTkFrame(card, width=4, fg_color=ec, corner_radius=0)
            stripe.place(x=0, y=0, relheight=1)
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=14)
            for ci in range(5):
                row.columnconfigure(ci, weight=(2 if ci == 0 else (3 if ci == 4 else 1)))
            ctk.CTkLabel(row, text=f"{era['president']}  ({era['years']})",
                         font=("Georgia", 13, "bold"), text_color=ec, anchor="w"
                         ).grid(row=0, column=0, sticky="w")
            for col_i, (lbl, val) in enumerate([
                ("GDP Growth",   era["gdp"]),
                ("Inflation",    era["inflation"]),
                ("Unemployment", era["unemployment"]),
            ]):
                ctk.CTkLabel(row, text=lbl, font=("Courier New", 8, "bold"),
                             text_color=PALETTE["text_dim"], anchor="w"
                             ).grid(row=0, column=col_i + 1, sticky="w", padx=(10, 0))
                ctk.CTkLabel(row, text=val, font=("Courier New", 10),
                             text_color=PALETTE["text_primary"], anchor="w"
                             ).grid(row=1, column=col_i + 1, sticky="w", padx=(10, 0))
            ctk.CTkLabel(row, text=era["notes"], font=("Courier New", 10),
                         text_color=PALETTE["text_secondary"],
                         wraplength=340, justify="left", anchor="w"
                         ).grid(row=0, column=4, rowspan=2, sticky="w", padx=(16, 0))


# ══════════════════════════════════════════════════════════════════════════════
#  CONGRESS TRACKER PANEL
# ══════════════════════════════════════════════════════════════════════════════

class CongressPanel(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._build()

    def _build(self):
        cd = CONGRESS_DATA

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(32, 4))
        ctk.CTkLabel(hdr, text="Congress Tracker",
                     font=("Georgia", 24, "bold"),
                     text_color=PALETTE["text_primary"], anchor="w").pack(side="left")
        badge = ctk.CTkFrame(hdr, fg_color=PALETTE["surface_2"], corner_radius=4,
                             border_width=1, border_color=PALETTE["border"])
        badge.pack(side="right", pady=6)
        ctk.CTkLabel(badge, text=f"  {cd['session']}  ",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["accent"]).pack(pady=4)
        ctk.CTkLabel(self,
                     text="Search Google for live congressional news, or browse current composition & bills below.",
                     font=("Courier New", 11),
                     text_color=PALETTE["text_secondary"], anchor="w").pack(fill="x", padx=40, pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        scrollbar_button_color=PALETTE["border"])
        scroll.pack(fill="both", expand=True, padx=40, pady=(0, 32))

        _make_scraper_section(scroll,
                              default_query="US Congress legislation bills 2025 2026 latest",
                              palette=PALETTE)

        ctk.CTkLabel(scroll, text="CURRENT COMPOSITION  —  119th CONGRESS",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"], anchor="w").pack(fill="x", pady=(4, 8))

        chambers = ctk.CTkFrame(scroll, fg_color="transparent")
        chambers.pack(fill="x", pady=(0, 16))
        chambers.columnconfigure(0, weight=1)
        chambers.columnconfigure(1, weight=1)

        for col_i, (chamber_name, data) in enumerate([
            ("SENATE (100 seats)", cd["senate"]),
            ("HOUSE (435 seats)",  cd["house"]),
        ]):
            card = ctk.CTkFrame(chambers, fg_color=PALETTE["surface"], corner_radius=10,
                                border_width=1, border_color=PALETTE["border"])
            card.grid(row=0, column=col_i,
                      padx=(0, 8) if col_i == 0 else (8, 0), sticky="nsew")
            ctk.CTkLabel(card, text=chamber_name, font=("Courier New", 9, "bold"),
                         text_color=PALETTE["text_dim"], anchor="w").pack(fill="x", padx=16, pady=(14, 8))
            total = 100 if "senate" in chamber_name.lower() else 435
            r_seats = data["R"]
            d_seats = data["D"]
            bar_bg = ctk.CTkFrame(card, height=14, fg_color=PALETTE["dem_light"], corner_radius=4)
            bar_bg.pack(fill="x", padx=16, pady=(0, 8))
            ctk.CTkFrame(bar_bg, height=14, fg_color=PALETTE["rep_light"], corner_radius=4
                         ).place(relx=1.0, rely=0, relwidth=r_seats / total, relheight=1, anchor="ne")
            count_row = ctk.CTkFrame(card, fg_color="transparent")
            count_row.pack(fill="x", padx=16, pady=(0, 8))
            ctk.CTkLabel(count_row, text=f"🔵 D: {d_seats}",
                         font=("Courier New", 11, "bold"),
                         text_color=PALETTE["dem_light"]).pack(side="left")
            ctk.CTkLabel(count_row, text=f"  🔴 R: {r_seats}",
                         font=("Courier New", 11, "bold"),
                         text_color=PALETTE["rep_light"]).pack(side="left")
            if "I" in data:
                ctk.CTkLabel(count_row, text=f"  ⚪ I: {data['I']}",
                             font=("Courier New", 11, "bold"),
                             text_color=PALETTE["text_dim"]).pack(side="left")
            maj_color = PALETTE["rep_light"] if data["majority"] == "Republican" else PALETTE["dem_light"]
            ctk.CTkLabel(card, text=f"Majority: {data['majority']}",
                         font=("Courier New", 10, "bold"),
                         text_color=maj_color, anchor="w").pack(fill="x", padx=16, pady=(0, 4))
            if "speaker" in data:
                ctk.CTkLabel(card, text=f"Speaker: {data['speaker']}",
                             font=("Courier New", 10),
                             text_color=PALETTE["text_secondary"], anchor="w").pack(fill="x", padx=16)
                ctk.CTkLabel(card, text=f"Minority Leader: {data['minority_leader']}",
                             font=("Courier New", 10),
                             text_color=PALETTE["text_secondary"], anchor="w").pack(fill="x", padx=16, pady=(0, 14))
            else:
                ctk.CTkLabel(card, text=f"Majority Leader: {data['leader_R']}",
                             font=("Courier New", 10),
                             text_color=PALETTE["text_secondary"], anchor="w").pack(fill="x", padx=16)
                ctk.CTkLabel(card, text=f"Minority Leader: {data['leader_D']}",
                             font=("Courier New", 10),
                             text_color=PALETTE["text_secondary"], anchor="w").pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(scroll, text="RECENT LEGISLATION",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"], anchor="w").pack(fill="x", pady=(8, 8))

        STATUS_COLORS = {
            "SIGNED": "positive", "PASSED SENATE": "accent", "PASSED HOUSE": "accent",
            "BLOCKED": "danger", "VETOED": "danger", "PENDING": "text_secondary",
        }
        for bill in cd["recent_bills"]:
            sc = PALETTE.get(STATUS_COLORS.get(bill["status"], "text_secondary"), PALETTE["text_secondary"])
            pc = (PALETTE["rep_light"] if bill["party"] == "R"
                  else PALETTE["dem_light"] if bill["party"] == "D"
                  else PALETTE["accent"])
            bc = ctk.CTkFrame(scroll, fg_color=PALETTE["surface"], corner_radius=8,
                              border_width=1, border_color=PALETTE["border"])
            bc.pack(fill="x", pady=(0, 8))
            ctk.CTkFrame(bc, width=4, fg_color=pc, corner_radius=0).place(x=0, y=0, relheight=1)
            brow = ctk.CTkFrame(bc, fg_color="transparent")
            brow.pack(fill="x", padx=16, pady=10)
            ctk.CTkLabel(brow, text=bill["name"], font=("Georgia", 12, "bold"),
                         text_color=PALETTE["text_primary"], anchor="w").pack(side="left")
            stat_b = ctk.CTkFrame(brow, fg_color=PALETTE["surface_2"], corner_radius=4)
            stat_b.pack(side="right")
            ctk.CTkLabel(stat_b, text=bill["status"], font=("Courier New", 9, "bold"),
                         text_color=sc).pack(padx=8, pady=3)
            ctk.CTkLabel(bc, text=f"{bill['date']}  —  {bill['summary']}",
                         font=("Courier New", 10), text_color=PALETTE["text_secondary"],
                         wraplength=820, justify="left", anchor="w").pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(scroll, text="HISTORICAL COMPOSITION",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"], anchor="w").pack(fill="x", pady=(12, 8))

        for h in cd["historical"]:
            hc = ctk.CTkFrame(scroll, fg_color=PALETTE["surface_2"], corner_radius=6,
                              border_width=1, border_color=PALETTE["border"])
            hc.pack(fill="x", pady=(0, 6))
            ctk.CTkLabel(hc, text=h["year"], font=("Courier New", 10, "bold"),
                         text_color=PALETTE["accent"], anchor="w").pack(fill="x", padx=14, pady=(10, 2))
            ctk.CTkLabel(hc, text=f"Senate: {h['senate']}  |  House: {h['house']}",
                         font=("Courier New", 10), text_color=PALETTE["text_secondary"],
                         anchor="w").pack(fill="x", padx=14, pady=(0, 2))
            ctk.CTkLabel(hc, text=h["notes"], font=("Courier New", 10),
                         text_color=PALETTE["text_dim"], wraplength=820,
                         justify="left", anchor="w").pack(fill="x", padx=14, pady=(0, 10))


# ══════════════════════════════════════════════════════════════════════════════
#  SUPREME COURT PANEL
# ══════════════════════════════════════════════════════════════════════════════

class ScotusPanel(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(32, 4))
        ctk.CTkLabel(hdr, text="Supreme Court Tracker",
                     font=("Georgia", 24, "bold"),
                     text_color=PALETTE["text_primary"], anchor="w").pack(side="left")
        cons = sum(1 for j in SCOTUS_DATA["justices"] if j["leaning"] == "Conservative")
        lib  = len(SCOTUS_DATA["justices"]) - cons
        badge = ctk.CTkFrame(hdr, fg_color=PALETTE["surface_2"], corner_radius=4,
                             border_width=1, border_color=PALETTE["border"])
        badge.pack(side="right", pady=6)
        ctk.CTkLabel(badge,
                     text=f"  🔴 Conservative: {cons}  |  🔵 Liberal: {lib}  ",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"]).pack(pady=4)
        ctk.CTkLabel(self,
                     text="Search Google for live SCOTUS news, or browse justices and landmark rulings below.",
                     font=("Courier New", 11),
                     text_color=PALETTE["text_secondary"], anchor="w").pack(fill="x", padx=40, pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        scrollbar_button_color=PALETTE["border"])
        scroll.pack(fill="both", expand=True, padx=40, pady=(0, 32))

        _make_scraper_section(scroll,
                              default_query="Supreme Court ruling decision 2025 2026",
                              palette=PALETTE)

        ctk.CTkLabel(scroll, text="CURRENT JUSTICES",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"], anchor="w").pack(fill="x", pady=(4, 10))

        jgrid = ctk.CTkFrame(scroll, fg_color="transparent")
        jgrid.pack(fill="x", pady=(0, 20))
        for col_i in range(3):
            jgrid.columnconfigure(col_i, weight=1)

        for i, j in enumerate(SCOTUS_DATA["justices"]):
            jc = PALETTE["rep_light"] if j["leaning"] == "Conservative" else PALETTE["dem_light"]
            card = ctk.CTkFrame(jgrid, fg_color=PALETTE["surface"], corner_radius=8,
                                border_width=1, border_color=jc)
            card.grid(row=i // 3, column=i % 3, padx=4, pady=4, sticky="nsew")
            ctk.CTkFrame(card, height=3, fg_color=jc, corner_radius=0).pack(fill="x")
            ctk.CTkLabel(card, text=j["name"], font=("Georgia", 12, "bold"),
                         text_color=jc, anchor="w").pack(fill="x", padx=12, pady=(10, 2))
            ctk.CTkLabel(card, text=j["title"], font=("Courier New", 9),
                         text_color=PALETTE["text_dim"], anchor="w").pack(fill="x", padx=12)
            ctk.CTkLabel(card, text=f"Appt: {j['appointed_by']} ({j['year']})  •  Age: {j['age']}",
                         font=("Courier New", 9), text_color=PALETTE["text_secondary"],
                         anchor="w").pack(fill="x", padx=12, pady=(2, 10))

        ctk.CTkLabel(scroll, text="LANDMARK RULINGS",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"], anchor="w").pack(fill="x", pady=(8, 10))

        for r in SCOTUS_DATA["landmark_rulings"]:
            rc = PALETTE["rep_light"] if r["leaning"] == "Conservative" else PALETTE["dem_light"]
            imp_color = PALETTE["danger"] if r["impact"] == "Major" else PALETTE["warning"]
            card = ctk.CTkFrame(scroll, fg_color=PALETTE["surface"], corner_radius=10,
                                border_width=1, border_color=PALETTE["border"])
            card.pack(fill="x", pady=(0, 10))
            ctk.CTkFrame(card, width=4, fg_color=rc, corner_radius=0).place(x=0, y=0, relheight=1)
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=16, pady=(12, 4))
            ctk.CTkLabel(top_row, text=r["case"], font=("Georgia", 13, "bold"),
                         text_color=PALETTE["text_primary"], anchor="w").pack(side="left")
            vote_b = ctk.CTkFrame(top_row, fg_color=PALETTE["surface_2"], corner_radius=4)
            vote_b.pack(side="right", padx=(4, 0))
            ctk.CTkLabel(vote_b, text=f"{r['vote']}  {r['impact']}",
                         font=("Courier New", 9, "bold"),
                         text_color=imp_color).pack(padx=8, pady=3)
            ctk.CTkLabel(card, text=r["ruling"], font=("Courier New", 10, "bold"),
                         text_color=rc, anchor="w").pack(fill="x", padx=16, pady=(0, 4))
            ctk.CTkLabel(card, text=r["summary"], font=("Courier New", 10),
                         text_color=PALETTE["text_secondary"], wraplength=840,
                         justify="left", anchor="w").pack(fill="x", padx=16, pady=(0, 12))
if __name__ == "__main__":
  class ExecutiveInsight(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Executive Insight")
        self.geometry("1280x800")
        self.configure(fg_color=PALETTE["bg"])
        self.engine = LegalEngine()
        self._build_ui()
        self._show_panel("Dashboard")

    def _build_ui(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        self.sidebar = Sidebar(body, on_select=self._show_panel)
        self.sidebar.pack(side="left", fill="y")
        self._divider = ctk.CTkFrame(body, width=1, fg_color=PALETTE["border"], corner_radius=0)
        self._divider.pack(side="left", fill="y")
        tr(self._divider, fg_color="border")
        self.content_area = ctk.CTkFrame(body, fg_color=PALETTE["bg"], corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)
        tr(self.content_area, fg_color="bg")
        ca = self.content_area
        en = self.engine
        self._panel_factories = {
            "Dashboard":    lambda: DashboardPanel(ca, en),
            "Legal Q&A":    lambda: LegalQAPanel(ca, en),
            "Bills":        lambda: BillsPanel(ca, en),
            "Party Impact": lambda: PartyImpactPanel(ca),
            "US Wars":      lambda: USWarsPanel(ca),
            "Gov. History": lambda: GovHistoryPanel(ca),
            "Elections":    lambda: ElectionHistoryPanel(ca),
            "Economy":      lambda: EconomyPanel(ca),
            "Congress":     lambda: CongressPanel(ca),
            "Supreme Court":lambda: ScotusPanel(ca),
            "Settings":     lambda: SettingsPanel(ca, on_theme_change=self._apply_theme),
        }
        self._built_panels = {}
        self._current_panel = None
        self.panels = self._built_panels
        dash = self._panel_factories["Dashboard"]()
        self._built_panels["Dashboard"] = dash

    def _apply_theme(self, theme_name):
        if theme_name not in THEMES:
            return
        PALETTE.update(THEMES[theme_name])
        CURRENT_THEME[0] = theme_name
        ctk.set_appearance_mode(PALETTE["ctk_mode"])
        self.configure(fg_color=PALETTE["bg"])
        apply_theme_to_registry()
        self.sidebar.refresh_theme()
        self._show_panel("Settings")

    def _show_panel(self, name):
        if hasattr(self, "_current_panel") and self._current_panel:
            self._current_panel.pack_forget()
        if name not in self._built_panels:
            factory = self._panel_factories.get(name)
            if factory:
                panel = factory()
                panel.place_forget()
                self._built_panels[name] = panel
            else:
                return
        self._current_panel = self._built_panels[name]
        self._current_panel.pack(fill="both", expand=True)
        if hasattr(self, "sidebar"):
            self.sidebar.set_active(name)


if __name__ == "__main__":
    app = ExecutiveInsight()
    app.mainloop()
