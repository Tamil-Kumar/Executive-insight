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
import math
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
    "deepseek/deepseek-r1",              # reasoning
    "openai/o4-mini",                    # reasoning
    "qwen/qwq-32b",                      # reasoning
]

OPENAI_MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4.1-mini",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-instruct",
    "o4-mini",                           # reasoning
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


_DIR_CACHE = {}


def clear_dir_cache():
    """Drop memoised directory listings (call before a rescan)."""
    _DIR_CACHE.clear()


def _dir_map(folder: str) -> dict:
    """lowercased filename -> full path, listed once per folder per scan."""
    cached = _DIR_CACHE.get(folder)
    if cached is None:
        try:
            cached = {name.lower(): os.path.join(folder, name)
                      for name in os.listdir(folder)}
        except OSError:
            cached = {}
        _DIR_CACHE[folder] = cached
    return cached


def resolve_data_path(filename: str, data_folder: str = ""):
    """Return (path_or_None, dirs_searched). Case-insensitive on every OS."""
    tried = candidate_dirs(data_folder)
    target = filename.lower()
    for folder in tried:
        hit = _dir_map(folder).get(target)
        if hit:
            return hit, tried
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
                reader = csv.DictReader(f, restval="")
                rows = list(reader)
                header = reader.fieldnames or []
            # Rebuilding every row is expensive; only do it if the header
            # actually has stray whitespace or a blank column name.
            if any(h is None or h != h.strip() for h in header):
                rows = [{(k or "").strip(): (v if isinstance(v, str) else "")
                         for k, v in row.items()} for row in rows]
            report.update(rows=len(rows), ok=True, error="")
            if not rows:
                report["error"] = "Parsed cleanly but has no data rows."
            return rows, report
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
    "Trump 2nd Term": "trump_eos.csv",   # 2025-2026
    "Trump 1st Term": "trump2.csv",      # 2017-2021
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


# ── Live government data (Federal Register API) ───────────────────────────────
#
# federalregister.gov exposes the same fields these CSVs already use, with no
# API key and no registration. That makes it a drop-in refresh: fetch, write a
# CSV in the identical schema, reload, and the tab populates.

FR_API = "https://www.federalregister.gov/api/v1/documents.json"

CSV_HEADER = ["citation", "document_number", "end_page", "html_url", "pdf_url",
              "type", "subtype", "publication_date", "signing_date",
              "start_page", "title", "disposition_notes",
              "executive_order_number", "not_received_for_publication"]

# tab name -> (Federal Register president slug, first year, last year)
FR_PRESIDENTS = {
    "Roosevelt":      ("franklin-d-roosevelt", 1936, 1945),
    "Truman":         ("harry-s-truman",       1945, 1953),
    "Eisenhower":     ("dwight-d-eisenhower",  1953, 1961),
    "Kennedy":        ("john-f-kennedy",       1961, 1963),
    "Johnson":        ("lyndon-b-johnson",     1963, 1969),
    "Nixon":          ("richard-nixon",        1969, 1974),
    "Ford":           ("gerald-r-ford",        1974, 1977),
    "Carter":         ("jimmy-carter",         1977, 1981),
    "Reagan":         ("ronald-reagan",        1981, 1989),
    "H.W. Bush":      ("george-h-w-bush",      1989, 1993),
    "Clinton":        ("william-j-clinton",    1993, 2001),
    "W. Bush":        ("george-w-bush",        2001, 2009),
    "Obama":          ("barack-obama",         2009, 2017),
    "Trump 1st Term": ("donald-trump",         2017, 2021),
    "Biden":          ("joe-biden",            2021, 2025),
    "Trump 2nd Term": ("donald-trump",         2025, 2029),
}


def _fr_get(params, timeout=60) -> dict:
    url = FR_API + "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Executive Insight (research tool)",
                      "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fr_row_key(row: dict) -> str:
    return (str(row.get("document_number") or "").strip()
            or f"{row.get('executive_order_number','')}|{row.get('title','')}")


