## Structure du dépôt

Le code est organisé en **quatre modules de haut niveau**, chacun responsable d’une partie du système. La documentation se trouve dans `docs/`; des guides détaillés par module suivent dans les sections ultérieures.

### Modules de haut niveau

- **`esp32cam_robot/` — Micrologiciel embarqué (sur le robot)**
  - Micrologiciel pour ESP32-CAM exposant **des endpoints HTTP de contrôle** et **un flux vidéo**.
  - Sous-systèmes : provisionnement Wi-Fi, serveur web et *handlers* de requêtes, pilotes moteur/LED, gestion de la caméra.
  - **Langage/Outils :** C++ (noyau Arduino pour ESP32), Arduino IDE ou PlatformIO.

- **`manual_control/` — Téléopération par gestes (hôte)**
  - Capture webcam, **détection et classification de gestes**, mappage de commandes, client HTTP vers le robot.
  - **Langage/Outils :** Python ; voir `requirements.txt` pour les dépendances vision/runtime.
  - Point d’entrée : `main.py`.

- **`auto_soccer_bot/` — Mode automatique (autonomie côté hôte)**
  - Ingestion du flux ESP32-CAM, **détection du ballon**, logique de décision (**suivi du ballon implémenté**), client HTTP.
  - Contient des poids YOLO exportés dans `models/` pour les exécutions locales.
  - **Langage/Outils :** Python ; point d’entrée `main.py`.

- **`opponent-detector/` — Entraînement et évaluation des modèles**
  - Organisation du *dataset* (`train/`, `val/`), script d’entraînement, test d’inférence et **artefacts** (courbes, matrices de confusion, poids sauvegardés).
  - **Langage/Outils :** Python avec la pile Ultralytics/YOLO (voir `requirements.txt`).

> Dossiers de support  
> - **`docs/`** : documentation multilingue (`en/`, `es/`, `fr/`).  
> - **`LICENSE` / `README.md`** : licence et aperçu global.

---

### Langages et outils

- **Micrologiciel (robot) :** C++ avec le **noyau Arduino pour ESP32** (sketch `esp32cam_robot.ino`, sources C++ sous `src/`).
- **Modules côté hôte :** **Python 3.x** pour la perception, la décision et la télémétrie.
- **Modèles/Artefacts :** Poids PyTorch `.pt`
- **Configuration & docs :** JSON/YAML, Markdown.

---

### Environnements Python (un par module côté hôte)

Pour garder des dépendances propres et reproductibles, le code côté hôte utilise **trois environnements Python isolés**—un par module Python :

1. **`auto_soccer_bot/`** — mode automatique (vision + contrôleur)  
2. **`manual_control/`** — téléopération par gestes  
3. **`opponent-detector/`** — entraînement & évaluation

Chaque module fournit son `requirements.txt`. Créez et activez l’environnement **dans le répertoire du module**.