#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ---------------- Persistence Helpers ----------------
DB_FILE = "prompt_library.json"

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"categories": [], "prompts": []}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ---------------- Tooltip ----------------
class Tooltip(tk.Toplevel):
    def __init__(self, widget, text: str):
        super().__init__(widget)
        self.wm_overrideredirect(True)
        self.configure(bg="#333333")
        self.label = tk.Label(
            self, text=text, background="#333333", foreground="white",
            relief="solid", borderwidth=1, padx=6, pady=4, font=("Segoe UI", 9)
        )
        self.label.pack()
        self.withdraw()

    def set_text(self, text: str):
        self.label.configure(text=text)

    def show(self, x, y):
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        tip_w = self.winfo_reqwidth()
        tip_h = self.winfo_reqheight()

        if x + tip_w > screen_w:
            x = screen_w - tip_w - 10
        if y + tip_h > screen_h:
            y = screen_h - tip_h - 10

        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def hide(self):
        self.withdraw()

# ---------------- AutocompleteEntry ----------------
class AutocompleteEntry(ttk.Entry):
    def __init__(self, master, values: list[str] = None, max_suggestions: int = 10,
                 tokens: list[str] = None, token_help: dict[str, str] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.values = sorted(values or [], key=str.lower)
        self.tokens = tokens or ["{{role}}", "{{profile}}"]
        self.token_help = token_help or {
            "{{role}}": "The role of the assistant (e.g. teacher, coder, mentor)",
            "{{profile}}": "Profile of the user (background info to tailor responses)",
            "{{date}}": "Current date",
            "{{username}}": "The user’s name"
        }
        self.max_suggestions = max_suggestions

        self.var = self["textvariable"] or tk.StringVar()
        self.configure(textvariable=self.var)

        self.popup = tk.Toplevel(master)
        self.popup.withdraw()
        self.popup.overrideredirect(True)
        self.listbox = tk.Listbox(self.popup, height=0, exportselection=False)
        self.listbox.pack(fill="both", expand=True)

        self.tooltip = Tooltip(self.listbox, "")
        self.listbox.bind("<Motion>", self._on_hover)
        self.listbox.bind("<Leave>", lambda e: self.tooltip.hide())
        self.listbox.bind("<<ListboxSelect>>", self._choose_suggestion)

        self.var.trace_add("write", self._update_suggestions)
        self.bind("<Down>", self._move_down)
        self.bind("<Up>", self._move_up)
        self.bind("<Return>", self._select_active)
        self.bind("<Escape>", lambda e: self.popup.withdraw())
        self.bind("<FocusOut>", lambda e: self.popup.withdraw())

        self.active_index = -1

    def _update_suggestions(self, *args):
        text = self.var.get()
        cursor_pos = self.index(tk.INSERT)

        if text[:cursor_pos].endswith("{{"):
            matches = self.tokens
        else:
            prefix = text.lower()
            matches = [v for v in self.values if prefix in v.lower()]

        self._show_popup(matches)

    def _show_popup(self, matches: list[str]):
        self.listbox.delete(0, tk.END)
        if not matches:
            self.popup.withdraw()
            return

        for m in matches[:self.max_suggestions]:
            self.listbox.insert(tk.END, m)

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self.popup.geometry(f"{self.winfo_width()}x{min(len(matches), self.max_suggestions)*20}+{x}+{y}")
        self.popup.deiconify()
        self.active_index = -1

    def _move_down(self, event=None):
        if self.listbox.size() == 0: return
        self.active_index = (self.active_index + 1) % self.listbox.size()
        self.listbox.select_clear(0, tk.END)
        self.listbox.select_set(self.active_index)
        self.listbox.activate(self.active_index)
        self._update_tooltip_for_index(self.active_index)

    def _move_up(self, event=None):
        if self.listbox.size() == 0: return
        self.active_index = (self.active_index - 1) % self.listbox.size()
        self.listbox.select_clear(0, tk.END)
        self.listbox.select_set(self.active_index)
        self.listbox.activate(self.active_index)
        self._update_tooltip_for_index(self.active_index)

    def _select_active(self, event=None):
        if self.listbox.size() > 0 and self.active_index >= 0:
            chosen = self.listbox.get(self.active_index)
            self._insert_token(chosen)
        self.popup.withdraw()
        self.tooltip.hide()

    def _choose_suggestion(self, event=None):
        sel = self.listbox.curselection()
        if sel:
            chosen = self.listbox.get(sel[0])
            self._insert_token(chosen)
        self.popup.withdraw()
        self.tooltip.hide()

    def _insert_token(self, token: str):
        pos = self.index(tk.INSERT)
        current = self.var.get()
        before, after = current[:pos], current[pos:]
        if before.endswith("{{"):
            before = before[:-2]
        self.var.set(before + token + after)
        self.icursor(len(before) + len(token))

    def _on_hover(self, event):
        index = self.listbox.nearest(event.y)
        self._update_tooltip_for_index(index)

    def _update_tooltip_for_index(self, index):
        if index >= 0 and index < self.listbox.size():
            value = self.listbox.get(index)
            if value in self.token_help:
                x = self.popup.winfo_rootx() + self.listbox.winfo_width() + 10
                y = self.popup.winfo_rooty() + index * 20
                self.tooltip.set_text(self.token_help[value])
                self.tooltip.show(x, y)
            else:
                self.tooltip.hide()
        else:
            self.tooltip.hide()

    def set_values(self, values: list[str]):
        self.values = sorted(values or [], key=str.lower)

# ---------------- LegacyWelcomeDialog ----------------
class LegacyWelcomeDialog(tk.Toplevel):
    def __init__(self, master, message: str, on_close):
        super().__init__(master)
        self.title("Welcome ✨ (Legacy)")
        self.resizable(False, False)
        self.configure(padx=16, pady=16)

        w, h = 560, 420
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (w // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")

        ttk.Label(self, text="TaylorMade Prompt Library", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0,8))

        frame = ttk.Frame(self); frame.pack(fill="both", expand=True)
        txt = tk.Text(frame, wrap="word")
        txt.insert("1.0", message or "Welcome!")
        txt.configure(state="disabled")
        txt.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        btns_top = ttk.Frame(self); btns_top.pack(fill="x", pady=(10,4))
        ttk.Button(btns_top, text="Add Prompt (Wizard)", command=lambda: messagebox.showinfo("Info", "global_add placeholder")).pack(side="left")
        ttk.Button(btns_top, text="Create New Category", command=lambda: messagebox.showinfo("Info", "new_category placeholder")).pack(side="left", padx=6)
        ttk.Button(btns_top, text="Open Library File", command=lambda: messagebox.showinfo("Info", "open_db_location placeholder")).pack(side="left", padx=6)

        self.var_dont_show = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Don’t show this again", variable=self.var_dont_show).pack(anchor="w", pady=(8,6))

        btns_bottom = ttk.Frame(self); btns_bottom.pack(fill="x")
        def _docs():
            messagebox.showinfo("Learn more", "Tip: Use tokens like {{role}} and profiles to resolve ambiguity fast.\nYou can edit defaults in the Wizard or per prompt.")
        ttk.Button(btns_bottom, text="Learn token & profile tips", command=_docs).pack(side="left")
        ttk.Button(btns_bottom, text="Let’s go →", command=self._close).pack(side="right")

        self._on_close = on_close
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _close(self):
        self._on_close(self.var_dont_show.get())
        self.destroy()

# ---------------- WelcomeDialog (Enhanced) ----------------
class WelcomeDialog(tk.Toplevel):
    def __init__(self, master, message: str, on_close, categories: list[str] = None, prompts: list[str] = None):
        super().__init__(master)
        self.title("Welcome ✨")
        self.resizable(False, False)
        self.configure(padx=20, pady=20)

        w, h = 640, 520
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (w // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")

        ttk.Label(self, text="TaylorMade Prompt Library", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0,10))

        frame = ttk.LabelFrame(self, text="📖 About")
        frame.pack(fill="both", expand=True, pady=(0,12))
        txt = tk.Text(frame, wrap="word", height=8)
        txt.insert("1.0", message or "Welcome!")
        txt.configure(state="disabled", relief="flat", bg=self.cget("bg"))
        txt.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        sb = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        quick = ttk.LabelFrame(self, text="✨ Quick Start")
        quick.pack(fill="x", pady=(0,12))

        ttk.Label(quick, text="Category:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.entry_category = AutocompleteEntry(quick, values=categories or [])
        self.entry_category.grid(row=0, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(quick, text="Prompt:").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.entry_prompt = AutocompleteEntry(
            quick,
            values=prompts or [],
            tokens=["{{role}}", "{{profile}}", "{{date}}", "{{username}}"],
            token_help={
                "{{role}}": "The role of the assistant (e.g. teacher, coder, mentor)",
                "{{profile}}": "Profile of the user (background info to tailor responses)",
                "{{date}}": "Current date",
                "{{username}}": "The user’s name"
            }
        )
        self.entry_prompt.grid(row=1, column=1, sticky="ew", padx=6, pady=4)

        ttk.Button(quick, text="➕ Add Prompt (Wizard)", command=self._add_prompt).grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=4
        )
        ttk.Button(quick, text="📂 Open Library File", command=self._open_library).grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=6, pady=4
        )

        quick.columnconfigure(1, weight=1)

        self.var_dont_show = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Don’t show this again", variable=self.var_dont_show).pack(anchor="w", pady=(4,6))

        footer = ttk.Frame(self); footer.pack(fill="x")
        ttk.Button(footer, text="Learn token & profile tips", command=lambda: messagebox.showinfo(
            "Tips", "Use {{role}} and profiles to resolve ambiguity.\nEdit defaults in the Wizard or per prompt."
        )).pack(side="left")
        ttk.Button(footer, text="Let’s go →", command=self._close).pack(side="right")

        self._on_close = on_close
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _add_prompt(self):
        data = load_data()
        category = self.entry_category.get().strip()
        prompt = self.entry_prompt.get().strip()

        if category and category not in data["categories"]:
            data["categories"].append(category)
        if prompt and prompt not in data["prompts"]:
            data["prompts"].append(prompt)

        save_data(data)
        messagebox.showinfo("Saved", "Prompt and category saved!")
        self.entry_category.set_values(data["categories"])
        self.entry_prompt.set_values(data["prompts"])

    def _open_library(self):
        if os.path.exists(DB_FILE):
            os.startfile(DB_FILE)
        else:
            messagebox.showwarning("Not Found", "No library file exists yet.")

    def _close(self):
        self._on_close(self.var_dont_show.get())
        self.destroy()

# ---------------- Demo ----------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    def on_close(dont_show):
        print("Dialog closed. Don’t show again:", dont_show)

    data = load_data()
    # Show enhanced dialog by default
    dlg = WelcomeDialog(root, "Welcome to the Prompt Wizard!", on_close,
                        categories=data["categories"], prompts=data["prompts"])

    # To test the legacy version instead, uncomment:
    # dlg = LegacyWelcomeDialog(root, "Welcome to the old dialog!", on_close)

    root.mainloop()