def fetch_federal_register(slug: str, start_year: int, end_year: int,
                           progress_cb=None, stop_flag=None, label: str = ""):
    """
    Pull every presidential document for one president. Queried a year at a
    time because the API caps any single search at 2,000 results.
    """
    found, years = {}, list(range(start_year, end_year + 1))
    this_year = time.localtime().tm_year
    years = [y for y in years if y <= this_year]

    for n, year in enumerate(years, 1):
        if stop_flag is not None and stop_flag.is_set():
            break
        if progress_cb:
            progress_cb(n / max(len(years), 1),
                        f"{label or slug}: fetching {year} ({len(found):,} so far)")
        page = 1
        while page <= 2:                        # 2 x 1000 covers any single year
            params = [("conditions[type][]", "PRESDOCU"),
                      ("conditions[president][]", slug),
                      ("conditions[signing_date][gte]", f"{year}-01-01"),
                      ("conditions[signing_date][lte]", f"{year}-12-31"),
                      ("per_page", "1000"), ("order", "oldest"), ("page", str(page))]
            params += [("fields[]", f) for f in CSV_HEADER]
            try:
                data = _fr_get(params)
            except urllib.error.HTTPError as e:
                if e.code == 404:               # no documents that year
                    break
                raise
            results = data.get("results") or []
            for item in results:
                row = {f: ("" if item.get(f) is None else str(item.get(f)))
                       for f in CSV_HEADER}
                found[_fr_row_key(row)] = row
            if page >= int(data.get("total_pages") or 1):
                break
            page += 1
    return list(found.values())


def write_csv(path: str, rows: list) -> int:
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in CSV_HEADER})
    os.replace(tmp, path)
    return len(rows)




