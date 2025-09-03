# cli/gui_repo.py
import json, uuid, re, tkinter as tk
from datetime import datetime, timezone
from tkinter import ttk, messagebox, simpledialog, filedialog
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "prompts.json"   # << uses your repo schema

# ---------- Schema helpers ----------
def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def slug(s: str):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def ensure_meta(p):
    p.setdefault("meta", {})
    p["meta"].setdefault("createdAt", now_iso())
    p["meta"].setdefault("updatedAt", p["meta"]["createdAt"])
    p["meta"].setdefault("usageCount", 0)
    p["meta"].setdefault("author", "Kait")

def load_flat():
    items = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    # normalize/ensure schema
    for p in items:
        p.setdefault("id", f"{slug(p.get('title','untitled'))}-{uuid.uuid4().hex[:8]}")
        p.setdefault("title", "(untitled)")
        p.setdefault("category", "Uncategorized")
        p.setdefault("body", "")
        p.setdefault("tags", [])
        p.setdefault("system", None)
        ensure_meta(p)
    return items

def save_flat(items):
    # ensure we only write schema fields
    clean = []
    for p in items:
        q = {
            "id": p["id"],
            "title": p.get("title",""),
            "category": p.get("category","Uncategorized"),
            "tags": list(dict.fromkeys([t.lower() for t in (p.get("tags") or [])])),
            "body": p.get("body",""),
            "system": p.get("system"),
            "meta": p.get("meta") or {},
        }
        ensure_meta(q)
        clean.append(q)
    DATA_PATH.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------- Grouping for UI ----------
def group_by_category(items):
    cats = {}
    for p in items:
        cats.setdefault(p["category"], []).append(p)
    # sort inside each category by updatedAt desc
    for k in cats:
        cats[k].sort(key=lambda x: (x.get("meta") or {}).get("updatedAt",""), reverse=True)
    return dict(sorted(cats.items(), key=lambda kv: kv[0].lower()))

# ---------- GUI ----------
APP_TITLE = "TaylorMadePromptLibrary — GUI (repo schema)"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE); self.geometry("1040x720"); self.minsize(900,600)
        self.items = load_flat()
        self.cats = group_by_category(self.items)

        self.nb = ttk.Notebook(self); self.nb.pack(fill="both", expand=True)
        self.tabs = {}
        for cat in self.cats:
            self.add_tab(cat)

        footer = ttk.Frame(self); footer.pack(fill="x", padx=10, pady=(4,10))
        ttk.Button(footer, text="Add Prompt", command=self.add_prompt).pack(side="left")
        ttk.Button(footer, text="New Category", command=self.new_category).pack(side="left", padx=6)
        ttk.Button(footer, text="Open JSON", command=self.open_json).pack(side="right")

    # ---- tabs ----
    def add_tab(self, cat):
        f = CategoryTab(self.nb, self, cat)
        self.nb.add(f, text=cat)
        self.tabs[cat] = f

    def rebuild_tabs(self, keep_index=True):
        cur = self.nb.index(self.nb.select()) if (keep_index and self.nb.tabs()) else 0
        for t in list(self.nb.tabs()):
            self.nb.forget(t)
        self.tabs.clear()
        self.cats = group_by_category(self.items)
        for cat in self.cats:
            self.add_tab(cat)
        try:
            self.nb.select(cur)
        except Exception:
            pass

    # ---- data ops ----
    def add_prompt(self):
        cat = simpledialog.askstring("Category", "Category for the new prompt:")
        if not cat:
            return
        title = simpledialog.askstring("Title", "Prompt title:")
        if not title:
            return
        body = self.edit_multiline("Body", "Enter prompt body:")
        if body is None:
            return
        new_id = f"{slug(title)}-{uuid.uuid4().hex[:8]}"
        new = {
            "id": new_id,
            "title": title,
            "category": cat,
            "tags": [],
            "body": body,
            "system": None,
            "meta": {"createdAt": now_iso(), "updatedAt": now_iso(), "usageCount": 0, "author": "Kait"},
        }
        self.items.append(new)
        save_flat(self.items)
        self.rebuild_tabs(keep_index=False)
        messagebox.showinfo("Added", f"Added: {new_id}")

    def new_category(self):
        name = simpledialog.askstring("New Category", "Enter new category:")
        if not name:
            return
        if name not in self.cats:
            self.cats[name] = []
            self.rebuild_tabs()
            messagebox.showinfo("Category", f"Created category: {name}")

    def open_json(self):
        messagebox.showinfo("JSON path", str(DATA_PATH))

    def edit_multiline(self, title, prompt, initial=""):
        win = tk.Toplevel(self); win.title(title); win.geometry("700x450")
        ttk.Label(win, text=prompt).pack(anchor="w", padx=8, pady=(8,4))
        txt = tk.Text(win, wrap="word"); txt.pack(fill="both", expand=True, padx=8, pady=(0,8))
        txt.insert("1.0", initial)
        out = {"value": None}
        def ok():
            out["value"] = txt.get("1.0","end").rstrip()
            win.destroy()
        def cancel():
            win.destroy()
        btn = ttk.Frame(win); btn.pack(fill="x", padx=8, pady=8)
        ttk.Button(btn, text="OK", command=ok).pack(side="right")
        ttk.Button(btn, text="Cancel", command=cancel).pack(side="right", padx=(0,8))
        win.transient(self); win.grab_set(); self.wait_window(win)
        return out["value"]

