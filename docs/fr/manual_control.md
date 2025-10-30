## Contrôle manuel (`manual_control/`) — Architecture & Fonctionnement
---

### Table des matières
- [Ce que fait ce module](#what-this-module-does)
- [Langages & runtime](#languages--runtime)
  - [Bibliothèques cœur (détails)](#core-libraries-details)
- [Structure des dossiers (haut niveau)](#folder-structure-high-level)
- [Responsabilités des fichiers (résumé)](#file-responsibilities-summary)
- [Installation](#installation)
- [Commandes de main — carte geste → commande](#hand-commands--gesture--command-map)
---

### Ce que fait ce module
Ce module côté hôte implémente la **téléopération par gestes**. La webcam du PC fournit des images traitées pour détecter les **points de repère de la main** (MediaPipe). La **main droite** encode la **direction** (avant/gauche/droite/arrière/stop), et la **main gauche** contrôle la **vitesse** (distance pouce–index). Les commandes sont empaquetées en JSON et envoyées via **HTTP** à l’endpoint ESP32 `/move`. La boucle est asynchrone et **limitée en débit** pour éviter d’inonder le robot.

**Pipeline (percevoir → interpréter → commander) :**
1. **Capture caméra** (OpenCV)  
2. **Détection de la main & landmarks** (MediaPipe Hands)  
3. **Classification de gestes** (direction) + **estimation de vitesse** (main gauche)  
4. **Encodeur de commande & transport** (HTTP `POST /move`, JSON)  
5. **Visualisation** (landmarks superposés ; ESC pour quitter)

---

### Langages & runtime
- **Langage :** Python 3.10+ (testé avec 3.11)
- **Bibliothèques cœur :** `opencv-python`, `mediapipe`, `httpx`, `asyncio`
- **Interface réseau :** HTTP (JSON) vers l’ESP32 à `http://<ESP32_IP>:80/move`

#### Bibliothèques cœur (détails)

<p align="center">
  <!-- Ajoutez vos logos ici -->
  <img src="../src/vendor/opencv_logo.jpg" alt="Logo OpenCV" height="76" style="margin-right:18px;" />
  <img src="../src/vendor/mediapipe_logo.jpg" alt="Logo MediaPipe" height="60" />
</p>

- **OpenCV** — capture caméra (`VideoCapture`), conversions RGB↔BGR, fenêtre d’affichage, overlays (texte de vitesse, etc.).
- **MediaPipe Hands** — suiveur de main **21-landmark** en temps réel utilisé comme suit :
  - L’image d’entrée est inversée en **mode selfie** et convertie en **RGB**.
  - `Hands.process()` renvoie `multi_hand_landmarks` et la **latéralité** par main.
  - On extrait les landmarks pour les mains **Right** et **Left**.  
    - **Main droite → direction** via `GestureClassifier.classify_gesture()` en s’appuyant sur la logique “doigt levé/baissé” (tip vs. MCP).  
    - **Main gauche → vitesse** via `GestureClassifier.calculate_speed_from_left_hand()`, mappant la **distance pouce–index** (en pixels, normalisée par la taille de l’image) à l’intervalle `[MIN_SPEED, MAX_SPEED]`.
  - Les seuils de confiance et le nombre max de mains se règlent dans `config.py` (`MIN_DETECTION_CONFIDENCE`, `MIN_TRACKING_CONFIDENCE`, `MAX_NUM_HANDS`).

<p align="center">
  <!-- Image guide des landmarks de main -->
  <img src="../src/vendor/hand-landmarks.png" alt="Guide des landmarks de main (21 points) — MediaPipe" />
</p>

**Figure — Landmarks de la main.** Nous suivons l’indexation MediaPipe ci-dessus pour calculer l’état des doigts (tip vs. MCP) et la distance pouce–index de la main gauche utilisée pour la commande de vitesse.

---

### Structure des dossiers (haut niveau)
````

manual_control/
├─ application.py             # Orchestration du cycle de vie et boucle principale (async)
├─ camera_manager.py          # Wrapper de capture webcam (OpenCV)
├─ config.py                  # IP/port, timeouts, seuils geste/vitesse, index webcam
├─ detection_manager_base.py  # Base abstraite pour détecteurs
├─ gesture_classifier.py      # Geste → commande ; estimation vitesse main gauche
├─ hand_detector.py           # Wrapper MediaPipe Hands + utilitaires de dessin
├─ main.py                    # Point d’entrée (asyncio.run)
├─ robot_communicator.py      # Client HTTP asynchrone avec rate limiting/backoff
└─ requirements.txt           # Dépendances figées

````

> Les détails d’endpoint et de payload sont couverts dans la section API. Ci-dessous, la **finalité principale** de chaque fichier.

---

### Responsabilités des fichiers (résumé)

| Chemin | Type | Finalité principale | Classes / fonctions clés | Notes |
|---|---|---|---|---|
| `application.py` | Orchestrateur | Initialise caméra, détecteur, comms ; exécute la boucle async ; rend l’overlay | `Application`, `start_application()` | Colle centrale du module. |
| `camera_manager.py` | IO | Ouvrir/fermer la webcam ; lire des images en sécurité | `CameraManager.initialize()`, `get_frame()`, `release()` | Utilise OpenCV VideoCapture. |
| `config.py` | Config | Endpoints réseau, timeouts ; constantes de geste ; mappage vitesse ; index webcam | constants | **Définir `ESP32_IP_ADDRESS` ici.** |
| `detection_manager_base.py` | Abstraction | Interface pour détecteurs interchangeables | `DetectionManager` (ABC) | Permet des détecteurs remplaçables. |
| `gesture_classifier.py` | Logique | Main droite → direction ; distance main gauche → vitesse | `classify_gesture()`, `calculate_speed_from_left_hand()` | Seuils depuis `config.py`. |
| `hand_detector.py` | Perception | Wrapper MediaPipe Hands ; extraction de landmarks & dessin | `HandDetector.initialize()`, `process_frame()`, `get_detection_data()` | Vue selfie (flip) activée. |
| `robot_communicator.py` | Transport | Client HTTP async ; dé-duplication & limitation de débit | `RobotCommunicator.send_command()` | Poste du JSON vers `/move` ; gère les timeouts. |
| `main.py` | Entrée | Lance l’application avec `asyncio.run` | — | Exécuter `python -m manual_control.main`. |
| `requirements.txt` | Dépendances | Dépendances runtime figées pour reproductibilité | — | `opencv-python`, `mediapipe`, `httpx`, `asyncio`. |

---

### Installation

**Prérequis**
- Python **3.10+** (3.11 recommandé)
- Une **webcam** fonctionnelle
- Le robot ESP32 allumé et accessible sur votre LAN

**1) Créer et activer l’environnement (`venv_manual_control`)**

> À lancer depuis la **racine du dépôt** (parent de `manual_control/`).

**Linux/macOS**
````bash
python3 -m venv manual_control/venv_manual_control
source manual_control/venv_manual_control/bin/activate
````

**Windows (PowerShell)**

````powershell
py -3 -m venv manual_control\venv_manual_control
.\manual_control\venv_manual_control\Scripts\Activate.ps1
````

**2) Installer les dépendances**

````bash
pip install -r manual_control/requirements.txt
````

**3) Configurer endpoints & options**

* Éditez `manual_control/config.py` :

  * Définir `ESP32_IP_ADDRESS = "..."` (IP du robot)
  * Optionnel : ajuster `WEBCAM_INDEX`, les confiances de détection et les seuils de mappage de vitesse.

**4) Lancer (depuis la racine du dépôt)**

````bash
python -m manual_control.main
````

* Une fenêtre OpenCV s’affiche avec les landmarks superposés.
* **ESC** pour quitter.
* Les logs console montrent les payloads JSON et les réponses HTTP.

---

### Commandes de main — carte geste → commande

Utilisez la **main DROITE** pour les commandes **directionnelles** et la **main GAUCHE** pour moduler la **vitesse** (distance pouce–index). Ajoutez les photos illustratives ci-dessous.

| Commande     | Remarques                                                            |
| ------------ | -------------------------------------------------------------------- |
| **forward**  | Les cinq doigts **baissés** (repliés).                               |
| **backward** | Pouce **levé**, les quatre autres **levés**.                         |
| **left**     | Pouce & index **levés**, autres **baissés**.                         |
| **right**    | Pouce **baissé**, index–annulaire **levés**, auriculaire **baissé**. |
| **stop**     | Les cinq doigts **étendus**.                                         |

> La vitesse est calculée à partir de la **distance pouce–index de la main GAUCHE** et affichée sur l’overlay vidéo.

<img src="../src/picture3.png" alt="Exemple d’overlay / landmarks de main" />