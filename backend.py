"""
Executive Insight — Backend
Powers: bill database + search/filter, activity log, stat counters,
        theme system, jurisdiction/detail settings, Q&A stub.

No external API keys required — everything runs locally.
To swap in real AI responses, replace process_legal_question() with
your preferred LLM call.
"""

import datetime


# ── Themes ────────────────────────────────────────────────────────────────────
THEMES = {
    "Executive Dark": {
        "bg":        "#0D0F14",
        "container": "#13161E",
        "accent":    "#C9A84C",
    },
    "Slate": {
        "bg":        "#0F1117",
        "container": "#181C25",
        "accent":    "#5B8DEF",
    },
    "Ivory": {
        "bg":        "#F5F0E8",
        "container": "#EDE8DF",
        "accent":    "#8B4513",
    },
}


# ── Bill Database ─────────────────────────────────────────────────────────────
BILLS_DB = [
    {
        "number":       "SB 2041",
        "title":        "Digital Privacy Protection Act",
        "status":       "PASSED",
        "jurisdiction": "Federal",
        "summary":      "Establishes federal standards for consumer data privacy, "
                        "requiring explicit opt-in consent for data collection and "
                        "mandating breach notifications within 72 hours.",
        "introduced":   "2025-01-14",
        "last_action":  "2025-11-03",
        "sponsor":      "Sen. Maria Cantwell",
        "tags":         ["privacy", "data", "technology", "consumer"],
    },
    {
        "number":       "HB 1187",
        "title":        "Small Business Tax Relief Amendment",
        "status":       "COMMITTEE",
        "jurisdiction": "California",
        "summary":      "Reduces state income tax burden on small businesses with "
                        "fewer than 50 employees, introducing a tiered rate schedule "
                        "and expanded deduction allowances.",
        "introduced":   "2025-03-22",
        "last_action":  "2025-12-10",
        "sponsor":      "Rep. James Silva",
        "tags":         ["tax", "small business", "economy"],
    },
    {
        "number":       "AB 345",
        "title":        "AI Accountability Framework",
        "status":       "SIGNED",
        "jurisdiction": "Federal",
        "summary":      "Requires federal agencies and large contractors to conduct "
                        "algorithmic impact assessments before deploying AI systems "
                        "that affect individual rights or public services.",
        "introduced":   "2024-09-05",
        "last_action":  "2026-01-18",
        "sponsor":      "Rep. Ted Lieu",
        "tags":         ["AI", "technology", "accountability", "federal"],
    },
    {
        "number":       "SB 089",
        "title":        "Healthcare Data Interoperability Act",
        "status":       "FLOOR",
        "jurisdiction": "New York",
        "summary":      "Mandates that healthcare providers adopt HL7 FHIR standards "
                        "for patient data exchange, enabling patients to access and "
                        "transfer their records across providers seamlessly.",
        "introduced":   "2025-06-01",
        "last_action":  "2026-02-20",
        "sponsor":      "Sen. Gustavo Rivera",
        "tags":         ["healthcare", "data", "interoperability"],
    },
    {
        "number":       "HR 2209",
        "title":        "Cybersecurity Infrastructure Protection Bill",
        "status":       "INTRODUCED",
        "jurisdiction": "Federal",
        "summary":      "Allocates $4.2 billion toward hardening critical infrastructure "
                        "against cyberattacks, with specific provisions for energy grid, "
                        "water systems, and financial networks.",
        "introduced":   "2026-01-07",
        "last_action":  "2026-01-07",
        "sponsor":      "Rep. Mike Gallagher",
        "tags":         ["cybersecurity", "infrastructure", "federal", "technology"],
    },
    {
        "number":       "AB 912",
        "title":        "Consumer Protection Modernisation Act",
        "status":       "HEARING",
        "jurisdiction": "Texas",
        "summary":      "Updates the Texas Deceptive Trade Practices Act to cover "
                        "digital goods and subscription services, with enhanced "
                        "penalties for dark-pattern UI practices.",
        "introduced":   "2025-08-15",
        "last_action":  "2026-02-28",
        "sponsor":      "Rep. Donna Howard",
        "tags":         ["consumer", "trade", "digital", "deceptive practices"],
    },
    {
        "number":       "SB 451",
        "title":        "Gig Worker Classification Reform",
        "status":       "COMMITTEE",
        "jurisdiction": "California",
        "summary":      "Establishes a new dependent contractor classification for "
                        "gig economy workers, granting partial benefits including "
                        "portable health stipends and minimum earnings guarantees.",
        "introduced":   "2025-04-30",
        "last_action":  "2025-11-19",
        "sponsor":      "Sen. Maria Elena Durazo",
        "tags":         ["labor", "gig economy", "worker classification"],
    },
    {
        "number":       "HB 778",
        "title":        "Environmental Justice Remediation Act",
        "status":       "PASSED",
        "jurisdiction": "Federal",
        "summary":      "Creates a $10 billion remediation fund for communities "
                        "disproportionately affected by industrial pollution, with "
                        "priority scoring based on health outcome data.",
        "introduced":   "2024-11-12",
        "last_action":  "2025-10-30",
        "sponsor":      "Rep. Alexandria Ocasio-Cortez",
        "tags":         ["environment", "justice", "pollution", "federal"],
    },
    {
        "number":       "SB 3301",
        "title":        "Broadband Rural Access Expansion",
        "status":       "SIGNED",
        "jurisdiction": "Federal",
        "summary":      "Extends high-speed internet infrastructure grants to rural "
                        "communities currently lacking broadband access, targeting "
                        "95% national coverage by 2028.",
        "introduced":   "2024-07-22",
        "last_action":  "2025-04-01",
        "sponsor":      "Sen. John Thune",
        "tags":         ["broadband", "rural", "infrastructure", "technology"],
    },
    {
        "number":       "AB 1102",
        "title":        "Tenant Anti-Displacement Protection Act",
        "status":       "FLOOR",
        "jurisdiction": "New York",
        "summary":      "Caps annual rent increases at 3% or CPI (whichever is lower) "
                        "for all residential leases, and restricts evictions to "
                        "enumerated just-cause grounds.",
        "introduced":   "2025-09-10",
        "last_action":  "2026-03-01",
        "sponsor":      "Sen. Julia Salazar",
        "tags":         ["housing", "tenant rights", "rent control"],
    },
    {
        "number":       "HR 5540",
        "title":        "Firearm Background Check Modernisation",
        "status":       "COMMITTEE",
        "jurisdiction": "Federal",
        "summary":      "Closes the private-sale loophole by requiring background "
                        "checks for all firearm transfers, including gun shows and "
                        "online marketplaces.",
        "introduced":   "2025-02-14",
        "last_action":  "2025-07-08",
        "sponsor":      "Rep. Mike Thompson",
        "tags":         ["firearms", "background checks", "public safety"],
    },
    {
        "number":       "SB 670",
        "title":        "Student Loan Interest Relief Act",
        "status":       "INTRODUCED",
        "jurisdiction": "Federal",
        "summary":      "Caps federal student loan interest rates at 4% and provides "
                        "retroactive interest cancellation for borrowers who have been "
                        "in repayment for over 10 years.",
        "introduced":   "2026-02-03",
        "last_action":  "2026-02-03",
        "sponsor":      "Sen. Bernie Sanders",
        "tags":         ["education", "student loans", "finance"],
    },
]