class CategoryTab(ttk.Frame):
    def __init__(self, nb, app: App, category: str):
        super().__init__(nb)
        self.app = app
        self.category = category
        self.build()

    def build(self):
        top = ttk.Frame(self); top.pack(fill="x", padx=10, pady=(10,6))
        ttk.Label(top, text=f"{self.category} — Prompts", font=("Segoe UI", 11, "bold")).pack(side="left")
        self.q = tk.StringVar(value=""); e = ttk.Entry(top, textvariable=self.q, width=36); e.pack(side="right", padx=(6,0))
        ttk.Label(top, text="Search").pack(side="right")
        e.bind("<KeyRelease>", lambda _e: self.refresh())

        main = ttk.Frame(self); main.pack(fill="both", expand=True, padx=10, pady=6)
        left = ttk.Frame(main); left.pack(side="left", fill="y", padx=(0,8))
        self.lb = tk.Listbox(left, height=20, width=36); self.lb.pack(side="left", fill="y")
        self.lb.bind("<<ListboxSelect>>", self.on_select)
        sb = ttk.Scrollbar(left, orient="vertical", command=self.lb.yview); self.lb.config(yscrollcommand=sb.set); sb.pack(side="right", fill="y")

        center = ttk.Frame(main); center.pack(side="left", fill="both", expand=True)
        ttk.Label(center, text="Title").grid(row=0, column=0, sticky="w")
        self.title = tk.StringVar(); ttk.Entry(center, textvariable=self.title).grid(row=0, column=1, sticky="we", pady=2)

        ttk.Label(center, text="Body").grid(row=1, column=0, sticky="nw")
        self.body = tk.Text(center, height=8, wrap="word"); self.body.grid(row=1, column=1, sticky="nsew", pady=2)

        ttk.Label(center, text="Tags (comma-separated)").grid(row=2, column=0, sticky="w")
        self.tags = tk.StringVar(); ttk.Entry(center, textvariable=self.tags).grid(row=2, column=1, sticky="we", pady=2)

        ttk.Label(center, text="System (optional)").grid(row=3, column=0, sticky="w")
        self.system = tk.StringVar(); ttk.Entry(center, textvariable=self.system).grid(row=3, column=1, sticky="we", pady=2)

        center.grid_columnconfigure(1, weight=1)
        center.grid_rowconfigure(1, weight=1)

        right = ttk.Frame(main); right.pack(side="left", fill="both", padx=(8,0))
        ttk.Button(right, text="Save Changes", command=self.save).pack(anchor="w")
        ttk.Button(right, text="Delete", command=self.delete).pack(anchor="w", pady=(6,0))
        ttk.Button(right, text="Export selected → file", command=self.export_selected).pack(anchor="w", pady=(6,0))

        self.refresh()

    def filtered_indices(self):
        q = (self.q.get() or "").lower()
        indices = []
        for i, p in enumerate(self.app.cats.get(self.category, [])):
            hay = (p.get("title","") + " " + p.get("body","") + " " + " ".join(p.get("tags") or [])).lower()
            if q in hay:
                indices.append(i)
        return indices

    def refresh(self):
        self.lb.delete(0, "end")
        for i in self.filtered_indices():
            p = self.app.cats[self.category][i]
            self.lb.insert("end", p.get("title","(untitled)"))

        self.title.set("")
        self.body.delete("1.0","end")
        self.tags.set("")
        self.system.set("")

    def current_index(self):
        if not self.lb.curselection():
            return None
        visible = self.filtered_indices()
        return visible[self.lb.curselection()[0]] if self.lb.curselection() else None

    def on_select(self, _e):
        i = self.current_index()
        if i is None: return
        p = self.app.cats[self.category][i]
        self.title.set(p.get("title",""))
        self.body.delete("1.0","end"); self.body.insert("1.0", p.get("body",""))
        self.tags.set(", ".join(p.get("tags") or []))
        self.system.set(p.get("system") or "")

    def save(self):
        i = self.current_index()
        if i is None:
            messagebox.showwarning("No selection", "Select a prompt first."); return
        p = self.app.cats[self.category][i]
        # Update fields
        p["title"] = self.title.get().strip() or p.get("title","")
        p["body"] = self.body.get("1.0","end").rstrip()
        p["tags"] = [t.strip().lower() for t in self.tags.get().split(",") if t.strip()]
        p["system"] = (self.system.get().strip() or None)
        # Bump updatedAt in the flat item list
        for item in self.app.items:
            if item["id"] == p["id"]:
                item.update(p)
                item["meta"]["updatedAt"] = now_iso()
                break
        save_flat(self.app.items)
        # Rebuild UI (re-sorts by updatedAt)
        self.app.rebuild_tabs()
        messagebox.showinfo("Saved", "Changes saved to data\\prompts.json")

    def delete(self):
        i = self.current_index()
        if i is None: return
        p = self.app.cats[self.category][i]
        if not messagebox.askyesno("Delete", f"Delete “{p.get('title','(untitled)')}”?"):
            return
        self.app.items = [it for it in self.app.items if it["id"] != p["id"]]
        save_flat(self.app.items)
        self.app.rebuild_tabs()

    def export_selected(self):
        i = self.current_index()
        if i is None:
            messagebox.showwarning("No selection", "Select a prompt first."); return
        p = self.app.cats[self.category][i]
        dest = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON","*.json")],
                                            initialfile=f"{slug(p.get('title','prompt'))}.json",
                                            title="Export prompt to file")
        if not dest: return
        Path(dest).write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
        messagebox.showinfo("Exported", f"Saved: {dest}")

if __name__ == "__main__":
    if not DATA_PATH.exists():
        messagebox = __import__("tkinter.messagebox").messagebox
        messagebox.showerror("Missing file", f"Could not find {DATA_PATH}")
        raise SystemExit(1)
    App().mainloop()

