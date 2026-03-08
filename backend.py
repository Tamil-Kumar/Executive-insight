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


def build_database():
    conn = sqlite3.connect(DB_PATH)
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
    for fname in CSV_FILES:
        if not os.path.exists(fname):
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

    cur.execute("""
        INSERT INTO orders_fts(rowid, president, title, disposition_notes,
                               executive_order_number, signing_date)
        SELECT id, president, title, disposition_notes,
               executive_order_number, signing_date
        FROM orders
    """)

    conn.commit()
    conn.close()
    return total


class LegalEngine:
    CONTEXT_ROWS = 15

    def __init__(self):
        if not os.path.exists(DB_PATH):
            build_database()

        conn = sqlite3.connect(DB_PATH)
        self.total_records = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        conn.close()

        # Kept for dashboard compatibility
        self.csv_files = CSV_FILES
        self.all_data_content = list(range(self.total_records))

        self.llm = OpenAI(model='gpt-3.5-turbo-instruct', temperature=0)

        template = """You are "Executive Insight", a professional legal research AI specialising in U.S. presidential executive orders and proclamations.

Relevant records from the database:
{context}

Question: {question}

Answer concisely and cite specific orders (title, EO number, date) where relevant.
Answer:"""

        prompt_obj = PromptTemplate.from_template(template)
        self.chain = prompt_obj | self.llm | StrOutputParser()

    def _get_conn(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _rows_to_text(self, rows):
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

    def _fts_search(self, query, limit):
        safe = query.replace('"', '""')
        try:
            conn = self._get_conn()
            rows = conn.execute("""
                SELECT o.* FROM orders o
                JOIN orders_fts f ON o.id = f.rowid
                WHERE orders_fts MATCH ?
                ORDER BY rank LIMIT ?
            """, (f'"{safe}"', limit)).fetchall()
            conn.close()
            return rows
        except Exception:
            return []

    def _like_search(self, query, limit):
        pattern = f"%{query.lower()}%"
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT * FROM orders
            WHERE lower(title)             LIKE ?
               OR lower(president)         LIKE ?
               OR lower(disposition_notes) LIKE ?
            LIMIT ?
        """, (pattern, pattern, pattern, limit)).fetchall()
        conn.close()
        return rows

    def query_ai(self, user_query):
        rows = self._fts_search(user_query, self.CONTEXT_ROWS)
        if not rows:
            rows = self._like_search(user_query, self.CONTEXT_ROWS)
        context = self._rows_to_text(rows) if rows else "No matching records found in the database."
        return self.chain.invoke({"context": context, "question": user_query})

    def search_records(self, query, limit=100):
        if not query.strip():
            return []
        rows = self._fts_search(query, limit) or self._like_search(query, limit)
        return [self._rows_to_text([r]) for r in rows]
