#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tramplers Manager
------------------
Little desktop app to manage tramplers from the game "Sand" (Hologryph),
since the game doesn't allow sharing them natively.

Features:
  - Local library (copy + notes) independent from the game folder
  - Quick import of a trampler from library to the game folder
  - Retrieve tramplers already present in the game folder
  - Export a trampler to share (Discord, USB drive, etc.)

No external dependencies: only Python standard library (Tkinter).
"""

import json
import os
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

APP_NAME = "Tramplers Manager"

# ---------------------------------------------------------------------------
# Color palette — warm desert dusk (Sand game)
# ---------------------------------------------------------------------------
COL_BG        = "#1C1917"   # warm charcoal
COL_PANEL     = "#292524"   # stone panel
COL_PANEL_ALT = "#35302C"
COL_BORDER    = "#44403C"
COL_TEXT      = "#F5F0E8"   # sand white
COL_MUTED     = "#A8A29E"
COL_ACCENT    = "#D4A574"   # sand gold
COL_ACCENT_HV = "#B8894F"
COL_OK        = "#84A98C"   # sage green
COL_RUST      = "#C97B63"   # terracotta
COL_ROW_ALT   = "#322C28"
COL_BTN_FG    = "#1C1917"

FONT_TITLE = ("Segoe UI", 15, "bold")
FONT_SUB   = ("Segoe UI", 9)
FONT_BODY  = ("Segoe UI", 10)
FONT_MONO  = ("Consolas", 9)
FONT_BTN   = ("Segoe UI", 9, "bold")

INVALID_CHARS = r'<>:"/\\|?*'


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(f"[{re.escape(INVALID_CHARS)}]", "_", name).strip()
    return cleaned or "trampler"


def default_game_folder() -> Path:
    return Path.home() / "AppData" / "LocalLow" / "Hologryph" / "Sand" / "Data" / "Walkers"


def library_root() -> Path:
    root = Path.home() / "Documents" / "TramplersManager"
    (root / "fichiers").mkdir(parents=True, exist_ok=True)
    return root


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ---------------------------------------------------------------------------
# Storage (config + library index)
# ---------------------------------------------------------------------------
class Store:
    def __init__(self):
        self.root = library_root()
        self.files_dir = self.root / "fichiers"
        self.config_path = self.root / "config.json"
        self.index_path = self.root / "index.json"
        self.config = self._load_json(self.config_path, {"game_folder": str(default_game_folder())})
        self.index = self._load_json(self.index_path, {"items": []})

    @staticmethod
    def _load_json(path: Path, default):
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return default

    def save_config(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def save_index(self):
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)

    @property
    def game_folder(self) -> Path:
        return Path(self.config.get("game_folder") or str(default_game_folder()))

    def set_game_folder(self, path: Path):
        self.config["game_folder"] = str(path)
        self.save_config()

    def items(self):
        return self.index["items"]

    def add_item(self, source_path: Path, display_name: str, notes: str = "") -> dict:
        item_id = uuid.uuid4().hex[:12]
        stored_name = f"{item_id}.wbt"
        dest = self.files_dir / stored_name
        shutil.copy2(source_path, dest)
        record = {
            "id": item_id,
            "file": stored_name,
            "name": display_name,
            "notes": notes,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "size": dest.stat().st_size,
            "original_filename": source_path.name,
        }
        self.index["items"].append(record)
        self.save_index()
        return record

    def remove_item(self, item_id: str):
        rec = self.find(item_id)
        if not rec:
            return
        try:
            (self.files_dir / rec["file"]).unlink(missing_ok=True)
        except Exception:
            pass
        self.index["items"] = [i for i in self.index["items"] if i["id"] != item_id]
        self.save_index()

    def find(self, item_id: str):
        for i in self.index["items"]:
            if i["id"] == item_id:
                return i
        return None

    def path_of(self, item_id: str) -> Path:
        rec = self.find(item_id)
        return self.files_dir / rec["file"]

    def known_original_names(self):
        return {i.get("original_filename") for i in self.index["items"]}


# ---------------------------------------------------------------------------
# User Interface
# ---------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.store = Store()

        self.title(APP_NAME)
        self.geometry("880x560")
        self.minsize(720, 460)
        self.configure(bg=COL_BG)

        self._build_style()
        self._build_layout()
        self._refresh_table()
        self._refresh_folder_label()

    # -- styling -----------------------------------------------------------
    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=COL_BG)
        style.configure("Panel.TFrame", background=COL_PANEL)
        style.configure("Card.TFrame", background=COL_PANEL, relief="flat")
        style.configure("TLabel", background=COL_BG, foreground=COL_TEXT, font=FONT_BODY)
        style.configure("Title.TLabel", background=COL_BG, foreground=COL_TEXT, font=FONT_TITLE)
        style.configure("Sub.TLabel", background=COL_BG, foreground=COL_MUTED, font=FONT_SUB)
        style.configure("Panel.TLabel", background=COL_PANEL, foreground=COL_MUTED, font=FONT_MONO)
        style.configure("Footer.TLabel", background=COL_PANEL, foreground=COL_MUTED, font=FONT_SUB)

        style.configure("Accent.TButton", background=COL_ACCENT, foreground=COL_BTN_FG,
                         font=FONT_BTN, padding=(12, 6), borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", COL_ACCENT_HV), ("disabled", COL_BORDER)],
                  foreground=[("disabled", COL_MUTED)])

        style.configure("Ghost.TButton", background=COL_PANEL_ALT, foreground=COL_TEXT,
                         font=FONT_BODY, padding=(10, 5), borderwidth=0)
        style.map("Ghost.TButton", background=[("active", COL_ROW_ALT)])

        style.configure("Danger.TButton", background=COL_RUST, foreground=COL_BTN_FG,
                         font=FONT_BODY, padding=(10, 5), borderwidth=0)
        style.map("Danger.TButton", background=[("active", "#A86552")])

        style.configure("Treeview", background=COL_PANEL, fieldbackground=COL_PANEL,
                         foreground=COL_TEXT, rowheight=28, font=FONT_BODY, borderwidth=0)
        style.map("Treeview", background=[("selected", COL_ACCENT_HV)],
                  foreground=[("selected", COL_BTN_FG)])
        style.configure("Treeview.Heading", background=COL_PANEL_ALT, foreground=COL_MUTED,
                         font=("Segoe UI", 9, "bold"), borderwidth=0, relief="flat")
        style.configure("Vertical.TScrollbar", background=COL_PANEL_ALT,
                         troughcolor=COL_PANEL, borderwidth=0, arrowsize=12)
        style.map("Vertical.TScrollbar", background=[("active", COL_BORDER)])

    def _card(self, parent, **pack_kw):
        outer = tk.Frame(parent, bg=COL_BORDER, padx=1, pady=1)
        outer.pack(**pack_kw)
        inner = ttk.Frame(outer, style="Panel.TFrame")
        inner.pack(fill="both", expand=True)
        return inner

    # -- layout ------------------------------------------------------------
    def _build_layout(self):
        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", padx=24, pady=(20, 12))

        ttk.Label(header, text="Tramplers Manager", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Local library for your Sand game tramplers",
                  style="Sub.TLabel").pack(anchor="w", pady=(4, 0))

        folder_card = self._card(self, fill="x", padx=24, pady=(0, 12))
        folder_row = ttk.Frame(folder_card, style="Panel.TFrame")
        folder_row.pack(fill="x", padx=12, pady=10)

        self.folder_status = tk.Label(folder_row, text="●", bg=COL_PANEL, fg=COL_MUTED,
                                       font=("Segoe UI", 10))
        self.folder_status.pack(side="left", padx=(0, 8))
        self.folder_label = tk.Label(folder_row, text="", bg=COL_PANEL, fg=COL_MUTED,
                                      font=FONT_MONO, anchor="w")
        self.folder_label.pack(side="left", fill="x", expand=True)

        folder_btns = ttk.Frame(folder_row, style="Panel.TFrame")
        folder_btns.pack(side="right")
        ttk.Button(folder_btns, text="Open", style="Ghost.TButton",
                   command=self.open_game_folder).pack(side="right", padx=(6, 0))
        ttk.Button(folder_btns, text="Change folder", style="Ghost.TButton",
                   command=self.change_game_folder).pack(side="right")

        table_card = self._card(self, fill="both", expand=True, padx=24, pady=(0, 12))
        table_frame = ttk.Frame(table_card, style="Panel.TFrame")
        table_frame.pack(fill="both", expand=True, padx=8, pady=8)

        columns = ("name", "added", "size", "notes")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Name")
        self.tree.heading("added", text="Added on")
        self.tree.heading("size", text="Size")
        self.tree.heading("notes", text="Notes")
        self.tree.column("name", width=260, anchor="w")
        self.tree.column("added", width=140, anchor="w")
        self.tree.column("size", width=90, anchor="w")
        self.tree.column("notes", width=280, anchor="w")
        self.tree.pack(fill="both", expand=True, side="left")
        self.tree.bind("<Double-1>", lambda e: self.rename_selected())

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview,
                                   style="Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        actions = ttk.Frame(self, style="TFrame")
        actions.pack(fill="x", padx=24, pady=(0, 12))

        left_actions = ttk.Frame(actions, style="TFrame")
        left_actions.pack(side="left")
        ttk.Button(left_actions, text="Import file…", style="Accent.TButton",
                   command=self.import_file).pack(side="left", padx=(0, 6))
        ttk.Button(left_actions, text="From game", style="Ghost.TButton",
                   command=self.load_from_game).pack(side="left")

        right_actions = ttk.Frame(actions, style="TFrame")
        right_actions.pack(side="right")
        ttk.Button(right_actions, text="Delete", style="Danger.TButton",
                   command=self.delete_selected).pack(side="right", padx=(6, 0))
        ttk.Button(right_actions, text="Export", style="Ghost.TButton",
                   command=self.export_selected).pack(side="right", padx=(6, 0))
        ttk.Button(right_actions, text="Notes", style="Ghost.TButton",
                   command=self.edit_notes_selected).pack(side="right", padx=(6, 0))
        ttk.Button(right_actions, text="Rename", style="Ghost.TButton",
                   command=self.rename_selected).pack(side="right", padx=(6, 0))
        ttk.Button(right_actions, text="Send to game", style="Accent.TButton",
                   command=self.send_to_game).pack(side="right", padx=(6, 0))

        footer = tk.Frame(self, bg=COL_PANEL, height=32)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        self.status = tk.StringVar(value=f"Library: {self.store.root}")
        ttk.Label(footer, textvariable=self.status, style="Footer.TLabel").pack(
            side="left", padx=24, pady=8)

    # -- UI helpers -------------------------------------------------------
    def _refresh_folder_label(self):
        exists = self.store.game_folder.exists()
        self.folder_status.configure(fg=COL_OK if exists else COL_RUST)
        status = "Connected" if exists else "Not found"
        self.folder_label.configure(
            text=f"{status}  ·  {self.store.game_folder}",
            fg=COL_TEXT if exists else COL_MUTED,
        )

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for i, rec in enumerate(sorted(self.store.items(), key=lambda r: r["added_at"], reverse=True)):
            self.tree.insert("", "end", iid=rec["id"],
                              values=(rec["name"], rec["added_at"], human_size(rec["size"]), rec.get("notes", "")))
        self.status.set(f"{len(self.store.items())} trampler(s) in library - {self.store.root}")

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(APP_NAME, "First select a trampler from the list.")
            return None
        return sel[0]

    # -- actions ----------------------------------------------------------
    def import_file(self):
        paths = filedialog.askopenfilenames(
            title="Choose one or more .wbt files",
            filetypes=[("Sand Trampler", "*.wbt"), ("All files", "*.*")],
        )
        if not paths:
            return
        added = 0
        for p in paths:
            src = Path(p)
            name = simpledialog.askstring(
                APP_NAME, f"Name for this trampler:", initialvalue=src.stem
            )
            if name is None:
                continue
            self.store.add_item(src, name.strip() or src.stem)
            added += 1
        if added:
            self._refresh_table()
            messagebox.showinfo(APP_NAME, f"{added} trampler(s) added to library.")

    def load_from_game(self):
        folder = self.store.game_folder
        if not folder.exists():
            messagebox.showwarning(APP_NAME, "Game folder not found. Change it first.")
            return
        wbt_files = sorted(folder.glob("*.wbt"))
        if not wbt_files:
            messagebox.showinfo(APP_NAME, "No .wbt files found in this folder.")
            return

        known = self.store.known_original_names()
        picker = tk.Toplevel(self)
        picker.title("Retrieve from game")
        picker.configure(bg=COL_BG)
        picker.geometry("420x420")

        ttk.Label(picker, text="Select tramplers to copy to your library:",
                  style="TLabel").pack(anchor="w", padx=14, pady=(14, 6))

        list_frame = ttk.Frame(picker, style="Panel.TFrame")
        list_frame.pack(fill="both", expand=True, padx=14)
        listbox = tk.Listbox(list_frame, selectmode="extended", bg=COL_PANEL, fg=COL_TEXT,
                              selectbackground=COL_ACCENT_HV, selectforeground=COL_BTN_FG,
                              font=FONT_BODY, borderwidth=0, highlightthickness=0)
        listbox.pack(fill="both", expand=True, padx=2, pady=2)
        for f in wbt_files:
            tag = "  (already in library)" if f.name in known else ""
            listbox.insert("end", f"{f.name}{tag}")

        def do_import():
            sel = listbox.curselection()
            count = 0
            for idx in sel:
                f = wbt_files[idx]
                self.store.add_item(f, f.stem)
                count += 1
            picker.destroy()
            if count:
                self._refresh_table()
                messagebox.showinfo(APP_NAME, f"{count} trampler(s) recupere(s).")

        btn_row = ttk.Frame(picker, style="TFrame")
        btn_row.pack(fill="x", padx=14, pady=12)
        ttk.Button(btn_row, text="Cancel", style="Ghost.TButton", command=picker.destroy).pack(side="right")
        ttk.Button(btn_row, text="Import selection", style="Accent.TButton",
                   command=do_import).pack(side="right", padx=(0, 8))

    def rename_selected(self):
        item_id = self._selected_id()
        if not item_id:
            return
        rec = self.store.find(item_id)
        new_name = simpledialog.askstring(APP_NAME, "New name:", initialvalue=rec["name"])
        if new_name:
            rec["name"] = new_name.strip()
            self.store.save_index()
            self._refresh_table()

    def edit_notes_selected(self):
        item_id = self._selected_id()
        if not item_id:
            return
        rec = self.store.find(item_id)
        new_notes = simpledialog.askstring(APP_NAME, "Notes:", initialvalue=rec.get("notes", ""))
        if new_notes is not None:
            rec["notes"] = new_notes.strip()
            self.store.save_index()
            self._refresh_table()

    def delete_selected(self):
        item_id = self._selected_id()
        if not item_id:
            return
        rec = self.store.find(item_id)
        if messagebox.askyesno(APP_NAME, f"Delete '{rec['name']}' from library?\n"
                                          f"(The file in the game, if present, is not affected.)"):
            self.store.remove_item(item_id)
            self._refresh_table()

    def export_selected(self):
        item_id = self._selected_id()
        if not item_id:
            return
        rec = self.store.find(item_id)
        dest = filedialog.asksaveasfilename(
            title="Export to...",
            initialfile=sanitize_filename(rec["name"]) + ".wbt",
            defaultextension=".wbt",
            filetypes=[("Sand Trampler", "*.wbt")],
        )
        if dest:
            shutil.copy2(self.store.path_of(item_id), dest)
            messagebox.showinfo(APP_NAME, "Trampler exported. You can share it any way you want "
                                           "(Discord, USB drive, cloud...).")

    def send_to_game(self):
        item_id = self._selected_id()
        if not item_id:
            return
        rec = self.store.find(item_id)
        folder = self.store.game_folder
        if not folder.exists():
            if messagebox.askyesno(APP_NAME, "Le dossier du jeu est introuvable. Le creer maintenant ?"):
                folder.mkdir(parents=True, exist_ok=True)
            else:
                return

        target_name = sanitize_filename(rec["name"]) + ".wbt"
        target = folder / target_name
        if target.exists():
            choice = messagebox.askyesnocancel(
                APP_NAME,
                f"'{target_name}' already exists in the game folder.\n\n"
                f"Yes = replace / No = keep both (rename) / Cancel = do nothing",
            )
            if choice is None:
                return
            if choice is False:
                n = 2
                while (folder / f"{sanitize_filename(rec['name'])} ({n}).wbt").exists():
                    n += 1
                target = folder / f"{sanitize_filename(rec['name'])} ({n}).wbt"

        shutil.copy2(self.store.path_of(item_id), target)
        messagebox.showinfo(APP_NAME, f"Trampler sent to game:\n{target.name}\n\n"
                                       f"Restart Sand to see it appear.")

    def change_game_folder(self):
        chosen = filedialog.askdirectory(
            title="Choose the game's Walkers folder",
            initialdir=str(self.store.game_folder if self.store.game_folder.exists() else Path.home()),
        )
        if chosen:
            self.store.set_game_folder(Path(chosen))
            self._refresh_folder_label()

    def open_game_folder(self):
        folder = self.store.game_folder
        if not folder.exists():
            messagebox.showwarning(APP_NAME, "This folder does not exist.")
            return
        try:
            os.startfile(folder)  # Windows only
        except AttributeError:
            messagebox.showinfo(APP_NAME, str(folder))


if __name__ == "__main__":
    App().mainloop()
