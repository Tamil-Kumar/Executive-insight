"""
Executive Insight — backend
===========================

What changed
------------
1. Provider switch: OpenAI *or* OpenRouter. The key is typed into the app
   (Settings tab) and stored in ei_settings.json — no .env editing needed.
   Env vars (OPENAI_API_KEY / OPENROUTER_API_KEY) still work as a fallback.
2. Resilient CSV loading. Files are looked up across several folders, matched
   case-insensitively, opened with newline="" + utf-8-sig, and every file gets
   a load report saying exactly what happened. That report is what tells you
   why past.csv or kennedy.csv didn't load.
3. A real search index over every record (the old build fed the model only the
   first 20 rows of the corpus).
4. AI enrichment: fills in missing fields on records — deterministic fills for
   citations/URLs, model-generated summary/topics/impact for the rest. Cached
   to disk so a record is only paid for once.

No new dependencies. Networking uses urllib from the stdlib, so this runs with
or without langchain / openai / requests installed.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Cells in these files contain long multi-line disposition notes.
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:                                   # 32-bit Python guard
    csv.field_size_limit(2 ** 31 - 1)

APP_DIR       = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(APP_DIR, "ei_settings.json")
INDEX_PATH    = os.path.join(APP_DIR, "ei_index.json")
ENRICH_PATH   = os.path.join(APP_DIR, "ei_enriched.json")


# ── Settings ──────────────────────────────────────────────────────────────────

DEFAULT_SETTINGS = {
    "appearance":        "Dark",
    "font_size":         "Medium",
    "results_limit":     200,
    "window_size":       "Fullscreen",
    "data_folder":       "",

    "ai_provider":       "openrouter",          # "openai" | "openrouter"
    "openai_key":        "",
    "openai_model":      "gpt-4o-mini",
    "openrouter_key":    "",
    "openrouter_model":  "openai/gpt-4o-mini",

    "ai_model":          "gpt-3.5-turbo-instruct",   # legacy key, kept for compat
    "openrouter_site":   "https://executive-insight.local",
    "openrouter_title":  "Executive Insight",
}

PROVIDERS = {
    "openai": {
        "label":       "OpenAI",
        "base_url":    "https://api.openai.com/v1",
        "key_field":   "openai_key",
        "model_field": "openai_model",
        "env":         "OPENAI_API_KEY",
        "key_prefix":  "sk-",
        "console":     "https://platform.openai.com/api-keys",
    },
    "openrouter": {
        "label":       "OpenRouter",
        "base_url":    "https://openrouter.ai/api/v1",
        "key_field":   "openrouter_key",
        "model_field": "openrouter_model",
        "env":         "OPENROUTER_API_KEY",
        "key_prefix":  "sk-or-",
        "console":     "https://openrouter.ai/keys",
    },
}

# Shortlist for the dropdown; any model id can still be typed in.
OPENROUTER_MODELS = [
    "openai/gpt-4o-mini",
    "openai/gpt-4o",
    "anthropic/claude-3.5-haiku",
    "anthropic/claude-sonnet-4",
    "google/gemini-2.0-flash-001",
    "meta-llama/llama-3.3-70b-instruct",
    "deepseek/deepseek-chat",
    "mistralai/mistral-small-3.1-24b-instruct",
]

OPENAI_MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4.1-mini",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-instruct",
]


def load_settings() -> dict:
    data = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data.update(json.load(f) or {})
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[settings] could not read {SETTINGS_PATH}: {e}")
    # Migrate an OpenRouter key that was pasted into the old openai_key field.
    if str(data.get("openai_key", "")).startswith("sk-or-") and not data.get("openrouter_key"):
        data["openrouter_key"] = data["openai_key"]
        data["openai_key"] = ""
        data["ai_provider"] = "openrouter"
    return data


def save_settings(updates: dict) -> bool:
    try:
        merged = load_settings()
        merged.update(updates)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
        return True
    except Exception as e:
        print(f"[settings] could not write {SETTINGS_PATH}: {e}")
        return False


def _load_env_files() -> None:
    """Read .env / _env sitting next to this file into os.environ (no deps)."""
    for name in (".env", "_env", "env"):
        path = os.path.join(APP_DIR, name)
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(),
                                          v.strip().strip('"').strip("'"))
        except Exception:
            pass


_load_env_files()


# ── Resilient CSV loading ─────────────────────────────────────────────────────

def candidate_dirs(data_folder: str = "") -> list:
    dirs = []
    for d in (data_folder,
              APP_DIR,
              os.path.join(APP_DIR, "data"),
              os.path.join(APP_DIR, "csv"),
              os.path.join(APP_DIR, "databases"),
              os.getcwd(),
              "/mnt/user-data/uploads",
              "/mnt/user-data/outputs"):
        if d and os.path.isdir(d) and d not in dirs:
            dirs.append(d)
    return dirs


def resolve_data_path(filename: str, data_folder: str = ""):
    """Return (path_or_None, dirs_searched). Case-insensitive on every OS."""
    tried = candidate_dirs(data_folder)
    target = filename.lower()
    for folder in tried:
        direct = os.path.join(folder, filename)
        if os.path.exists(direct):
            return direct, tried
        try:
            for entry in os.listdir(folder):
                if entry.lower() == target:
                    return os.path.join(folder, entry), tried
        except OSError:
            continue
    return None, tried


def load_csv_resilient(filename: str, data_folder: str = ""):
    """
    Load one CSV and always come back with an explanation.

    Returns (rows, report) where report is
        {"file", "path", "rows", "ok", "error", "tried"}
    """
    report = {"file": filename, "path": None, "rows": 0,
              "ok": False, "error": "", "tried": []}

    path, tried = resolve_data_path(filename, data_folder)
    report["tried"] = tried
    if not path:
        report["error"] = "Not found in: " + " | ".join(tried)
        return [], report

    report["path"] = path
    try:
        if os.path.getsize(path) == 0:
            report["error"] = "File is empty (0 bytes)."
            return [], report
    except OSError as e:
        report["error"] = f"{type(e).__name__}: {e}"
        return [], report

    last_error = ""
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            # newline="" matters: these files have newlines inside quoted
            # disposition_notes fields.
            with open(path, newline="", encoding=encoding, errors="strict") as f:
                rows = list(csv.DictReader(f))
            clean = []
            for row in rows:
                clean.append({(k or "").strip(): (v if isinstance(v, str) else "")
                              for k, v in row.items()})
            report.update(rows=len(clean), ok=True, error="")
            if not clean:
                report["error"] = "Parsed cleanly but has no data rows."
            return clean, report
        except UnicodeDecodeError as e:
            last_error = f"{encoding}: {e}"
            continue
        except PermissionError:
            report["error"] = ("Permission denied — the file is probably open "
                               "in Excel. Close it and rescan.")
            return [], report
        except Exception as e:
            report["error"] = f"{type(e).__name__}: {e}"
            return [], report

    # Last resort: never lose a whole file to one bad byte.
    try:
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            rows = list(csv.DictReader(f))
        report.update(rows=len(rows), ok=True,
                      error=f"Recovered with replaced characters ({last_error})")
        return rows, report
    except Exception as e:
        report["error"] = f"{type(e).__name__}: {e}"
        return [], report


PRESIDENT_SOURCES = {
    "Trump 2nd Term": "trump2.csv",
    "Trump 1st Term": "trump_eos.csv",
    "Biden":          "biden.csv",
    "Obama":          "obama.csv",
    "W. Bush":        "w_bush.csv",
    "Clinton":        "clinton.csv",
    "H.W. Bush":      "h_w_bush.csv",
    "Reagan":         "reagan.csv",
    "Carter":         "carter.csv",
    "Ford":           "ford.csv",
    "Nixon":          "nixon.csv",
    "Johnson":        "johnson.csv",
    "Kennedy":        "kennedy.csv",
    "Eisenhower":     "eisenhower.csv",
    "Truman":         "truman.csv",
    "Roosevelt":      "roosevelt.csv",
    "Historical":     "past.csv",
}


# ── LLM client (OpenAI + OpenRouter behind one interface) ─────────────────────

class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, settings=None):
        self.reload(settings)

    # -- configuration -------------------------------------------------------
    def reload(self, settings=None):
        self.settings = settings if settings is not None else load_settings()
        name = str(self.settings.get("ai_provider", "openrouter")).lower()
        self.provider = name if name in PROVIDERS else "openrouter"
        self.spec = PROVIDERS[self.provider]
        self.base_url = self.spec["base_url"]

    @property
    def api_key(self) -> str:
        key = str(self.settings.get(self.spec["key_field"], "") or "").strip()
        return key or os.environ.get(self.spec["env"], "").strip()

    @property
    def model(self) -> str:
        m = str(self.settings.get(self.spec["model_field"], "") or "").strip()
        return m or DEFAULT_SETTINGS[self.spec["model_field"]]

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def key_hint(self) -> str:
        k = self.api_key
        if not k:
            return "not set"
        return f"{k[:7]}\u2026{k[-4:]}  ({len(k)} chars)"

    # -- transport -----------------------------------------------------------
    def _headers(self) -> dict:
        h = {"Authorization": f"Bearer {self.api_key}",
             "Content-Type": "application/json"}
        if self.provider == "openrouter":
            h["HTTP-Referer"] = str(self.settings.get("openrouter_site", ""))
            h["X-Title"] = str(self.settings.get("openrouter_title",
                                                 "Executive Insight"))
        return h

    def _post(self, endpoint: str, payload: dict, timeout: int = 90) -> dict:
        if not self.api_key:
            raise LLMError(
                f"No {self.spec['label']} API key set. Open Settings \u2192 "
                f"AI provider, paste your key, then press Save & test.")
        req = urllib.request.Request(
            self.base_url + endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")
                body = json.loads(body).get("error", {}).get("message", body)
            except Exception:
                pass
            if e.code == 401:
                raise LLMError(f"401 — {self.spec['label']} rejected the key. "
                               f"Check it at {self.spec['console']}.") from None
            if e.code == 402:
                raise LLMError("402 — this account is out of credits.") from None
            if e.code == 404:
                raise LLMError(f"404 — model '{self.model}' isn't available on "
                               f"{self.spec['label']}.") from None
            if e.code == 429:
                raise LLMError("429 — rate limited. Wait a moment and retry.") from None
            raise LLMError(f"HTTP {e.code} — {str(body)[:400]}") from None
        except urllib.error.URLError as e:
            raise LLMError(f"Network error — {e.reason}") from None

    def get_models(self, timeout: int = 20) -> list:
        """Live model list (OpenRouter). Falls back to the shortlist."""
        if self.provider != "openrouter":
            return list(OPENAI_MODELS)
        try:
            req = urllib.request.Request(self.base_url + "/models",
                                         headers=self._headers())
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            ids = sorted({m.get("id", "") for m in data.get("data", []) if m.get("id")})
            return ids or list(OPENROUTER_MODELS)
        except Exception:
            return list(OPENROUTER_MODELS)

    # -- generation ----------------------------------------------------------
    def complete(self, system: str, user: str,
                 max_tokens: int = 800, temperature: float = 0.0) -> str:
        model = self.model
        # Legacy OpenAI instruct models use /completions, not /chat/completions.
        if self.provider == "openai" and model.endswith("-instruct"):
            data = self._post("/completions", {
                "model": model,
                "prompt": f"{system}\n\n{user}\n\nAnswer:",
                "max_tokens": max_tokens,
                "temperature": temperature,
            })
            return (data["choices"][0].get("text") or "").strip()

        data = self._post("/chat/completions", {
            "model": model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        })
        choice = data["choices"][0]
        msg = choice.get("message") or {}
        return (msg.get("content") or choice.get("text") or "").strip()

    def test(self):
        """Return (ok: bool, message: str)."""
        if not self.api_key:
            return False, f"No {self.spec['label']} key set."
        try:
            t0 = time.time()
            out = self.complete("Reply with the single word OK.", "ping",
                                max_tokens=8, temperature=0)
            ms = int((time.time() - t0) * 1000)
            return True, (f"Connected to {self.spec['label']} \u00b7 {self.model} "
                          f"\u00b7 {ms} ms \u00b7 replied \"{out[:20]}\"")
        except LLMError as e:
            return False, str(e)
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"


# ── Search index ──────────────────────────────────────────────────────────────

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP = {"the", "of", "and", "to", "for", "in", "on", "a", "an", "by", "with",
         "or", "as", "at", "is", "be", "from", "that", "this", "it"}


def _tokens(text: str) -> set:
    return {t for t in _TOKEN_RE.findall(text.lower())
            if len(t) > 1 and t not in _STOP}


# ── Engine ────────────────────────────────────────────────────────────────────

class LegalEngine:
    def __init__(self, settings=None):
        self.settings = settings if settings is not None else load_settings()
        self.llm = LLMClient(self.settings)

        self.sources = dict(PRESIDENT_SOURCES)
        self.csv_files = list(PRESIDENT_SOURCES.values())

        self.records = []            # dicts, each carrying _source/_president/_id
        self.all_data_content = []   # "col: val" strings (frontend compatibility)
        self.load_report = []        # per-file diagnostics
        self.index = {}              # token -> [record ids]
        self.enriched = load_json(ENRICH_PATH, {})

        self.reload_data()

    # -- data ----------------------------------------------------------------
    def reload_data(self):
        self.records, self.all_data_content, self.load_report = [], [], []
        folder = str(self.settings.get("data_folder", "") or "")

        for president, filename in self.sources.items():
            rows, report = load_csv_resilient(filename, folder)
            report["president"] = president
            self.load_report.append(report)
            for row in rows:
                row = dict(row)
                row["_source"] = filename
                row["_president"] = president
                row["_id"] = len(self.records)
                self.records.append(row)
                self.all_data_content.append(self._format(row))
        self.build_index()
        return self.load_report

    def loaded_sources(self) -> list:
        return [r for r in self.load_report if r["ok"] and r["rows"]]

    def missing_sources(self) -> list:
        return [r for r in self.load_report if not (r["ok"] and r["rows"])]

    def report_text(self) -> str:
        lines = []
        for r in sorted(self.load_report, key=lambda x: x["president"]):
            if r["ok"] and r["rows"]:
                lines.append(f"OK    {r['president']:<16} {r['rows']:>6,} rows   {r['path']}")
            else:
                lines.append(f"FAIL  {r['president']:<16} {r['file']} — {r['error']}")
        return "\n".join(lines)

    # -- index ---------------------------------------------------------------
    def build_index(self, progress_cb=None) -> dict:
        index = {}
        total = len(self.records) or 1
        for i, row in enumerate(self.records):
            blob = " ".join(str(row.get(k, "")) for k in
                            ("title", "disposition_notes", "executive_order_number",
                             "citation", "subtype", "_president"))
            for tok in _tokens(blob):
                index.setdefault(tok, []).append(i)
            if progress_cb and i % 500 == 0:
                progress_cb(i / total, f"Indexing {i:,} of {total:,} records")
        self.index = index
        if progress_cb:
            progress_cb(1.0, f"Indexed {len(self.records):,} records \u00b7 "
                             f"{len(index):,} terms")
        return index

    def save_index(self) -> str:
        write_json(INDEX_PATH, {
            "built": time.time(),
            "records": len(self.records),
            "terms": len(self.index),
            "sources": {r["president"]: r["rows"] for r in self.load_report},
        })
        return INDEX_PATH

    def search(self, query: str, limit: int = 100) -> list:
        """Ranked record search over the inverted index."""
        toks = _tokens(query or "")
        if not toks:
            return self.records[:limit]
        scores = {}
        for tok in toks:
            for rid in self.index.get(tok, ()):
                scores[rid] = scores.get(rid, 0) + 1
        if not scores:                                    # substring fallback
            q = (query or "").lower()
            return [r for r in self.records
                    if q in str(r.get("title", "")).lower()][:limit]
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])[:limit]
        return [self.records[rid] for rid, _ in ranked]

    def search_records(self, query: str, limit: int = 100) -> list:
        """Frontend compatibility: returns formatted strings."""
        return [self._format(r) for r in self.search(query, limit)]

    @staticmethod
    def _format(row: dict) -> str:
        return "\n".join(f"{k}: {v}" for k, v in row.items()
                         if v and not str(k).startswith("_"))

    # -- AI ------------------------------------------------------------------
    def query_ai(self, user_query: str, k: int = 12) -> str:
        hits = self.search(user_query, limit=k)
        context = ("\n\n---\n\n".join(self._format(r) for r in hits)
                   if hits else "No matching records in the loaded databases.")
        system = (
            "You are Executive Insight, a legal research assistant covering "
            "U.S. presidential executive orders, proclamations and memoranda. "
            "Answer only from the supplied records. Give the executive order "
            "number and signing date for every claim. If the records don't "
            "answer the question, say so plainly."
        )
        return self.llm.complete(system,
                                 f"Records:\n{context}\n\nQuestion: {user_query}",
                                 max_tokens=900, temperature=0)

    # -- enrichment ----------------------------------------------------------
    @staticmethod
    def _enrich_key(row: dict) -> str:
        return (f"{row.get('_source','')}|"
                f"{row.get('executive_order_number','')}|"
                f"{str(row.get('title',''))[:60]}")

    @staticmethod
    def _derive_links(row: dict) -> dict:
        """Deterministic fills — no model involved, so nothing gets invented."""
        out = {}
        doc = str(row.get("document_number", "")).strip()
        pub = str(row.get("publication_date", "")).strip()
        if doc and pub and not str(row.get("pdf_url", "")).strip():
            m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", pub)
            if m:
                mm, dd, yyyy = m.groups()
                out["pdf_url"] = (f"https://www.govinfo.gov/content/pkg/"
                                  f"FR-{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}"
                                  f"/pdf/{doc}.pdf")
        if doc and not str(row.get("html_url", "")).strip():
            out["html_url"] = f"https://www.federalregister.gov/d/{doc}"
        if not doc and not str(row.get("html_url", "")).strip():
            term = str(row.get("citation") or row.get("title") or "").strip()
            if term:
                out["html_url"] = (
                    "https://www.federalregister.gov/documents/search"
                    "?conditions%5Bterm%5D=" + urllib.parse.quote(term))
        return out

    def enrich(self, rows=None, batch_size: int = 8, limit: int = 200,
               progress_cb=None, stop_flag=None) -> dict:
        """
        Fill in missing information for records using the configured API key.
        Link fills are deterministic and free; summary / topics / impact come
        from the model. Everything is cached in ei_enriched.json so a record is
        never paid for twice.
        """
        rows = self.records if rows is None else rows
        todo = []
        for row in rows:
            if self._enrich_key(row) in self.enriched:
                continue
            todo.append(row)
            if len(todo) >= limit:
                break

        done, total = 0, max(len(todo), 1)
        for start in range(0, len(todo), batch_size):
            if stop_flag is not None and stop_flag.is_set():
                break
            batch = todo[start:start + batch_size]
            listing = "\n\n".join(
                f"[{i}] EO {r.get('executive_order_number') or '—'} \u00b7 "
                f"{r.get('_president')} \u00b7 signed "
                f"{r.get('signing_date') or r.get('publication_date') or '—'}\n"
                f"Title: {r.get('title','')}\n"
                f"Notes: {str(r.get('disposition_notes',''))[:300]}"
                for i, r in enumerate(batch)
            )
            system = ("You summarise U.S. executive actions for a research "
                      "database. Reply with a JSON array only — no prose, no "
                      "markdown fences. One object per input item: "
                      '{"i": <index>, "summary": "<=40 words, plain English", '
                      '"topics": ["up to 4 short tags"], '
                      '"impact": "High|Medium|Low", '
                      '"agencies": ["agencies named or affected"]}. '
                      "Use only the title and notes given. Empty list if unknown.")
            try:
                parsed = _parse_json_array(
                    self.llm.complete(system, listing, max_tokens=1200, temperature=0))
            except Exception as e:
                if progress_cb:
                    progress_cb(done / total, f"Stopped: {e}")
                break

            by_index = {int(o.get("i", -1)): o for o in parsed if isinstance(o, dict)}
            for i, row in enumerate(batch):
                info = dict(self._derive_links(row))
                ai = by_index.get(i, {})
                if ai:
                    info["ai_summary"] = str(ai.get("summary", ""))[:400]
                    info["ai_topics"] = ai.get("topics", [])
                    info["ai_impact"] = ai.get("impact", "")
                    info["ai_agencies"] = ai.get("agencies", [])
                self.enriched[self._enrich_key(row)] = info
                done += 1

            write_json(ENRICH_PATH, self.enriched)
            if progress_cb:
                progress_cb(done / total,
                            f"Enriched {done:,} of {len(todo):,} records")

        write_json(ENRICH_PATH, self.enriched)
        if progress_cb:
            progress_cb(1.0, f"Done — {len(self.enriched):,} records cached")
        return self.enriched

    def enrichment_for(self, row: dict) -> dict:
        """Merged view: stored values win, enrichment only fills the gaps."""
        merged = dict(row)
        for k, v in self.enriched.get(self._enrich_key(row), {}).items():
            if not str(merged.get(k, "")).strip():
                merged[k] = v
        return merged

    def enrichment_stats(self):
        return len(self.enriched), len(self.records)

    # -- settings ------------------------------------------------------------
    def apply_settings(self, updates: dict, reload_data: bool = False):
        self.settings.update(updates)
        save_settings(updates)
        self.llm.reload(self.settings)
        if reload_data:
            self.reload_data()
        return self.settings


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_json(path: str, fallback):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback


def write_json(path: str, data) -> bool:
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
        os.replace(tmp, path)
        return True
    except Exception as e:
        print(f"[io] could not write {path}: {e}")
        return False


def _parse_json_array(text: str) -> list:
    text = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(),
                  flags=re.MULTILINE).strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except Exception:
        pass
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return []


# ── CLI diagnostics:  python backend.py ───────────────────────────────────────

if __name__ == "__main__":
    engine = LegalEngine()
    print("Folders searched:")
    for d in candidate_dirs(engine.settings.get("data_folder", "")):
        print("   ", d)
    print()
    print(engine.report_text())
    print()
    print(f"{len(engine.records):,} records \u00b7 {len(engine.index):,} index terms")
    print(f"Provider: {engine.llm.spec['label']} \u00b7 model {engine.llm.model} "
          f"\u00b7 key {engine.llm.key_hint()}")
