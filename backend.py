import os
import csv
import sqlite3
from dotenv import load_dotenv
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

DB_PATH = "executive_orders.db"

CSV_FILES = [
    'trump_eos.csv', 'biden.csv', 'carter.csv', 'clinton.csv', 'eisenhower.csv',
    'ford.csv', 'h_w_bush.csv', 'johnson.csv', 'kennedy.csv', 'nixon.csv',
    'obama.csv', 'past.csv', 'reagan.csv', 'roosevelt.csv', 'truman.csv',
    'trump2.csv', 'w_bush.csv'
]

# Map filename → president name for the 'president' column
PRESIDENT_MAP = {
    'trump_eos.csv': 'Trump (1st Term)',
    'trump2.csv':    'Trump (2nd Term)',
    'biden.csv':     'Biden',
    'carter.csv':    'Carter',
    'clinton.csv':   'Clinton',
    'eisenhower.csv':'Eisenhower',
    'ford.csv':      'Ford',
    'h_w_bush.csv':  'H.W. Bush',
    'johnson.csv':   'Johnson',
    'kennedy.csv':   'Kennedy',
    'nixon.csv':     'Nixon',
    'obama.csv':     'Obama',
    'past.csv':      'Historical',
    'reagan.csv':    'Reagan',
    'roosevelt.csv': 'Roosevelt',
    'truman.csv':    'Truman',
    'w_bush.csv':    'W. Bush',
}


def build_database(db_path: str = DB_PATH, csv_files: list = CSV_FILES) -> int:
    """
    Creates (or re-creates) the SQLite database from all CSV files.
    Returns the total number of rows inserted.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS orders")
    cur.execute("""
        CREATE TABLE orders (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            president               TEXT,
            citation                TEXT,
            document_number         TEXT,
            html_url                TEXT,
            pdf_url                 TEXT,
            type                    TEXT,
            subtype                 TEXT,
            publication_date        TEXT,
            signing_date            TEXT,
            title                   TEXT,
            disposition_notes       TEXT,
            executive_order_number  TEXT
        )
    """)

    # Full-text search virtual table — allows fast MATCH queries
    cur.execute("DROP TABLE IF EXISTS orders_fts")
    cur.execute("""
        CREATE VIRTUAL TABLE orders_fts USING fts5(
            president,
            title,
            disposition_notes,
            executive_order_number,
            signing_date,
            content='orders',
            content_rowid='id'
        )
    """)

    total = 0
    for fname in csv_files:
        if not os.path.exists(fname):
            print(f"[WARN] {fname} not found — skipping.")
            continue
        president = PRESIDENT_MAP.get(fname, fname)
        with open(fname, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = []
            for row in reader:
                rows.append((
                    president,
                    row.get('citation', ''),
                    row.get('document_number', ''),
                    row.get('html_url', ''),
                    row.get('pdf_url', ''),
                    row.get('type', ''),
                    row.get('subtype', ''),
                    row.get('publication_date', ''),
                    row.get('signing_date', ''),
                    row.get('title', ''),
                    row.get('disposition_notes', ''),
                    row.get('executive_order_number', ''),
                ))
            cur.executemany("""
                INSERT INTO orders
                    (president, citation, document_number, html_url, pdf_url,
                     type, subtype, publication_date, signing_date, title,
                     disposition_notes, executive_order_number)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, rows)
            total += len(rows)
            print(f"  Loaded {len(rows):>4} rows from {fname}")

    # Populate FTS index
    cur.execute("""
        INSERT INTO orders_fts(rowid, president, title, disposition_notes,
                               executive_order_number, signing_date)
        SELECT id, president, title, disposition_notes,
               executive_order_number, signing_date
        FROM orders
    """)

    conn.commit()
    conn.close()
    print(f"[DB] Database built — {total} total rows.")
    return total


