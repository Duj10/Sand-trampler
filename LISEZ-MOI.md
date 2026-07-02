# Tramplers Manager

Petite appli pour gérer tes tramplers du jeu **Sand** (Hologryph) : bibliothèque
locale, import rapide vers le dossier du jeu, récupération des tramplers déjà
présents, export pour les partager avec d'autres joueurs.

## Pourquoi pas directement un .exe fourni ?

Je tourne sur un serveur Linux, donc je ne peux pas compiler un `.exe` Windows
moi-même — il doit être construit *sur* Windows. Mais l'étape est simple et à
faire une seule fois (2 minutes).

## Étape 1 — Installer Python (si pas déjà fait)

Télécharge Python sur https://python.org/downloads (bouton jaune "Download
Python"). Pendant l'installation, **coche bien la case "Add python.exe to
PATH"** en bas de la première fenêtre.

## Étape 2 — Générer le .exe

1. Mets `tramplers_manager.py` et `build_exe.bat` dans le même dossier.
2. Double-clique sur `build_exe.bat`.
3. Une fenêtre noire s'ouvre, installe PyInstaller, puis construit l'appli.
4. À la fin, ton exécutable est dans le dossier `dist` qui vient d'apparaître :
   **`dist\Tramplers Manager.exe`**

Tu peux déplacer ce `.exe` où tu veux (bureau, autre dossier) et le lancer par
un double-clic, sans rien installer d'autre.

## Utilisation

- **+ Importer un fichier...** : ajoute un `.wbt` (reçu d'un ami, téléchargé...)
  à ta bibliothèque locale.
- **Récupérer depuis le jeu** : scanne le dossier `Walkers` du jeu et te
  propose d'ajouter les tramplers qui s'y trouvent déjà à ta bibliothèque
  (utile pour faire une sauvegarde ou organiser ce que tu as déjà).
- **Envoyer dans le jeu** : copie le trampler sélectionné dans le dossier
  `Walkers`, prêt à apparaître dans Sand.
- **Exporter / Partager...** : copie le fichier `.wbt` ailleurs (Discord,
  clé USB, cloud...) pour le donner à quelqu'un.
- **Renommer** / **Modifier les notes** : organise ta bibliothèque comme tu veux.
- **Changer le dossier du jeu** : au cas où le dossier détecté par défaut
  (`%USERPROFILE%\AppData\LocalLow\Hologryph\Sand\Data\Walkers`) ne serait pas
  le bon sur ta machine.

Ta bibliothèque et ses fichiers sont stockés dans :
`Documents\TramplersManager\` — donc indépendants du jeu, tu ne perds rien
même si tu réinstalles Sand.

## Limite à connaître

L'appli traite les fichiers `.wbt` comme des blocs de données : elle les
copie, les renomme, les organise — mais elle ne lit pas leur contenu (le
format interne du jeu n'est pas documenté publiquement). Donc pas d'aperçu ou
de miniature du trampler dans la liste, seulement son nom et tes notes.