class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, settings=None):
        self.last_reasoning = ""
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

    # -- reasoning / thinking models -----------------------------------------
    # Models that think before answering behave differently in three ways:
    # the visible answer may be wrapped in <think> tags, the reasoning may come
    # back in a separate field, and the whole budget can be spent thinking so
    # that "content" arrives empty. All three are handled here.

    THINK_TAGS = re.compile(
        r"<(think|thinking|reasoning|thought|scratchpad)>.*?</\1>",
        re.DOTALL | re.IGNORECASE)
    UNCLOSED_THINK = re.compile(
        r"^\s*<(think|thinking|reasoning|thought|scratchpad)>.*", re.DOTALL | re.IGNORECASE)

    @staticmethod
    def looks_like_reasoner(model: str) -> bool:
        m = (model or "").lower()
        needles = ("o1", "o3", "o4-mini", "r1", "qwq", "reason", "think",
                   "deepseek-r", "magistral", "gpt-5")
        tail = m.split("/")[-1]
        return any(n in tail for n in needles)

    @classmethod
    def strip_thinking(cls, text: str) -> str:
        """Remove chain-of-thought so only the answer reaches the user."""
        if not text:
            return ""
        out = cls.THINK_TAGS.sub("", text)
        # A budget cut mid-thought leaves an opening tag with no close.
        if cls.UNCLOSED_THINK.match(out):
            for marker in ("</think>", "</thinking>", "</reasoning>"):
                if marker in out:
                    out = out.split(marker, 1)[1]
                    break
            else:
                out = ""
        return out.strip()

    @staticmethod
    def _extract(choice: dict):
        """Return (visible_text, reasoning_text) from one choice."""
        msg = choice.get("message") or {}
        content = msg.get("content")
        # Some gateways return content as a list of parts.
        if isinstance(content, list):
            content = "".join(p.get("text", "") for p in content
                              if isinstance(p, dict))
        reasoning = (msg.get("reasoning") or msg.get("reasoning_content") or "")
        if isinstance(reasoning, list):
            reasoning = "".join(p.get("text", "") for p in reasoning
                                if isinstance(p, dict))
        return (content or choice.get("text") or ""), (reasoning or "")

    def _build_payload(self, messages, max_tokens, temperature):
        model = self.model
        payload = {"model": model, "messages": messages}
        reasoner = self.looks_like_reasoner(model)

        # Thinking tokens are billed against the same budget as the answer, so
        # a normal ceiling can leave nothing for the reply.
        payload_tokens = max_tokens * 3 if reasoner else max_tokens

        if self.provider == "openai" and reasoner:
            # o-series takes max_completion_tokens and rejects temperature.
            payload["max_completion_tokens"] = payload_tokens
        else:
            payload["max_tokens"] = payload_tokens
            payload["temperature"] = temperature

        if self.provider == "openrouter" and reasoner:
            # Keep the thinking short; we only want the conclusion.
            payload["reasoning"] = {"effort": "low"}
        return payload

    # -- generation ----------------------------------------------------------
    def complete(self, system: str, user: str,
                 max_tokens: int = 800, temperature: float = 0.0,
                 history=None) -> str:
        model = self.model
        history = list(history or [])

        # Legacy OpenAI instruct models use /completions, not /chat/completions.
        if self.provider == "openai" and model.endswith("-instruct"):
            prior = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in history)
            data = self._post("/completions", {
                "model": model,
                "prompt": f"{system}\n\n{prior}\n\n{user}\n\nAnswer:".strip(),
                "max_tokens": max_tokens,
                "temperature": temperature,
            })
            return self.strip_thinking(data["choices"][0].get("text") or "")

        reasoner = self.looks_like_reasoner(model)
        # o-series models historically reject a system role.
        if self.provider == "openai" and reasoner:
            messages = history + [{"role": "user", "content": f"{system}\n\n{user}"}]
        else:
            messages = ([{"role": "system", "content": system}] + history
                        + [{"role": "user", "content": user}])

        budget = max_tokens
        for attempt in (1, 2):
            data = self._post("/chat/completions",
                              self._build_payload(messages, budget, temperature),
                              timeout=180 if reasoner else 90)
            choice = (data.get("choices") or [{}])[0]
            raw, reasoning = self._extract(choice)
            answer = self.strip_thinking(raw)
            self.last_reasoning = reasoning or self.THINK_TAGS.findall(raw or "")

            if answer:
                return answer

            finish = choice.get("finish_reason") or choice.get("native_finish_reason")
            if attempt == 1 and (finish == "length" or reasoning or raw):
                # It thought itself out of room. Give it more and ask for the
                # answer directly.
                budget = max_tokens * 3
                messages = messages + [
                    {"role": "assistant", "content": "(thinking omitted)"},
                    {"role": "user", "content":
                        "Give the final answer now. Do not show your reasoning."},
                ]
                continue

            if reasoning:
                raise LLMError(
                    f"'{model}' spent its whole budget reasoning and returned no "
                    f"answer. Try a larger budget or a non-reasoning model.")
            raise LLMError(f"'{model}' returned an empty response "
                           f"(finish_reason: {finish}).")
        return ""

    def test(self):
        """Return (ok: bool, message: str)."""
        if not self.api_key:
            return False, f"No {self.spec['label']} key set."
        try:
            t0 = time.time()
            out = self.complete("Reply with the single word OK.", "ping",
                                max_tokens=64 if self.looks_like_reasoner(self.model)
                                else 8,
                                temperature=0)
            ms = int((time.time() - t0) * 1000)
            kind = " (reasoning model)" if self.looks_like_reasoner(self.model) else ""
            return True, (f"Connected to {self.spec['label']} \u00b7 {self.model}{kind} "
                          f"\u00b7 {ms} ms \u00b7 replied \"{out[:20]}\"")
        except LLMError as e:
            return False, str(e)
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"


# ── Search index ──────────────────────────────────────────────────────────────

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP = {"the", "of", "and", "to", "for", "in", "on", "a", "an", "by", "with",
         "or", "as", "at", "is", "be", "from", "that", "this", "it",
         "what", "which", "who", "how", "many", "did", "does", "do", "was",
         "were", "are", "any", "all", "about", "me", "you", "i", "tell",
         "show", "list", "find", "give", "there", "their", "his", "her"}

# "EO 13805", "executive order 13805", or a bare 4-5 digit number
_EO_RE = re.compile(r"\b(?:e\.?o\.?|executive\s+order)?\s*#?\s*(\d{4,5})\b", re.I)

