#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tramplers Manager
------------------
Petite appli de bureau pour gerer les tramplers du jeu "Sand" (Hologryph),
puisque le jeu ne permet pas de les partager nativement.

Fonctions:
  - Bibliotheque locale (copie + notes) independante du dossier du jeu
  - Import rapide d'un trampler de la bibliotheque vers le dossier du jeu
  - Recuperation des tramplers deja presents dans le dossier du jeu
  - Export d'un trampler pour le partager (Discord, cle USB, etc.)

Aucune dependance externe : uniquement la bibliotheque standard Python (Tkinter).
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
# Palette "dune au crepuscule"
# ---------------------------------------------------------------------------
COL_BG        = "#211E36"   # fond principal - indigo nuit
COL_PANEL     = "#2C2848"   # panneaux
COL_PANEL_ALT = "#332C4D"
COL_TEXT      = "#EFE3C8"   # sable pale
COL_MUTED     = "#B7A98A"
COL_GOLD      = "#D4A24C"   # accent dune
COL_GOLD_DK   = "#B4863A"
COL_TEAL      = "#5C8B89"   # succes / connecte
COL_RUST      = "#C1602D"   # danger / suppression
COL_ROW_ALT   = "#2A2646"

FONT_TITLE = ("Georgia", 18, "bold")
FONT_SUB   = ("Segoe UI", 10)
FONT_BODY  = ("Segoe UI", 10)
FONT_MONO  = ("Consolas", 9)
FONT_BTN   = ("Segoe UI", 10, "bold")

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
    for unit in ("o", "Ko", "Mo", "Go"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "o" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} To"


# ---------------------------------------------------------------------------
# Stockage (config + index bibliotheque)
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
            "original_name": source_path.name,
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
        return {i.get("original_name") for i in self.index["items"]}