# Status display ordering (lower = more progressed)
STATUS_ORDER = {
    "SIGNED":     0,
    "PASSED":     1,
    "FLOOR":      2,
    "HEARING":    3,
    "COMMITTEE":  4,
    "INTRODUCED": 5,
}

ALL_JURISDICTIONS = sorted({b["jurisdiction"] for b in BILLS_DB})
ALL_STATUSES      = list(STATUS_ORDER.keys())


# ── Activity Log ──────────────────────────────────────────────────────────────
class ActivityLog:
    """Simple in-memory timestamped activity feed."""

    def __init__(self):
        now = datetime.datetime.now
        self._entries = [
            {"type": "bill",  "desc": "AB 345 signed into law",               "ts": now() - datetime.timedelta(minutes=120)},
            {"type": "bill",  "desc": "SB 2041 status updated to PASSED",     "ts": now() - datetime.timedelta(minutes=90)},
            {"type": "query", "desc": "GDPR compliance analysis requested",   "ts": now() - datetime.timedelta(minutes=60)},
            {"type": "bill",  "desc": "HB 1187 moved to committee",           "ts": now() - datetime.timedelta(minutes=30)},
            {"type": "query", "desc": "Contract termination clause reviewed", "ts": now() - datetime.timedelta(minutes=10)},
        ]

    def add(self, entry_type: str, description: str):
        self._entries.append({
            "type": entry_type,
            "desc": description,
            "ts":   datetime.datetime.now(),
        })

    def recent(self, n: int = 20):
        """Return up to n most recent entries, newest first."""
        return list(reversed(self._entries[-n:]))

    @staticmethod
    def human_time(ts: datetime.datetime) -> str:
        delta = datetime.datetime.now() - ts
        secs  = int(delta.total_seconds())
        if secs < 60:
            return "Just now"
        if secs < 3600:
            m = secs // 60
            return f"{m} min ago"
        if secs < 86400:
            h = secs // 3600
            return f"{h} hr ago"
        d = secs // 86400
        return f"{d} day{'s' if d > 1 else ''} ago"


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN BACKEND CLASS
# ══════════════════════════════════════════════════════════════════════════════
class ExecutiveInsightBackend:

    def __init__(self):
        self.current_theme        = "Executive Dark"
        self.response_detail      = "Standard"
        self.default_jurisdiction = "Federal (US)"
        self.activity_log         = ActivityLog()
        self._query_count         = 0

        # The UI can register a callable here; it will be called after any
        # new activity entry so the dashboard feed can refresh itself.
        self._on_activity_update = None

    # ── Settings ──────────────────────────────────────────────────────────────
    def get_theme_names(self):
        return list(THEMES.keys())

    def get_theme(self, name: str) -> dict:
        return THEMES.get(name, THEMES["Executive Dark"])

    def set_theme(self, name: str):
        if name in THEMES:
            self.current_theme = name

    def set_response_detail(self, level: str):
        """level: 'Concise' | 'Standard' | 'Detailed' | 'Comprehensive'"""
        self.response_detail = level

    def set_default_jurisdiction(self, jurisdiction: str):
        self.default_jurisdiction = jurisdiction

    # ── Stats ─────────────────────────────────────────────────────────────────
    def get_stats(self) -> dict:
        """Live figures shown on the dashboard stat cards."""
        active = sum(
            1 for b in BILLS_DB
            if b["status"] not in ("SIGNED", "PASSED")
        )
        return {
            "active_bills":  str(active),
            "legal_queries": str(self._query_count),
            "jurisdictions": str(len(ALL_JURISDICTIONS)),
        }

    # ── Activity ──────────────────────────────────────────────────────────────
    def register_activity_callback(self, fn):
        """
        Register a zero-argument callable that the UI wants called
        whenever the activity log gains a new entry.
        """
        self._on_activity_update = fn

    def _push_activity(self, entry_type: str, description: str):
        self.activity_log.add(entry_type, description)
        if self._on_activity_update:
            self._on_activity_update()

    def get_recent_activity(self, n: int = 20) -> list:
        """
        Returns a list of dicts, newest first:
          {"type": "bill"|"query",  "desc": str,  "time_str": str}
        """
        return [
            {
                "type":     e["type"],
                "desc":     e["desc"],
                "time_str": ActivityLog.human_time(e["ts"]),
            }
            for e in self.activity_log.recent(n)
        ]

    # ── Bill search & filter ──────────────────────────────────────────────────
    def search_bills(
        self,
        query:        str = "",
        jurisdiction: str = "All",
        status:       str = "All",
        sort_by:      str = "status",   # "status" | "date" | "number"
    ) -> list:
        """
        Keyword search across number, title, summary, sponsor, and tags.
        All words in the query must appear (AND logic).
        Returns filtered, sorted list of bill dicts.
        """
        q = query.strip().lower()
        results = []

        for bill in BILLS_DB:
            if jurisdiction != "All" and bill["jurisdiction"] != jurisdiction:
                continue
            if status != "All" and bill["status"] != status:
                continue
            if q:
                searchable = " ".join([
                    bill["number"].lower(),
                    bill["title"].lower(),
                    bill["summary"].lower(),
                    bill["sponsor"].lower(),
                    " ".join(bill["tags"]),
                ])
                if not all(word in searchable for word in q.split()):
                    continue
            results.append(bill)

        if sort_by == "status":
            results.sort(key=lambda b: STATUS_ORDER.get(b["status"], 99))
        elif sort_by == "date":
            results.sort(key=lambda b: b["last_action"], reverse=True)
        elif sort_by == "number":
            results.sort(key=lambda b: b["number"])

        return results

    def get_all_jurisdictions(self) -> list:
        return ["All"] + ALL_JURISDICTIONS

    def get_all_statuses(self) -> list:
        return ["All"] + ALL_STATUSES

    def get_bill_detail(self, bill_number: str) -> dict | None:
        for b in BILLS_DB:
            if b["number"] == bill_number:
                return b
        return None

    # ── Legal Q&A ─────────────────────────────────────────────────────────────
    def process_legal_question(self, question: str) -> str:
        """
        Stub response. Replace this method body with your LLM call to get
        real answers. The response_detail and default_jurisdiction settings
        are available as self.response_detail and self.default_jurisdiction.
        """
        if not question.strip():
            return "Please enter a question."

        self._query_count += 1
        short_q = question[:60] + ("…" if len(question) > 60 else "")
        self._push_activity("query", f"Legal query: \"{short_q}\"")

        detail_note = {
            "Concise":       "one short paragraph",
            "Standard":      "a clear, structured answer",
            "Detailed":      "a detailed breakdown with cited principles",
            "Comprehensive": "a comprehensive legal memorandum-style response",
        }.get(self.response_detail, "a clear answer")

        return (
            f"[STUB — connect your LLM to get real answers]\n\n"
            f"Question: \"{question}\"\n\n"
            f"Active settings:\n"
            f"  Jurisdiction : {self.default_jurisdiction}\n"
            f"  Detail level : {self.response_detail} ({detail_note})\n\n"
            f"Replace ExecutiveInsightBackend.process_legal_question() in\n"
            f"backend.py with your preferred LLM API call.\n\n"
            f"This query (#{self._query_count}) has been logged to the activity feed."
        )
