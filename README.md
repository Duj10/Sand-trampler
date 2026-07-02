# Tramplers Manager

Little app to manage your tramplers from the game **Sand** (Hologryph): local library,
quick import to the game folder, retrieve tramplers already present, export to share
with other players.

## Step 1 — Install Python (if not already done)

Download Python from https://python.org/downloads (yellow "Download Python" button).
During installation, **make sure to check the "Add python.exe to PATH"** box at the
bottom of the first window.

## Step 2 — Generate the .exe

1. Put `tramplers_manager.py` and `build_exe.bat` in the same folder.
2. Double-click `build_exe.bat`.
3. A black window opens, installs PyInstaller, then builds the app.
4. At the end, your executable is in the `dist` folder that just appeared:
   **`dist\Tramplers Manager.exe`**

You can move this `.exe` anywhere you want (desktop, another folder) and launch it
with a double-click, without installing anything else.

## Usage

- **+ Import a file...** : adds a `.wbt` (received from a friend, downloaded...)
  to your local library.
- **Retrieve from game** : scans the game's `Walkers` folder and offers to add the
  tramplers already there to your library (useful for backup or organizing what
  you already have).
- **Send to game** : copies the selected trampler to the `Walkers` folder, ready
  to appear in Sand.
- **Export / Share...** : copies the `.wbt` file elsewhere (Discord, USB drive, cloud...)
  to give it to someone.
- **Rename** / **Edit notes** : organize your library the way you want.
- **Change game folder** : in case the auto-detected folder
  (`%USERPROFILE%\AppData\LocalLow\Hologryph\Sand\Data\Walkers`) isn't correct on your machine.

Your library and its files are stored in:
`Documents\TramplersManager\` — so independent of the game, you won't lose anything
even if you reinstall Sand.

## Known Limitation

The app treats `.wbt` files as data blocks: it copies, renames, and organizes them —
but it doesn't read their contents (the game's internal format is not publicly documented).
So no preview or thumbnail of the trampler in the list, only its name and your notes.