# ---------------------------------------------------------------------------
# Interface
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

    # -- style -------------------------------------------------------------
    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=COL_BG)
        style.configure("Panel.TFrame", background=COL_PANEL)
        style.configure("TLabel", background=COL_BG, foreground=COL_TEXT, font=FONT_BODY)
        style.configure("Title.TLabel", background=COL_BG, foreground=COL_TEXT, font=FONT_TITLE)
        style.configure("Sub.TLabel", background=COL_BG, foreground=COL_MUTED, font=FONT_SUB)
        style.configure("Panel.TLabel", background=COL_PANEL, foreground=COL_MUTED, font=FONT_MONO)

        style.configure("Gold.TButton", background=COL_GOLD, foreground="#241D0E",
                         font=FONT_BTN, padding=8, borderwidth=0)
        style.map("Gold.TButton", background=[("active", COL_GOLD_DK)])

        style.configure("Ghost.TButton", background=COL_PANEL_ALT, foreground=COL_TEXT,
                         font=FONT_BODY, padding=7, borderwidth=0)
        style.map("Ghost.TButton", background=[("active", COL_ROW_ALT)])

        style.configure("Danger.TButton", background=COL_RUST, foreground="#241D0E",
                         font=FONT_BODY, padding=7, borderwidth=0)
        style.map("Danger.TButton", background=[("active", "#9C4A21")])

        style.configure("Treeview", background=COL_PANEL, fieldbackground=COL_PANEL,
                         foreground=COL_TEXT, rowheight=26, font=FONT_BODY, borderwidth=0)
        style.map("Treeview", background=[("selected", COL_GOLD_DK)],
                  foreground=[("selected", "#241D0E")])
        style.configure("Treeview.Heading", background=COL_PANEL_ALT, foreground=COL_MUTED,
                         font=("Segoe UI", 9, "bold"), borderwidth=0)

    # -- layout --------------------------------------------------------------
    def _build_layout(self):
        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", padx=20, pady=(18, 6))

        ttk.Label(header, text="Tramplers Manager", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Bibliotheque locale pour tes tramplers du jeu Sand",
                  style="Sub.TLabel").pack(anchor="w", pady=(2, 0))

        # ~~~ ligne "dune" decorative ~~~
        wave = tk.Canvas(self, height=10, bg=COL_BG, highlightthickness=0)
        wave.pack(fill="x", padx=20, pady=(8, 4))
        self._draw_dune(wave)

        # dossier du jeu
        folder_row = ttk.Frame(self, style="TFrame")
        folder_row.pack(fill="x", padx=20, pady=(4, 10))
        self.folder_label = ttk.Label(folder_row, text="", style="Sub.TLabel")
        self.folder_label.pack(side="left")
        ttk.Button(folder_row, text="Changer le dossier du jeu", style="Ghost.TButton",
                   command=self.change_game_folder).pack(side="right")
        ttk.Button(folder_row, text="Ouvrir le dossier du jeu", style="Ghost.TButton",
                   command=self.open_game_folder).pack(side="right", padx=(0, 8))

        # table
        table_frame = ttk.Frame(self, style="Panel.TFrame")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        columns = ("name", "added", "size", "notes")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Nom")
        self.tree.heading("added", text="Ajoute le")
        self.tree.heading("size", text="Taille")
        self.tree.heading("notes", text="Notes")
        self.tree.column("name", width=260, anchor="w")
        self.tree.column("added", width=140, anchor="w")
        self.tree.column("size", width=90, anchor="w")
        self.tree.column("notes", width=280, anchor="w")
        self.tree.pack(fill="both", expand=True, side="left")
        self.tree.bind("<Double-1>", lambda e: self.rename_selected())

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # boutons d'action
        actions = ttk.Frame(self, style="TFrame")
        actions.pack(fill="x", padx=20, pady=(0, 10))

        left_actions = ttk.Frame(actions, style="TFrame")
        left_actions.pack(side="left")
        ttk.Button(left_actions, text="+ Importer un fichier...", style="Gold.TButton",
                   command=self.import_file).pack(side="left", padx=(0, 8))
        ttk.Button(left_actions, text="Recuperer depuis le jeu", style="Ghost.TButton",
                   command=self.load_from_game).pack(side="left", padx=(0, 8))

        right_actions = ttk.Frame(actions, style="TFrame")
        right_actions.pack(side="right")
        ttk.Button(right_actions, text="Supprimer", style="Danger.TButton",
                   command=self.delete_selected).pack(side="right", padx=(8, 0))
        ttk.Button(right_actions, text="Exporter / Partager...", style="Ghost.TButton",
                   command=self.export_selected).pack(side="right", padx=(8, 0))
        ttk.Button(right_actions, text="Modifier les notes", style="Ghost.TButton",
                   command=self.edit_notes_selected).pack(side="right", padx=(8, 0))
        ttk.Button(right_actions, text="Renommer", style="Ghost.TButton",
                   command=self.rename_selected).pack(side="right", padx=(8, 0))
        ttk.Button(right_actions, text="Envoyer dans le jeu", style="Gold.TButton",
                   command=self.send_to_game).pack(side="right", padx=(8, 0))

        # barre de statut
        self.status = tk.StringVar(value=f"Bibliotheque : {self.store.root}")
        status_bar = ttk.Label(self, textvariable=self.status, style="Sub.TLabel")
        status_bar.pack(fill="x", padx=20, pady=(0, 14))

    def _draw_dune(self, canvas: tk.Canvas):
        def redraw(event=None):
            canvas.delete("all")
            w = canvas.winfo_width() or 800
            y = 5
            points = []
            step = 14
            x = 0
            up = True
            while x <= w:
                points.append((x, y - 3 if up else y + 3))
                x += step
                up = not up
            for i in range(len(points) - 1):
                canvas.create_line(*points[i], *points[i + 1], fill=COL_GOLD_DK, width=2, smooth=True)
        canvas.bind("<Configure>", redraw)

    # -- helpers UI ----------------------------------------------------------
    def _refresh_folder_label(self):
        exists = self.store.game_folder.exists()
        marker = "connecte" if exists else "introuvable - clique sur Changer le dossier du jeu"
        self.folder_label.configure(text=f"Dossier du jeu ({marker}) : {self.store.game_folder}")

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for i, rec in enumerate(sorted(self.store.items(), key=lambda r: r["added_at"], reverse=True)):
            self.tree.insert("", "end", iid=rec["id"],
                              values=(rec["name"], rec["added_at"], human_size(rec["size"]), rec.get("notes", "")))
        self.status.set(f"{len(self.store.items())} trampler(s) dans la bibliotheque - {self.store.root}")

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(APP_NAME, "Selectionne d'abord un trampler dans la liste.")
            return None
        return sel[0]

    # -- actions ---------------------------------------------------------
    def import_file(self):
        paths = filedialog.askopenfilenames(
            title="Choisir un ou plusieurs fichiers .wbt",
            filetypes=[("Trampler Sand", "*.wbt"), ("Tous les fichiers", "*.*")],
        )
        if not paths:
            return
        added = 0
        for p in paths:
            src = Path(p)
            name = simpledialog.askstring(
                APP_NAME, f"Nom a donner a ce trampler :", initialvalue=src.stem
            )
            if name is None:
                continue
            self.store.add_item(src, name.strip() or src.stem)
            added += 1
        if added:
            self._refresh_table()
            messagebox.showinfo(APP_NAME, f"{added} trampler(s) ajoute(s) a la bibliotheque.")

    def load_from_game(self):
        folder = self.store.game_folder
        if not folder.exists():
            messagebox.showwarning(APP_NAME, "Le dossier du jeu est introuvable. Change-le d'abord.")
            return
        wbt_files = sorted(folder.glob("*.wbt"))
        if not wbt_files:
            messagebox.showinfo(APP_NAME, "Aucun fichier .wbt trouve dans ce dossier.")
            return

        known = self.store.known_original_names()
        picker = tk.Toplevel(self)
        picker.title("Recuperer depuis le jeu")
        picker.configure(bg=COL_BG)
        picker.geometry("420x420")

        ttk.Label(picker, text="Selectionne les tramplers a copier dans ta bibliotheque :",
                  style="TLabel").pack(anchor="w", padx=14, pady=(14, 6))

        list_frame = ttk.Frame(picker, style="Panel.TFrame")
        list_frame.pack(fill="both", expand=True, padx=14)
        listbox = tk.Listbox(list_frame, selectmode="extended", bg=COL_PANEL, fg=COL_TEXT,
                              selectbackground=COL_GOLD_DK, selectforeground="#241D0E",
                              font=FONT_BODY, borderwidth=0, highlightthickness=0)
        listbox.pack(fill="both", expand=True, padx=2, pady=2)
        for f in wbt_files:
            tag = "  (deja dans la bibliotheque)" if f.name in known else ""
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
        ttk.Button(btn_row, text="Annuler", style="Ghost.TButton", command=picker.destroy).pack(side="right")
        ttk.Button(btn_row, text="Importer la selection", style="Gold.TButton",
                   command=do_import).pack(side="right", padx=(0, 8))

    def rename_selected(self):
        item_id = self._selected_id()
        if not item_id:
            return
        rec = self.store.find(item_id)
        new_name = simpledialog.askstring(APP_NAME, "Nouveau nom :", initialvalue=rec["name"])
        if new_name:
            rec["name"] = new_name.strip()
            self.store.save_index()
            self._refresh_table()

    def edit_notes_selected(self):
        item_id = self._selected_id()
        if not item_id:
            return
        rec = self.store.find(item_id)
        new_notes = simpledialog.askstring(APP_NAME, "Notes :", initialvalue=rec.get("notes", ""))
        if new_notes is not None:
            rec["notes"] = new_notes.strip()
            self.store.save_index()
            self._refresh_table()

    def delete_selected(self):
        item_id = self._selected_id()
        if not item_id:
            return
        rec = self.store.find(item_id)
        if messagebox.askyesno(APP_NAME, f"Supprimer '{rec['name']}' de la bibliotheque ?\n"
                                          f"(Le fichier dans le jeu, s'il y est, n'est pas touche.)"):
            self.store.remove_item(item_id)
            self._refresh_table()

    def export_selected(self):
        item_id = self._selected_id()
        if not item_id:
            return
        rec = self.store.find(item_id)
        dest = filedialog.asksaveasfilename(
            title="Exporter vers...",
            initialfile=sanitize_filename(rec["name"]) + ".wbt",
            defaultextension=".wbt",
            filetypes=[("Trampler Sand", "*.wbt")],
        )
        if dest:
            shutil.copy2(self.store.path_of(item_id), dest)
            messagebox.showinfo(APP_NAME, "Trampler exporte. Tu peux le partager comme tu veux "
                                           "(Discord, cle USB, cloud...).")

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
                f"'{target_name}' existe deja dans le dossier du jeu.\n\n"
                f"Oui = remplacer / Non = garder les deux (renommer) / Annuler = ne rien faire",
            )
            if choice is None:
                return
            if choice is False:
                n = 2
                while (folder / f"{sanitize_filename(rec['name'])} ({n}).wbt").exists():
                    n += 1
                target = folder / f"{sanitize_filename(rec['name'])} ({n}).wbt"

        shutil.copy2(self.store.path_of(item_id), target)
        messagebox.showinfo(APP_NAME, f"Trampler envoye dans le jeu :\n{target.name}\n\n"
                                       f"Relance Sand pour le voir apparaitre.")

    def change_game_folder(self):
        chosen = filedialog.askdirectory(
            title="Choisir le dossier Walkers du jeu",
            initialdir=str(self.store.game_folder if self.store.game_folder.exists() else Path.home()),
        )
        if chosen:
            self.store.set_game_folder(Path(chosen))
            self._refresh_folder_label()

    def open_game_folder(self):
        folder = self.store.game_folder
        if not folder.exists():
            messagebox.showwarning(APP_NAME, "Ce dossier n'existe pas.")
            return
        try:
            os.startfile(folder)  # Windows uniquement
        except AttributeError:
            messagebox.showinfo(APP_NAME, str(folder))


if __name__ == "__main__":
    App().mainloop()
