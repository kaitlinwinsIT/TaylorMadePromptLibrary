#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk

# ---------------- Persistence Helpers ----------------
DB_FILE = "DesignerPromptLibrary.json"

# ---------------- Data Management ----------------
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load saved library: {e}\nUsing defaults.")
    return {"categories": {}}

def save_data(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save library: {e}")

# ---------------- Pager Library App ----------------
class PagerLibraryApp(tk.Tk):
    def __init__(self, background_path=None):
        super().__init__()
        self.title("Taylor Made Prompt Library ✨ - 64-bit Pager")
        self.geometry("1200x800")
        self.configure(bg="#000000")

        # Load background image if provided
        self.bg_photo = None
        if background_path and os.path.exists(background_path):
            try:
                self.bg_image = Image.open(background_path)
                self.bg_image = self.bg_image.resize((1200, 800), Image.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(self.bg_image)
                self.bg_label = tk.Label(self, image=self.bg_photo)
                self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception:
                self.configure(bg="#000000")
        else:
            self.configure(bg="#000000")

        # Overlay frame for UI
        self.overlay = tk.Frame(self, bg="#000000", highlightthickness=2, highlightbackground="#00FF7F")
        self.overlay.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.85)

        # Load data
        raw_data = load_data()
        self.data = raw_data.get("categories", {})
        self.categories = list(self.data.keys())
        self.total_pages = 64
        while len(self.categories) < self.total_pages:
            self.categories.append(f"Empty Slot {len(self.categories)+1}")

        self.current_page = 0
        self.page_frame = None

        # Navigation buttons + status
        nav_frame = tk.Frame(self, bg="#000000")
        nav_frame.pack(side="bottom", fill="x", pady=10)

        self.prev_btn = tk.Button(nav_frame, text="◀ PREV", command=self.prev_page,
                                  bg="#111111", fg="#00FF7F", font=("Courier New", 14, "bold"))
        self.prev_btn.pack(side="left", padx=20)

        self.page_label = tk.Label(nav_frame, text="", bg="#000000", fg="#00FF7F", font=("Courier New", 14, "bold"))
        self.page_label.pack(side="left", expand=True)

        self.next_btn = tk.Button(nav_frame, text="NEXT ▶", command=self.next_page,
                                  bg="#111111", fg="#00FF7F", font=("Courier New", 14, "bold"))
        self.next_btn.pack(side="right", padx=20)

        # Keyboard bindings
        self.bind("<Left>", lambda e: self.prev_page())
        self.bind("<Right>", lambda e: self.next_page())
        self.bind("a", lambda e: self.prev_page())
        self.bind("d", lambda e: self.next_page())

        # Show main welcome page first
        self.show_main_page()

    def show_main_page(self):
        if self.page_frame:
            self.page_frame.destroy()
        self.page_frame = tk.Frame(self.overlay, bg="#000000")

        greeting = tk.Label(self.page_frame, text="Welcome back, User ✨", bg="#000000", fg="#00FF7F", font=("Courier New", 18, "bold"))
        greeting.pack(pady=(10, 5))

        info = tk.Label(self.page_frame, text="Browse categories, explore prompts, or add your own.", bg="#000000", fg="#00FF7F", font=("Courier New", 12))
        info.pack(pady=(0, 10))

        # Category list
        category_list = tk.Listbox(self.page_frame, width=60, bg="#111111", fg="#00FF7F", font=("Courier New", 12))
        category_list.pack(fill="both", expand=True, padx=10, pady=10)

        for i, cat in enumerate(self.categories):
            category_list.insert(tk.END, f"{i+1}. {cat}")

        def open_category(event):
            selection = category_list.curselection()
            if selection:
                idx = selection[0]
                self.show_page(idx, animate=False)
                self.current_page = idx

        category_list.bind("<Double-1>", open_category)

        # Add new prompt button
        add_btn = tk.Button(self.page_frame, text="➕ Add New Prompt", command=self.add_prompt,
                            bg="#111111", fg="#00FF7F", font=("Courier New", 14, "bold"))
        add_btn.pack(pady=10)

        self.page_frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.85)
        self.page_label.config(text="Main Page")

    def add_prompt(self):
        # Simple popup form for new prompt
        popup = tk.Toplevel(self)
        popup.title("Add New Prompt")
        popup.configure(bg="#000000")
        popup.geometry("500x500")

        entries = {}
        fields = ["title", "description", "text", "use_case", "tags", "category", "version", "date"]

        for field in fields:
            lbl = tk.Label(popup, text=field.capitalize(), bg="#000000", fg="#00FF7F", font=("Courier New", 12))
            lbl.pack(pady=(5,0))
            ent = tk.Entry(popup, width=50, bg="#111111", fg="#00FF7F", insertbackground="#00FF7F", font=("Courier New", 12))
            ent.pack(pady=(0,5))
            entries[field] = ent

        def save_new():
            prompt = {f: entries[f].get() for f in fields}
            prompt["tags"] = [t.strip() for t in prompt["tags"].split(",") if t.strip()]

            cat = prompt.get("category", "Uncategorized")
            if cat not in self.data:
                self.data[cat] = []
                if cat not in self.categories:
                    self.categories.append(cat)

            self.data[cat].append(prompt)
            save_data({"categories": self.data})
            messagebox.showinfo("Success", "New prompt added!")
            popup.destroy()
            self.show_main_page()

        save_btn = tk.Button(popup, text="Save Prompt", command=save_new,
                             bg="#111111", fg="#00FF7F", font=("Courier New", 14, "bold"))
        save_btn.pack(pady=10)

    def show_page(self, index, animate=True, direction=1):
        if self.page_frame:
            self.page_frame.destroy()
            self.page_frame = None

        self.page_frame = self.create_page(index)
        self.page_frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.85)
        self.page_label.config(text=f"Page {index+1} / {self.total_pages}")

    def create_page(self, index):
        frame = tk.Frame(self.overlay, bg="#000000")

        category = self.categories[index]
        prompts = self.data.get(category, []) if isinstance(self.data, dict) else []

        category_label = tk.Label(frame, text=category, bg="#000000", fg="#00FF7F", font=("Courier New", 16, "bold"))
        category_label.pack(pady=(10, 5))

        prompt_list = tk.Listbox(frame, width=80, bg="#111111", fg="#00FF7F", font=("Courier New", 12))
        prompt_list.pack(fill="both", expand=True, padx=10, pady=10)

        if isinstance(prompts, list):
            for prompt in prompts:
                title = prompt.get("title", "Untitled")
                category_type = prompt.get("category", "")
                icon = ""
                if category_type.lower() == "technical":
                    icon = "🟢 "
                elif category_type.lower() == "research":
                    icon = "🔵 "
                elif category_type.lower() == "creative":
                    icon = "🟣 "
                prompt_list.insert(tk.END, f"{icon}{title}")

        def open_popup(event):
            selection = prompt_list.curselection()
            if selection and isinstance(prompts, list):
                idx = selection[0]
                prompt_obj = prompts[idx]

                popup = tk.Toplevel(self)
                popup.title(prompt_obj.get("title", "Prompt"))
                popup.configure(bg="#000000")
                popup.geometry("700x500")

                text_frame = tk.Frame(popup, bg="#000000")
                text_frame.pack(fill="both", expand=True, padx=10, pady=10)

                scrollbar = tk.Scrollbar(text_frame)
                scrollbar.pack(side="right", fill="y")

                text_area = tk.Text(
                    text_frame,
                    wrap="word",
                    bg="#111111",
                    fg="#00FF7F",
                    insertbackground="#00FF7F",
                    font=("Courier New", 12),
                    yscrollcommand=scrollbar.set
                )
                text_area.pack(fill="both", expand=True)
                scrollbar.config(command=text_area.yview)

                title = prompt_obj.get("title", "Untitled")
                desc = prompt_obj.get("description", "— Not Provided —")
                text = prompt_obj.get("text", "— Not Provided —")
                use_case = prompt_obj.get("use_case", "— Not Provided —")
                tags = ", ".join(prompt_obj.get("tags", [])) or "— None —"
                version = prompt_obj.get("version", "1.0")
                date = prompt_obj.get("date", "Unknown Date")

                formatted = (
                    f"Title: {title}\n\n"
                    f"Description: {desc}\n\n"
                    f"Prompt Text:\n{text}\n\n"
                    f"Suggested Use Case: {use_case}\n\n"
                    f"Tags/Keywords: {tags}\n\n"
                    f"Version: {version} | Last Updated: {date}\n"
                )

                text_area.insert("1.0", formatted)
                text_area.config(state="disabled")

                def close_popup(event=None):
                    popup.destroy()
                def scroll_up(event=None):
                    text_area.yview_scroll(-3, "units")
                def scroll_down(event=None):
                    text_area.yview_scroll(3, "units")
                def page_up(event=None):
                    text_area.yview_scroll(-1, "pages")
                def page_down(event=None):
                    text_area.yview_scroll(1, "pages")

                popup.bind("<Escape>", close_popup)
                popup.bind("<Up>", scroll_up)
                popup.bind("<Down>", scroll_down)
                popup.bind("<Prior>", page_up)
                popup.bind("<Next>", page_down)

        prompt_list.bind("<Double-1>", open_popup)

        return frame

    def prev_page(self):
        new_index = (self.current_page - 1) % self.total_pages
        self.show_page(new_index, animate=False)
        self.current_page = new_index

    def next_page(self):
        new_index = (self.current_page + 1) % self.total_pages
        self.show_page(new_index, animate=False)
        self.current_page = new_index

# ---------------- Run App ----------------
def main():
    bg_path = os.path.join(os.path.dirname(__file__), "57e85c78-337b-45ea-90bc-159a7ab4cfa9.png")
    app = PagerLibraryApp(bg_path)
    app.mainloop()

if __name__ == "__main__":
    main()