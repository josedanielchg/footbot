## Contrôle manuel (`manual_control/`) — Architecture & Fonctionnement

### Sommaire
- [Ce que fait ce module](#ce-que-fait-ce-module)
- [Langages & environnement d’exécution](#langages--environnement-dexécution)
  - [Bibliothèques cœur (détails)](#bibliothèques-cœur-détails)
- [Arborescence (haut niveau)](#arborescence-haut-niveau)
- [Responsabilités des fichiers (résumé)](#responsabilités-des-fichiers-résumé)
- [Installation](#installation)
- [Commandes de main — correspondance geste → commande](#commandes-de-main--correspondance-geste--commande)

### Ce que fait ce module
Ce module côté hôte implémente la **téléopération par gestes**. La webcam du portable fournit des images traitées pour détecter les **repères de la main** (MediaPipe). La **main droite** encode la **direction** (avant/gauche/droite/arrière/stop) et la **main gauche** contrôle la **vitesse** (distance pouce–index). Les commandes sont envoyées en **HTTP** (JSON) vers l’endpoint `/move` de l’ESP32. La boucle est asynchrone avec **limitation de débit** pour éviter de saturer le robot.

**Pipeline (percevoir → interpréter → commander) :**
1. **Capture caméra** (OpenCV)  
2. **Détection de la main et *landmarks*** (MediaPipe Hands)  
3. **Classification du geste** (direction) + **estimation de vitesse** (main gauche)  
4. **Encodage & transport de la commande** (HTTP `POST /move`, JSON)  
5. **Visualisation** (superposition de *landmarks* ; ESC pour quitter)

---

### Langages & environnement d’exécution
- **Langage :** Python 3.10+ (testé avec 3.11)
- **Bibliothèques cœur :** `opencv-python`, `mediapipe`, `httpx`, `asyncio`
- **Interface réseau :** HTTP (JSON) vers `http://<ESP32_IP>:80/move`

#### Bibliothèques cœur (détails)

<p align="center">
  <!-- Espace pour les logos -->
  <img src="../src/vendor/opencv_logo.jpg" alt="OpenCV logo" height="76" style="margin-right:18px;" />
  <img src="../src/vendor/mediapipe_logo.jpg" alt="MediaPipe logo" height="60" />
</p>

- **OpenCV** — capture caméra (`VideoCapture`), conversions RGB↔BGR, affichage de fenêtre et superpositions (texte de vitesse, etc.).
- **MediaPipe Hands** — *tracker* de main à **21 *landmarks*** en temps réel, utilisé ainsi :
  - L’image d’entrée est inversée en **vue selfie** puis convertie en **RGB**.
  - `Hands.process()` renvoie `multi_hand_landmarks` et la **latéralité** de chaque main.
  - Nous extrayons les *landmarks* des mains **Droite** et **Gauche**.  
    - **Droite → direction** via `GestureClassifier.classify_gesture()` (logique doigt “haut/bas” en comparant pointe vs. MCP).  
    - **Gauche → vitesse** via `GestureClassifier.calculate_speed_from_left_hand()`, en mappant la **distance pouce–index** (en pixels, normalisée) vers `[MIN_SPEED, MAX_SPEED]`.
  - Seuils de confiance et nombre max. de mains dans `config.py` (`MIN_DETECTION_CONFIDENCE`, `MIN_TRACKING_CONFIDENCE`, `MAX_NUM_HANDS`).

<p align="center">
  <!-- Guide des landmarks de la main -->
  <img src="../src/vendor/hand-landmarks.png" alt="Guide des landmarks de la main (21 points)" />
</p>

**Figure — *Landmarks* de la main.** Nous suivons l’indexation MediaPipe pour déduire l’état des doigts (pointe vs. MCP) et la distance pouce–index de la main gauche utilisée pour la vitesse.

---

### Arborescence (haut niveau)
````

manual_control/
├─ application.py
├─ camera_manager.py
├─ config.py
├─ detection_manager_base.py
├─ gesture_classifier.py
├─ hand_detector.py
├─ main.py
├─ robot_communicator.py
└─ requirements.txt

````

> Les détails des endpoints et des *payloads* figurent dans la section API. Ci-dessous, le **but principal** de chaque fichier.

---

### Responsabilités des fichiers (résumé)

| Chemin | Type | But principal | Classes / fonctions clés | Remarques |
|---|---|---|---|---|
| `application.py` | Orchestrateur | Initialise caméra, détecteur et comms ; boucle asynchrone ; rendu de l’overlay | `Application`, `start_application()` | Colle centrale du module. |
| `camera_manager.py` | IO | Ouvrir/fermer la webcam ; lire des images | `initialize()`, `get_frame()`, `release()` | OpenCV `VideoCapture`. |
| `config.py` | Config | Endpoints réseau, *timeouts* ; constantes de gestes ; mappage de vitesse ; index webcam | constantes | **Définir `ESP32_IP_ADDRESS` ici.** |
| `detection_manager_base.py` | Abstraction | Interface pour détecteurs interchangeables | `DetectionManager` (ABC) | Favorise l’extensibilité. |
| `gesture_classifier.py` | Logique | Main droite → direction ; distance main gauche → vitesse | `classify_gesture()`, `calculate_speed_from_left_hand()` | Seuils dans `config.py`. |
| `hand_detector.py` | Perception | Enveloppe MediaPipe Hands ; extraction/dessin des *landmarks* | `initialize()`, `process_frame()`, `get_detection_data()` | Vue selfie activée. |
| `robot_communicator.py` | Transport | Client HTTP asynchrone ; déduplication et *rate limiting* | `send_command()` | Envoie JSON à `/move`. |
| `main.py` | Entrée | Lance l’app via `asyncio.run` | — | Exécuter `python -m manual_control.main`. |
| `requirements.txt` | Dépendances | Verrouillage du *runtime* | — | `opencv-python`, `mediapipe`, `httpx`, `asyncio`. |

---

### Installation

**Prérequis**
- Python **3.10+** (recommandé 3.11)
- Une **webcam** fonctionnelle
- Le robot ESP32 allumé et accessible sur votre réseau

**1) Créer et activer l’environnement (`venv_manual_control`)**

> Exécutez depuis la **racine du dépôt** (dossier parent de `manual_control/`).

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

**3) Configurer les endpoints & options**

* Éditez `manual_control/config.py` :

  * Définissez `ESP32_IP_ADDRESS = "..."` (IP du robot)
  * Optionnel : ajustez `WEBCAM_INDEX`, les seuils de détection et le mappage de vitesse.

**4) Exécuter (depuis la racine du dépôt)**

````bash
python -m manual_control.main
````

* Une fenêtre OpenCV s’ouvrira avec les *landmarks*.
* **ESC** pour quitter.
* La console affiche les JSON envoyés et les réponses HTTP.

---

### Commandes de main — correspondance geste → commande

Utilisez la **main DROITE** pour les **directions** et la **main GAUCHE** pour la **vitesse** (distance pouce–index). Insérez vos images ci-dessous.

| Commande     | Remarques                                                            |
| ------------ | -------------------------------------------------------------------- |
| **forward**  | Les cinq doigts **baissés** (repliés).                               |
| **backward** | Pouce **levé**, autres quatre **levés**.                             |
| **left**     | Pouce et index **levés**, autres **baissés**.                        |
| **right**    | Pouce **baissé**, index–annulaire **levés**, auriculaire **baissé**. |
| **stop**     | Les cinq doigts **étendus**.                                         |

> La vitesse est calculée à partir de la distance pouce–index de la **main gauche** et affichée sur la superposition vidéo.

<img src="../src/picture3.png" alt="Exemple de landmarks/gesture" />