# Words in a question that pin it to one database.
_PRESIDENT_HINTS = {
    "trump": ("Trump 1st Term", "Trump 2nd Term"),
    "biden": ("Biden",),
    "obama": ("Obama",),
    "bush": ("W. Bush", "H.W. Bush"),
    "clinton": ("Clinton",),
    "reagan": ("Reagan",),
    "carter": ("Carter",),
    "ford": ("Ford",),
    "nixon": ("Nixon",),
    "johnson": ("Johnson",),
    "lbj": ("Johnson",),
    "kennedy": ("Kennedy",),
    "jfk": ("Kennedy",),
    "eisenhower": ("Eisenhower",),
    "ike": ("Eisenhower",),
    "truman": ("Truman",),
    "roosevelt": ("Roosevelt",),
    "fdr": ("Roosevelt",),
}


# Used to pull the right slice out of the Historical archive when a president is
# named but their own database isn't loaded.
PRESIDENT_TERMS = {
    "Roosevelt":      (1933, 1945),
    "Truman":         (1945, 1953),
    "Eisenhower":     (1953, 1961),
    "Kennedy":        (1961, 1963),
    "Johnson":        (1963, 1969),
    "Nixon":          (1969, 1974),
    "Ford":           (1974, 1977),
    "Carter":         (1977, 1981),
    "Reagan":         (1981, 1989),
    "H.W. Bush":      (1989, 1993),
    "Clinton":        (1993, 2001),
    "W. Bush":        (2001, 2009),
    "Obama":          (2009, 2017),
    "Trump 1st Term": (2017, 2021),
    "Biden":          (2021, 2025),
    "Trump 2nd Term": (2025, 2029),
}

_YEAR_RE = re.compile(r"(19|20)\d{2}")


def _record_year(row: dict):
    m = _YEAR_RE.search(str(row.get("signing_date") or
                            row.get("publication_date") or ""))
    return int(m.group(0)) if m else None


def _tokens(text: str) -> set:
    return {t for t in _TOKEN_RE.findall((text or "").lower())
            if len(t) > 1 and t not in _STOP}


SYSTEM_PROMPT = """You are Executive Insight, a research assistant for the \
United States presidential document archive. You answer questions about \
executive orders, proclamations, memoranda and notices using the records \
supplied to you in each message.

WHAT YOU ARE WORKING WITH
The archive is Federal Register *metadata*, not the text of the documents. \
Each record has some subset of: executive_order_number, title, signing_date \
(YYYY-MM-DD), publication_date (MM/DD/YYYY), subtype, citation (Federal \
Register volume and page), document_number, disposition_notes, and links. \
Older records, especially pre-1994, are often missing document numbers, page \
numbers and links. An empty field is a gap in the source data, not a zero and \
not evidence that something did not happen.

You never see the body of an order. If someone asks what an order actually \
says, provides for, or requires beyond what the title states, say the archive \
holds the citation and status but not the text, then point them at the record's \
link. Do not reconstruct the contents from background knowledge and present it \
as though it came from the archive.

READING disposition_notes
This field is the amendment chain and it is how you determine current status:
  "Revoked by: EO 13811, September 29, 2017"  -> no longer in effect from that date
  "Superseded by: ..."                        -> replaced
  "Amended by: ..."                           -> still in effect, modified
  "Amends: ..." / "Supersedes: ..."           -> what THIS order did to earlier ones
  "Continued by: ..." / "See: ..."            -> related actions
Report status from these notes and give the date. An empty disposition_notes \
field means the archive records no later action; it is not proof the order is \
still in force. Say "no later action recorded" rather than "still in effect".

THE COVERAGE BLOCK
Every message begins with a coverage block listing which databases are loaded \
and how many records each holds. Use it, because it is exact:
  - For counting or "how many" questions, cite the totals in that block. The \
records shown below it are only the top matches for the question, never a \
complete set, so never count them and present the number as a total.
  - If a question is about a president whose database is NOT loaded, say that \
the database is not loaded rather than saying no such orders exist. Those are \
completely different claims.
  - The Historical database overlaps the per-president ones, so the same order \
can appear twice. Report it once.

HOW TO ANSWER
Lead with the direct answer in a sentence or two, then the supporting records. \
Reference documents as: EO 13805 (signed 2017-07-19). When only a publication \
date exists, use it and label it as published. When listing several records, \
use one short line each: number, title, date, and status if the notes give one. \
Do not dump raw field lists at the reader, and do not restate the coverage \
block unless it is the answer.

Match length to the question. A one-fact question gets one or two sentences. \
Do not add a summary paragraph that repeats what you just said, and do not \
open with a restatement of the question.

If the supplied records do not answer the question, say so in one line, name \
what you looked at, and suggest a sharper search term or a specific president \
and year. Do not pad with general knowledge to fill the gap.

HARD RULES
Never invent an executive order number, title, date, citation or URL. Every \
number and date you give must appear in the records above. If you are working \
from your own background knowledge rather than the records, label it plainly as \
outside the archive. You do research, not legal advice; if someone asks whether \
something is legal or applies to them, give them the documents and tell them to \
take it to a lawyer."""


