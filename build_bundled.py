import PyInstaller.__main__
import shutil
import os
import sys

# --- CONFIGURATION ---
MAIN_SCRIPT = "MapDungeon.py"
EXE_NAME = "MapDungeon"
# Le nom du dossier à inclure DANS l'exe
ASSET_FOLDER = "Neutral Stone"

# Dossiers de travail PyInstaller
DIST_FOLDER = "dist"
BUILD_FOLDER = "build"

def build():
    # 1. Vérifications préalables
    if not os.path.exists(MAIN_SCRIPT):
        print(f"ERREUR : '{MAIN_SCRIPT}' introuvable !")
        return
    if not os.path.exists(ASSET_FOLDER):
         print(f"ERREUR CRITIQUE : Le dossier d'images '{ASSET_FOLDER}' est absent !")
         print("La compilation va échouer ou l'exe ne fonctionnera pas.")
         input("Appuyez sur Entrée pour annuler...")
         return

    print("========================================================")
    print("      COMPILATION AVEC ASSETS INTEGRES (ONEFILE)")
    print("========================================================")

    # 2. Nettoyage
    print(f"\n[1/3] Nettoyage des dossiers de construction...")
    if os.path.exists(DIST_FOLDER): shutil.rmtree(DIST_FOLDER)
    if os.path.exists(BUILD_FOLDER): shutil.rmtree(BUILD_FOLDER)
    spec_file = f"{EXE_NAME}.spec"
    if os.path.exists(spec_file): os.remove(spec_file)

    # 3. Compilation avec --add-data
    print(f"[2/3] Compilation et intégration des images...")
    print(f"      Intégration du dossier : {ASSET_FOLDER}")

    # Syntaxe pour Windows : "source;destination"
    # (Sur Linux/Mac ce serait ":")
    add_data_arg = f'{ASSET_FOLDER};{ASSET_FOLDER}'

    try:
        PyInstaller.__main__.run([
            MAIN_SCRIPT,
            '--onefile',            # Un seul gros fichier exe
            '--noconsole',          # Pas de fenêtre noire
            f'--name={EXE_NAME}',   # Nom du fichier final
            f'--add-data={add_data_arg}', # LA COMMANDE MAGIQUE pour inclure le dossier
        ])
    except Exception as e:
        print(f"\nERREUR CRITIQUE pendant la compilation : {e}")
        return

    # Plus besoin de copier le dossier manuellement à la fin !

    print("\n========================================================")
    print(f"      SUCCES !")
    print(f"      Votre fichier '{EXE_NAME}.exe'")
    print(f"      se trouve dans le dossier '{DIST_FOLDER}'.")
    print("      Il contient les images et peut être déplacé seul.")
    print("========================================================")


if __name__ == "__main__":
    build()
    input("\nAppuyez sur Entrée pour quitter...")