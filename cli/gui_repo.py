import json, uuid, re, csv, tkinter as tk
from datetime import datetime, timezone
from tkinter import ttk, messagebox, simpledialog, filedialog
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "prompts.json"

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")

def ensure_meta(p: dict) -> None:
    p.setdefault("meta", {})
    p["meta"].setdefault("createdAt", now_iso())
    p["meta"].setdefault("updatedAt", p["meta"]["createdAt"])
    p["meta"].setdefault("usageCount", 0)
    p["meta"].setdefault("author", "Kait")

def load_flat() -> list:
    # use utf-8-sig to ignore BOM
    items = json.loads(DATA_PATH.read_text(encoding="utf-8-sig"))
    for p in items:
        p.setdefault("id", f"{slug(p.get('title','untitled'))}-{uuid.uuid4().hex[:8]}")
        p.setdefault("title", "(untitled)")
        p.setdefault("category", "Uncategorized")
        p.setdefault("body", "")
        p.setdefault("tags", [])
        p.setdefault("system", None)
        ensure_meta(p)
    return items

def save_flat(items: list) -> None:
    clean = []
    for p in items:
        q = {
            "id": p["id"],
            "title": p.get("title", ""),
            "category": p.get("category", "Uncategorized"),
            "tags": list(dict.fromkeys([t.lower() for t in (p.get("tags") or [])])),
            "body": p.get("body", ""),
            "system": p.get("system", None),
            "meta": p.get("meta") or {},
        }
        ensure_meta(q)
        clean.append(q)
    DATA_PATH.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")

def group_by_category(items: list) -> dict:
    cats = {}
    for p in items:
        cats.setdefault(p["category"], []).append(p)
    for k in cats:
        cats[k].sort(key=lambda x: (x.get("meta") or {}).get("updatedAt", ""), reverse=True)
    return dict(sorted(cats.items(), key=lambda kv: kv[0].lower()))

def rows_for_export(prompts: list) -> list:
    rows = []
    for p in prompts:
        meta = p.get("meta") or {}
        rows.append({
            "id": p.get("id", ""),
            "title": p.get("title", ""),
            "category": p.get("category", ""),
            "tags": ", ".join(p.get("tags") or []),
            "system": (p.get("system") or ""),
            "body": (p.get("body", "") or "").replace("\r\n", "\n").strip(),
            "createdAt": meta.get("createdAt", ""),
            "updatedAt": meta.get("updatedAt", ""),
            "usageCount": meta.get("usageCount", ""),
            "author": meta.get("author", ""),
        })
    return rows

def filtered_prompts_for_category(app, category: str, query_text: str) -> list:
    q = (query_text or "").lower()
    out = []
    for p in app.cats.get(category, []):
        hay = (p.get("title", "") + " " + p.get("body", "") + " " + " ".join(p.get("tags") or [])).lower()
        if q in hay:
            out.append(p)
    return out

APP_TITLE = "TaylorMadePromptLibrary — GUI"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1040x720")
        self.minsize(900, 600)

        try:
            self.call("tk", "scaling", 1.25)
        except tk.TclError:
            pass

        style = ttk.Style(self)
        try:
            if "vista" in style.theme_names():
                style.theme_use("vista")
        except tk.TclError:
            pass

        self.items = load_flat()
        self.cats = group_by_category(self.items)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)
        self.tabs = {}
        for cat in self.cats:
            self.add_tab(cat)

        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=10, pady=(4, 10))

        ttk.Button(footer, text="Add Prompt", command=self.add_prompt).pack(side="left")
        ttk.Button(footer, text="New Category", command=self.new_category).pack(side="left", padx=6)
        ttk.Button(footer, text="Open JSON", command=self.open_json).pack(side="right")
        ttk.Button(footer, text="Export ALL → Markdown", command=self.export_all_md).pack(side="right", padx=6)
        ttk.Button(footer, text="Export ALL → CSV", command=self.export_all_csv).pack(side="right", padx=6)

    # … [keep CategoryTab class + export functions same as before]

if __name__ == "__main__":
    if not DATA_PATH.exists():
        messagebox = __import__("tkinter.messagebox").messagebox
        messagebox.showerror("Missing file", f"Could not find {DATA_PATH}")
        raise SystemExit(1)
    App().mainloop()
