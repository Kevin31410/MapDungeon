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
<img width="1282" height="832" alt="Interface Principale" src="https://github.com/user-attachments/assets/a83d08da-255c-4f78-a82d-5aa5ca6e57b8" />
</p>

| Système de Murs | Interface Immersive |
| :---: | :---: |
| <img width="1282" height="832" alt="MapDungeon1" src="https://github.com/user-attachments/assets/869c42a0-c3ee-4126-994e-fcccbad3c6d4" /> | <img width="1282" height="832" alt="immersion" src="https://github.com/user-attachments/assets/ba5fe720-516f-47b5-8dd8-ca3d0692cab0" /> |

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
4.  Lancez `MapDungeon.exe`.
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
    python MapDungeon.py
    ```
    
### 🛠️ Compilation (Créer l'exécutable)
Si vous souhaitez générer votre propre fichier `.exe`, lancez simplement le script de build inclus :
    ```bash
    python build_bundled.py
    ```
Cela créera un exécutable autonome dans le dossier dist.

## 🎮 Contrôles
_______________________________________________________________________
| Action             | Contrôle                                       |
| Poser une tuile    | Clic Gauche                                    |
| Effacer une tuile  | Outil "GOMME" + Clic Gauche                    |
| Tracer un mur      | Outil "MUR" + Glisser-Déposer                  |
| Défiler les assets | Molette Souris (sur le panneau de droite)      |
| Pivoter l'asset    | Bouton "PIVOTER" ou Interface                  |
| Mode Immersion     | Bouton "IMMERSION" (Quitter avec la croix 'X') |
| Annuler / Rétablir | Boutons en haut du menu                        |
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯

______________________________________________________________________________

## 🤝 Contribuer
Les contributions sont les bienvenues ! Si vous souhaitez ajouter des packs de textures, corriger des bugs ou ajouter des fonctionnalités (comme le brouillard de guerre) :
1.  Forkez le projet.
2.  Créez votre branche (git checkout -b feature/MaSuperFeature).
3.  Commitez vos changements (git commit -m 'Ajout de MaSuperFeature').
4.  Pushez vers la branche (git push origin feature/MaSuperFeature).
5.  Ouvrez une Pull Request.

______________________________________________________________________________

## 📜 Licence
Distribué sous la licence MIT. Voir le fichier LICENSE pour plus d'informations.

______________________________________________________________________________

<p align="center">
    Fait avec ❤️ par [VOTRE NOM] pour la communauté JDR.
</p>