# ── Engine ────────────────────────────────────────────────────────────────────

class LegalEngine:
    def __init__(self, settings=None):
        self.settings = settings if settings is not None else load_settings()
        self.llm = LLMClient(self.settings)

        self.sources = dict(PRESIDENT_SOURCES)
        self.csv_files = list(PRESIDENT_SOURCES.values())

        self.records = []            # dicts, each carrying _source/_president/_id
        self._corpus = None          # lazy "col: val" strings
        self.load_report = []        # per-file diagnostics
        self.index = {}              # token -> [record ids]
        self.title_index = {}        # token -> [record ids], titles only
        self.by_eo = {}              # executive order number -> [record ids]
        self.chat_history = []       # rolling Legal Q&A turns
        self.data_version = 0        # bumped on every reload, tabs watch this
        self.last_sync = []          # result of the last Federal Register sync
        self.enriched = load_json(ENRICH_PATH, {})

        self.reload_data()

    # -- data ----------------------------------------------------------------
    def reload_data(self, progress_cb=None):
        clear_dir_cache()
        self.records, self.load_report = [], []
        self._corpus = None                    # invalidate the lazy corpus
        folder = str(self.settings.get("data_folder", "") or "")
        records = self.records
        n_files = len(self.sources) or 1

        for n, (president, filename) in enumerate(self.sources.items(), 1):
            if progress_cb:
                progress_cb(n / (n_files + 1), f"Reading {filename}")
            rows, report = load_csv_resilient(filename, folder)
            report["president"] = president
            self.load_report.append(report)
            base = len(records)
            for offset, row in enumerate(rows):
                # rows come straight from the loader, so they can be tagged in
                # place rather than copied
                row["_source"] = filename
                row["_president"] = president
                row["_id"] = base + offset
            records.extend(rows)

        self.build_index(progress_cb=progress_cb)
        self.data_version += 1
        return self.load_report

    @property
    def all_data_content(self):
        """Formatted record strings. Built on first use, not on every load."""
        if getattr(self, "_corpus", None) is None:
            self._corpus = [self._format(r) for r in self.records]
        return self._corpus

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

    # -- live government data ------------------------------------------------
    def sync_government_data(self, targets=None, only_missing: bool = True,
                             refresh_years: int = 2, progress_cb=None,
                             stop_flag=None) -> list:
        """
        Pull presidential documents from the Federal Register and write them to
        the CSVs the tabs read. Empty tabs get filled completely; tabs that
        already have data only get the last couple of years refreshed, so a
        sync stays quick and never throws away existing rows.

        Returns a list of {"president", "file", "added", "total", "error"}.
        """
        folder = (str(self.settings.get("data_folder", "") or "").strip()
                  or APP_DIR)
        if not os.path.isdir(folder):
            folder = APP_DIR

        have = {r["president"]: r for r in self.load_report}
        if targets is None:
            targets = [name for name in self.sources
                       if name in FR_PRESIDENTS
                       and (not only_missing
                            or not (have.get(name, {}).get("ok")
                                    and have.get(name, {}).get("rows")))]

        this_year = time.localtime().tm_year
        summary = []

        for n, name in enumerate(targets, 1):
            if stop_flag is not None and stop_flag.is_set():
                break
            slug, first, last = FR_PRESIDENTS[name]
            filename = self.sources.get(name)
            if not filename:
                continue

            report = have.get(name, {})
            populated = bool(report.get("ok") and report.get("rows"))
            # Full history for an empty tab, recent window for a populated one.
            if populated:
                start = max(first, min(last, this_year) - refresh_years + 1)
            else:
                start = first
            end = min(last, this_year)

            def step(frac, msg):
                if progress_cb:
                    progress_cb((n - 1 + frac) / max(len(targets), 1), msg)

            entry = {"president": name, "file": filename, "added": 0,
                     "total": 0, "error": ""}
            try:
                fetched = fetch_federal_register(slug, start, end,
                                                 progress_cb=step,
                                                 stop_flag=stop_flag,
                                                 label=name)
            except urllib.error.HTTPError as e:
                entry["error"] = f"Federal Register returned HTTP {e.code}"
                summary.append(entry)
                continue
            except urllib.error.URLError as e:
                entry["error"] = f"No connection to federalregister.gov ({e.reason})"
                summary.append(entry)
                continue
            except Exception as e:
                entry["error"] = f"{type(e).__name__}: {e}"
                summary.append(entry)
                continue

            if not fetched:
                entry["error"] = "No documents returned for this period."
                summary.append(entry)
                continue

            # Merge into whatever is already on disk rather than overwriting.
            path, _ = resolve_data_path(filename, folder)
            existing, _rep = (load_csv_resilient(filename, folder)
                              if path else ([], None))
            merged = {_fr_row_key(r): r for r in existing}
            before = len(merged)
            for row in fetched:
                merged[_fr_row_key(row)] = row

            out_path = path or os.path.join(folder, filename)
            try:
                write_csv(out_path, sorted(
                    merged.values(),
                    key=lambda r: (r.get("signing_date", ""),
                                   r.get("executive_order_number", ""))))
            except Exception as e:
                entry["error"] = f"Could not write {out_path}: {e}"
                summary.append(entry)
                continue

            entry["added"] = len(merged) - before
            entry["total"] = len(merged)
            summary.append(entry)

        if progress_cb:
            gained = sum(s["added"] for s in summary)
            progress_cb(1.0, f"Sync complete — {gained:,} new records across "
                             f"{len(summary)} databases")
        self.last_sync = summary
        return summary

    def sync_and_index(self, progress_cb=None, stop_flag=None,
                       only_missing: bool = True):
        """Pull fresh data, reload every CSV, then rebuild the index."""
        summary = self.sync_government_data(only_missing=only_missing,
                                            progress_cb=progress_cb,
                                            stop_flag=stop_flag)
        self.reload_data(progress_cb=progress_cb)
        return summary

    # -- index ---------------------------------------------------------------
    def build_index(self, progress_cb=None) -> dict:
        # Hot loop, so everything it touches is a local: no attribute lookups,
        # no setdefault (which allocates a throwaway list on every hit), and
        # each record's text is tokenised exactly once.
        index, title_index, by_eo = {}, {}, {}
        findall = _TOKEN_RE.findall
        stop = _STOP
        records = self.records
        total = len(records) or 1
        step = max(total // 20, 1)

        for i, row in enumerate(records):
            get = row.get

            title_toks = {t for t in findall(get("title", "").lower())
                          if len(t) > 1}
            title_toks -= stop
            for tok in title_toks:
                bucket = title_index.get(tok)
                if bucket is None:
                    title_index[tok] = [i]
                else:
                    bucket.append(i)

            rest = " ".join((get("disposition_notes", ""),
                             get("executive_order_number", ""),
                             get("citation", ""),
                             get("subtype", ""),
                             get("_president", ""))).lower()
            toks = {t for t in findall(rest) if len(t) > 1}
            toks -= stop
            toks |= title_toks
            for tok in toks:
                bucket = index.get(tok)
                if bucket is None:
                    index[tok] = [i]
                else:
                    bucket.append(i)

            eo = get("executive_order_number", "").strip()
            if eo:
                bucket = by_eo.get(eo)
                if bucket is None:
                    by_eo[eo] = [i]
                else:
                    bucket.append(i)

            if progress_cb and i % step == 0:
                progress_cb(i / total, f"Indexing {i:,} of {total:,} records")

        self.index = index
        self.title_index = title_index
        self.by_eo = by_eo
        if progress_cb:
            progress_cb(1.0, f"Indexed {len(records):,} records \u00b7 "
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

    @staticmethod
    def _dedupe_key(row: dict):
        eo = str(row.get("executive_order_number", "")).strip()
        title = str(row.get("title", "")).strip().lower()
        return ("eo", eo) if eo else ("t", title, str(row.get("signing_date", "")))

    def _dedupe(self, rows: list) -> list:
        """Collapse the Historical/per-president overlap, keeping the richer copy."""
        seen, out = {}, []
        for row in rows:
            key = self._dedupe_key(row)
            if key not in seen:
                seen[key] = len(out)
                row = dict(row)
                row["_also_in"] = []
                out.append(row)
                continue
            kept = out[seen[key]]
            other = str(row.get("_president", ""))
            if other and other not in kept["_also_in"]:
                kept["_also_in"].append(other)
            # A per-president record beats the Historical catch-all.
            if kept.get("_source") == "past.csv" and row.get("_source") != "past.csv":
                merged = dict(row)
                merged["_also_in"] = kept["_also_in"]
                out[seen[key]] = merged
        return out

    def search(self, query: str, limit: int = 100) -> list:
        """
        Ranked retrieval. Rare words count for more than common ones, title
        matches count double, an explicit EO number wins outright, and a named
        president biases the results toward that database.
        """
        query = query or ""
        toks = _tokens(query)
        if not toks and not _EO_RE.search(query):
            return self._dedupe(self.records)[:limit]

        n = max(len(self.records), 1)
        scores, matched = {}, {}

        def add(postings, weight, tok):
            if not postings:
                return
            idf = math.log(1 + n / len(postings))
            for rid in postings:
                scores[rid] = scores.get(rid, 0.0) + weight * idf
                matched.setdefault(rid, set()).add(tok)

        for tok in toks:
            add(self.index.get(tok), 1.0, tok)
            add(self.title_index.get(tok), 1.5, tok)

        # With a multi-word question, one incidental word in common is not a
        # match. Require two, unless that leaves nothing at all.
        if len(toks) >= 2:
            strict = {rid: sc for rid, sc in scores.items()
                      if len(matched.get(rid, ())) >= 2}
            if strict:
                scores = strict

        low = query.lower()

        # An explicit document number takes over the whole result set: the order
        # itself, plus every record whose notes reference it (the amendment chain).
        exact = set()
        for num in _EO_RE.findall(query):
            exact.update(getattr(self, "by_eo", {}).get(num, ()))
        if exact:
            chain = set()
            for num in _EO_RE.findall(query):
                chain.update(self.index.get(num, ()))
            focused = {rid: (100.0 if rid in exact else 20.0)
                       for rid in (exact | chain)}
            ranked = sorted(focused.items(), key=lambda kv: -kv[1])
            return self._dedupe([self.records[rid] for rid, _ in ranked])[:limit]

        # A named president filters rather than merely nudges. Their own database
        # when it's loaded, otherwise their years out of the Historical archive.
        wanted = set()
        for word, names in _PRESIDENT_HINTS.items():
            if re.search(r"\b" + word + r"\b", low):
                wanted.update(names)
        if wanted:
            spans = [PRESIDENT_TERMS[n] for n in wanted if n in PRESIDENT_TERMS]

            def in_scope(rid):
                row = self.records[rid]
                if row.get("_president") in wanted:
                    return True
                if row.get("_president") == "Historical":
                    yr = _record_year(row)
                    return yr is not None and any(a <= yr <= b for a, b in spans)
                return False

            # If the named president has nothing on this topic, say nothing —
            # returning off-topic records from other administrations is worse
            # than an empty result.
            scores = {rid: sc for rid, sc in scores.items() if in_scope(rid)}
            if not scores:
                return []

        if not scores:                                    # substring fallback
            q = low.strip()
            hits = [r for r in self.records
                    if q and q in str(r.get("title", "")).lower()]
            return self._dedupe(hits)[:limit]

        ranked = sorted(scores.items(), key=lambda kv: -kv[1])[:limit * 3]
        # Drop the long tail of one-weak-token matches; they only dilute the
        # context the model reasons over.
        cutoff = ranked[0][1] * 0.35
        ranked = [pair for pair in ranked if pair[1] >= cutoff]
        return self._dedupe([self.records[rid] for rid, _ in ranked])[:limit]

    def search_records(self, query: str, limit: int = 100) -> list:
        """Frontend compatibility: returns formatted strings."""
        return [self._format(r) for r in self.search(query, limit)]

    @staticmethod
    def _format(row: dict) -> str:
        return "\n".join(f"{k}: {v}" for k, v in row.items()
                         if v and not str(k).startswith("_"))

    # -- AI ------------------------------------------------------------------
    def coverage_block(self) -> str:
        """Exact per-database totals and date spans — the model's ground truth."""
        loaded, missing = [], []
        for r in sorted(self.load_report, key=lambda x: -x["rows"]):
            name = r["president"]
            if r["ok"] and r["rows"]:
                years = self._year_span(name)
                loaded.append(f"  {name:<16} {r['rows']:>6,} records{years}")
            else:
                missing.append(name)

        lines = [f"ARCHIVE COVERAGE — {len(self.records):,} records across "
                 f"{len(self.loaded_sources())} databases"]
        lines += loaded
        if missing:
            lines.append("  NOT LOADED (no data available for these, do not "
                         "claim their orders don't exist): " + ", ".join(missing))
        return "\n".join(lines)

    def _year_span(self, president: str) -> str:
        years = []
        for r in self.records:
            if r.get("_president") != president:
                continue
            m = re.search(r"(19|20)\d{2}", str(r.get("signing_date") or
                                               r.get("publication_date") or ""))
            if m:
                years.append(int(m.group(0)))
        return f"   {min(years)}\u2013{max(years)}" if years else ""

    def _record_block(self, row: dict, n: int) -> str:
        eo = str(row.get("executive_order_number", "")).strip()
        head = f"[{n}] " + (f"EO {eo}" if eo else "(no EO number)")
        head += f" \u00b7 {row.get('_president', '')}"
        signed = str(row.get("signing_date", "")).strip()
        pub = str(row.get("publication_date", "")).strip()
        if signed:
            head += f" \u00b7 signed {signed}"
        if pub:
            head += f" \u00b7 published {pub}"

        out = [head, f"    Title: {row.get('title', '') or '(untitled)'}"]
        meta = []
        if row.get("subtype"):
            meta.append(str(row["subtype"]))
        if row.get("citation"):
            meta.append(str(row["citation"]))
        if meta:
            out.append("    " + " \u00b7 ".join(meta))

        notes = " ".join(str(row.get("disposition_notes", "")).split())
        out.append(f"    Notes: {notes}" if notes else
                   "    Notes: (none recorded)")
        if row.get("html_url"):
            out.append(f"    Link: {row['html_url']}")
        if row.get("_also_in"):
            out.append("    Also appears in: " + ", ".join(row["_also_in"]))
        return "\n".join(out)

    def build_context(self, user_query: str, k: int = 25,
                      char_budget: int = 14000):
        hits = self.search(user_query, limit=k)
        blocks, used = [], 0
        for i, row in enumerate(hits, 1):
            block = self._record_block(row, i)
            if used + len(block) > char_budget:
                break
            blocks.append(block)
            used += len(block)

        if blocks:
            body = (f"TOP {len(blocks)} MATCHING RECORDS (a ranked sample, not "
                    f"a complete set):\n\n" + "\n\n".join(blocks))
        else:
            body = ("TOP MATCHING RECORDS: none. Nothing in the loaded "
                    "databases matched this question.")
        return self.coverage_block() + "\n\n" + body, hits

    def query_ai(self, user_query: str, k: int = 25, use_history: bool = True) -> str:
        context, _ = self.build_context(user_query, k=k)
        prompt = f"{context}\n\nQUESTION: {user_query}"

        history = self.chat_history[-6:] if use_history else []
        answer = self.llm.complete(SYSTEM_PROMPT, prompt,
                                   max_tokens=1400, temperature=0,
                                   history=history)
        if use_history:
            # Store the question without its context so history stays cheap.
            self.chat_history.append({"role": "user", "content": user_query})
            self.chat_history.append({"role": "assistant", "content": answer})
            self.chat_history = self.chat_history[-12:]
        return answer

    def reset_chat(self):
        self.chat_history = []

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