class LegalEngine:
    # How many matching rows to pass as context to the LLM.
    # Keep this small to stay well under the token limit.
    CONTEXT_ROWS = 15

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.csv_files = CSV_FILES

        # Build DB if it doesn't exist yet
        if not os.path.exists(db_path):
            print("[DB] Building database for the first time…")
            build_database(db_path, CSV_FILES)

        self.total_records = self._count_records()
        print(f"[DB] Ready — {self.total_records} records in database.")

        self.llm = OpenAI(model='gpt-3.5-turbo-instruct', temperature=0)

        template = """
You are "Executive Insight", a professional legal research AI specialising in
U.S. presidential executive orders and proclamations.

Relevant records from the database:
{context}

Question: {question}

Answer concisely and cite specific orders (title, EO number, date) where relevant."""

        prompt_obj = PromptTemplate.from_template(template)
        self.chain = prompt_obj | self.llm | StrOutputParser()

    # ── Database helpers ───────────────────────────────────────────────────────

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _count_records(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

    def _rows_to_text(self, rows) -> str:
        """Convert SQLite rows into a compact text block for the LLM context."""
        lines = []
        for r in rows:
            parts = [f"[{r['president']}]", r['title'] or '(no title)']
            if r['executive_order_number']:
                parts.append(f"EO #{r['executive_order_number']}")
            if r['signing_date']:
                parts.append(f"Signed: {r['signing_date']}")
            if r['disposition_notes']:
                parts.append(f"Notes: {r['disposition_notes']}")
            lines.append(" | ".join(parts))
        return "\n".join(lines)

    # ── Public API ─────────────────────────────────────────────────────────────

    def search_records(self, query: str, limit: int = 100):
        """
        Returns matching records as plain-text strings (for the Bills panel).
        Uses FTS5 when possible, falls back to LIKE search.
        """
        if not query.strip():
            return []
        rows = self._fts_search(query, limit) or self._like_search(query, limit)
        return [self._rows_to_text([r]) for r in rows]

    def query_ai(self, user_query: str) -> str:
        """
        Retrieves the most relevant DB rows for the query, builds a compact
        context string, and calls the LLM — keeping well under the token limit.
        """
        rows = self._fts_search(user_query, self.CONTEXT_ROWS)
        if not rows:
            rows = self._like_search(user_query, self.CONTEXT_ROWS)

        if rows:
            context = self._rows_to_text(rows)
        else:
            context = "No closely matching records found in the database."

        return self.chain.invoke({"context": context, "question": user_query})

    # ── Internal search methods ────────────────────────────────────────────────

    def _fts_search(self, query: str, limit: int):
        """Full-text search via FTS5 (fast, ranked by relevance)."""
        # Sanitise query for FTS5: wrap multi-word phrases, escape quotes
        safe = query.replace('"', '""')
        fts_query = f'"{safe}"'
        try:
            with self._connect() as conn:
                rows = conn.execute("""
                    SELECT o.*
                    FROM orders o
                    JOIN orders_fts f ON o.id = f.rowid
                    WHERE orders_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (fts_query, limit)).fetchall()
            return rows
        except sqlite3.OperationalError:
            return []

    def _like_search(self, query: str, limit: int):
        """Fallback LIKE search across title, president, and notes columns."""
        pattern = f"%{query.lower()}%"
        with self._connect() as conn:
            return conn.execute("""
                SELECT * FROM orders
                WHERE lower(title)             LIKE ?
                   OR lower(president)         LIKE ?
                   OR lower(disposition_notes) LIKE ?
                LIMIT ?
            """, (pattern, pattern, pattern, limit)).fetchall()


# ── CLI helper: rebuild the database on demand ─────────────────────────────────
if __name__ == "__main__":
    import sys
    if "--rebuild" in sys.argv:
        build_database()
    else:
        engine = LegalEngine()
        print(f"Loaded {engine.total_records} records.")
        result = engine.query_ai("What executive orders did Reagan sign about taxes?")
        print(result)
