# 🏰 Éditeur de Cartes Dark Fantasy (Compatible VTT)

![Badge Licence](https://img.shields.io/badge/License-MIT-yellow.svg)
![Badge Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Badge Pygame](https://img.shields.io/badge/Made%20with-Pygame-red.svg)
![Badge VTT](https://img.shields.io/badge/Export-.dd2vtt-green.svg)

> **Un créateur de cartes léger et immersif pour les Maîtres du Jeu.**
> Créez des battlemaps en quelques secondes et exportez-les directement vers FoundryVTT, Roll20 ou d'autres Tables Virtuelles (VTT) avec les murs et les collisions pré-configurés.

---

## 📸 Captures d'écran

<p align="center">
  <img src="LIEN_DE_VOTRE_IMAGE_ICI.png" alt="Interface Principale" width="800">
</p>

| Système de Murs | Interface Immersive |
| :---: | :---: |
| <img src="LIEN_GIF_MURS.gif" width="400"> | <img src="LIEN_IMAGE_UI.png" width="400"> |

---

## ✨ Fonctionnalités Clés

* **🎨 Système de Tuiles :** Glissez-déposez facilement des textures sur une grille (64x64px).
* **🧱 Murs Dynamiques :** Tracez des murs qui bloquent la ligne de vue (LOS). L'export conserve ces données !
* **🌍 Export Universel VTT (.dd2vtt) :** Génère un fichier contenant l'image ET les données des murs. Importez-le dans FoundryVTT (via *Universal Battlemap Importer*) et votre carte est jouable instantanément.
* **🌑 Interface Dark Fantasy :** Une UI élégante et non intrusive conçue pour rester dans l'ambiance.
* **🏗️ Gestion des Couches :** Couches Sol, Objets et Pions indépendantes.
* **💾 Sauvegarde & Chargement :** Sauvegardez vos projets en JSON pour les modifier plus tard.
* **🖱️ Ergonomie :** Scroll vertical pour les assets, historique Undo/Redo (30 actions) et "Mode Immersion" plein écran.

---

## 🚀 Installation & Utilisation

### Option 1 : Pour les Utilisateurs (Windows)
1.  Allez dans l'onglet [Releases](https://github.com/VOTRE_PSEUDO/VOTRE_REPO/releases).
2.  Téléchargez le dernier fichier `.zip`.
3.  Extrayez-le n'importe où sur votre ordinateur.
4.  Lancez `MapEditor_Fantasy_Bundled.exe`.
5.  *C'est tout ! Pas besoin d'installer Python.*

### Option 2 : Pour les Développeurs (Python)
1.  Clonez ce dépôt :
    ```bash
    git clone [https://github.com/VOTRE_PSEUDO/VOTRE_REPO.git](https://github.com/VOTRE_PSEUDO/VOTRE_REPO.git)
    cd VOTRE_REPO
    ```
2.  Installez les dépendances :
    ```bash
    pip install pygame
    ```
3.  Lancez l'éditeur :
    ```bash
    python main.py
    ```

### 🛠️ Compilation (Créer l'exécutable)
Si vous souhaitez générer votre propre fichier `.exe`, lancez simplement le script de build inclus :
```bash
python build_bundled.py
