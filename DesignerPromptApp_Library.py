#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import json, re
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

# now your classes can safely use tk
class WelcomeDialog(tk.Toplevel):
    ...


class WelcomeDialog(tk.Toplevel):
    def __init__(self, master, message: str, on_close):
        super().__init__(master)
        self.title("Welcome ✨")
        self.resizable(False, False)
        self.configure(padx=16, pady=16)

        # Size & center
        w, h = 560, 420
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (w // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")

        ttk.Label(self, text="TaylorMade Prompt Library", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0,8))

        # Read-only explainer text
        frame = ttk.Frame(self); frame.pack(fill="both", expand=True)
        txt = tk.Text(frame, wrap="word")
        txt.insert("1.0", message or "Welcome!")
        txt.configure(state="disabled")
        txt.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        # Quick actions
        btns_top = ttk.Frame(self); btns_top.pack(fill="x", pady=(10,4))
        ttk.Button(btns_top, text="Add Prompt (Wizard)", command=master.global_add).pack(side="left")
        ttk.Button(btns_top, text="Create New Category", command=master.new_category).pack(side="left", padx=6)
        ttk.Button(btns_top, text="Open Library File", command=master.open_db_location).pack(side="left", padx=6)

        self.var_dont_show = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Don’t show this again", variable=self.var_dont_show).pack(anchor="w", pady=(8,6))

        # Close / Learn more
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
