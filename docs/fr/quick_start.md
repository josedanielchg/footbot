# 🚀 Démarrage rapide

Cette page vous aide à passer de zéro → opérationnel en quelques minutes. Elle est organisée par sous-projet :

---
## Table des matières

- [1) `esp32cam_robot` — Flasher le firmware (Arduino IDE)](#1-esp32cam_robot--flash-the-firmware-arduino-ide)
- [2) `manual_control` — Téléopération par gestes (ordinateur portable)](#2-manual_control--hand-gesture-teleoperation-laptop)
- [3) `auto_soccer_bot` — Suivi de ballon autonome (ordinateur portable)](#3-auto_soccer_bot--autonomous-ball-follower-laptop)
- [4) `soccer_vision` — Réentraîner & tester un YOLO personnalisé (2 classes)](#4-soccer_vision--retrain--test-custom-yolo-2-classes)
- [Dépannage courant](#common-troubleshooting)
---

## 1) `esp32cam_robot` — Flasher le firmware (Arduino IDE)

### Prérequis

* **Matériel :** ESP32-CAM (AI-Thinker), **USB-série (FTDI 3,3 V)**, câbles Dupont
* **Alimentation :** 5 V vers l’ESP32-CAM (via la broche **5V**) ; **GND commun** partagé avec le FTDI
* **Hôte :** Arduino IDE **2.x** (recommandé)

### A. Installer la plateforme ESP32

1. Ouvrez **Arduino IDE** → **File → Preferences** → *Additional Boards Manager URLs*
2. **Tools → Board → Boards Manager…** → recherchez **« esp32 by Espressif Systems »** → **Install**.

### B. Sélectionner la carte et les options

* **Board :** `ESP32 Arduino → AI Thinker ESP32-CAM`
* **Upload Speed :** `115200` (valeur stable par défaut)
* **Flash Mode/Freq/Partition :** laissez par défaut
* **PSRAM :** `Enabled` (recommandé pour la caméra)

### C. Câbler l’ESP32-CAM pour le flashage

Pour plus d’infos sur le câblage cliquez [ici](hardware-power.md)
* Pour entrer en mode bootloader : avec IO0 relié à GND, appuyez une fois sur **RESET** ; gardez IO0-GND pendant l’upload.

> Après l’upload, **déconnectez IO0 de GND** et appuyez sur **RESET** pour exécuter le programme.

### D. Ouvrir le sketch & configurer le Wi-Fi / les GPIO

1. Dans Arduino IDE, ouvrez : `esp32cam_robot/esp32cam_robot.ino`
2. Renseignez votre **SSID/Mot de passe Wi-Fi** et vérifiez les définitions **GPIO / pilote moteur** (dans `config.h` ou en tête du sketch).
3. **Tools → Port :** sélectionnez le port COM du FTDI (`/dev/ttyUSB*` sous Linux, `/dev/cu.*` sous macOS, `COM*` sous Windows).

### E. Téléverser & vérifier

1. Cliquez sur **Upload**. Si vous voyez des erreurs de synchro, appuyez une fois sur **RESET** (IO0 doit être à GND).
2. À la fin : retirez **IO0–GND**, appuyez sur **RESET**.
3. Ouvrez le **Moniteur série** à **115200** bauds. L’ESP32-CAM doit afficher son **adresse IP**.
4. Tests rapides (exemples) :

   * Snapshot : `http://<ESP32_IP>:80/capture`
   * Flux MJPEG : `http://<ESP32_IP>:81/stream`
---

## 2) `manual_control` — Téléopération par gestes (ordinateur portable)

### Installation

**Prérequis**

* Python **3.10+** (3.11 recommandé)
* Une **webcam** fonctionnelle
* Le robot ESP32 sous tension et accessible sur votre LAN

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

Éditez `manual_control/config.py` :

* Définissez `ESP32_IP_ADDRESS = "..."` (IP du robot)
* Optionnel : ajustez `WEBCAM_INDEX`, les seuils de confiance et les seuils de mappage de vitesse.

**4) Lancer (depuis la racine du dépôt)**

````bash
python -m manual_control.main
````

* Une fenêtre OpenCV s’ouvre avec les repères (*landmarks*).
* Appuyez sur **ESC** pour quitter.
* La console affiche les charges utiles JSON et les réponses HTTP.

---

## 3) `auto_soccer_bot` — Suivi de ballon autonome (ordinateur portable)

### Installation

**Prérequis**

* Python **3.10+** (3.11 recommandé)
* Robot ESP32 accessible sur votre LAN et diffusant sur `http://<ESP32_IP>:81/stream`

**1) Créer et activer l’environnement (`venv_auto_soccer`)**

> Exécutez depuis la **racine du dépôt** (dossier parent de `auto_soccer_bot/`).

**Linux/macOS**

````bash
python3 -m venv auto_soccer_bot/venv_auto_soccer
source auto_soccer_bot/venv_auto_soccer/bin/activate
````

**Windows (PowerShell)**

````powershell
py -3 -m venv auto_soccer_bot\venv_auto_soccer
.\auto_soccer_bot\venv_auto_soccer\Scripts\Activate.ps1
````

**2) Installer les dépendances**

````bash
pip install -r auto_soccer_bot/requirements.txt
````

**3) Configurer**

Éditez `auto_soccer_bot/config_auto.py` :

* Définissez `ESP32_IP_ADDRESS = "..."` et ajustez les ports si nécessaire.
* Sélectionnez les poids **YOLO** dans `models/` et les seuils.
* Réglez les gains du contrôleur, le couloir cible et (optionnel) le redimensionnement à l’ingestion.

**4) Lancer (depuis la racine du dépôt)**

````bash
python -m auto_soccer_bot.main
````

* Une fenêtre de debug optionnelle affiche les détections et l’état de pilotage.
* Les logs indiquent le temps par frame, la commande choisie et les réponses HTTP.

---

## 4) `soccer_vision` — Réentraîner & tester un YOLO personnalisé (2 classes)

Ce module permet de **(ré)entraîner** YOLOv11 pour détecter **deux classes** sur le terrain : `goal` et `opponent`, puis de **faire une inférence rapide** sur images/vidéos. Il correspond au guide complet [ici](soccer_vision.md).

### Installation

**Prérequis**

* Python **3.10+** (3.11 recommandé)
* (Optionnel) GPU compatible CUDA + build PyTorch correspondant
* (Optionnel) **Label Studio** pour l’annotation si vous créez un nouveau jeu de données

**1) Créer & activer un venv (dans le module)**

> À faire **dans** le dossier `soccer_vision/`.

**Windows (PowerShell)**

````powershell
cd soccer_vision
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
````

**macOS / Linux**

````bash
cd soccer_vision
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
````

**2) Installer les dépendances**

````bash
pip install -r requirements.txt
# Optionnel : choisissez le build Torch adapté à votre machine
# Exemple GPU (CUDA 12.1) :
# pip install --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio
# CPU uniquement :
# pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
````

### Préparer le jeu de données (Label Studio → export YOLO)

1. Démarrez Label Studio :

   ````bash
   label-studio
   ````
2. Sur [http://localhost:8080](http://localhost:8080) créez un projet (ex. « Soccer Vision »), ajoutez **Bounding Box** avec les labels :

   * `goal`
   * `opponent`
3. Annotez → **Export** au format **YOLO (v5/v8/v11)**.
4. Placez l’export ici :

   ````
   soccer_vision/
     dataset/
       train/
         images/
         labels/
       # (optionnel) val/
       classes.txt   # doit contenir exactement : goal, opponent
   ````

   *Si `val/` est absent, l’entraînement créera une validation à partir de `train/`*

### Entraîner (choisissez UNE voie)

**A) Notebook (recommandé pour débuter)**

1. Lancez Jupyter depuis le **venv activé** :

   ````bash
   python -m pip install notebook ipykernel  # si manquant
   python -m notebook
   ````
2. Ouvrez `notebooks/01_retrain_yolo.ipynb` et **Run All**.
   Le notebook valide le dataset, crée `data.yaml`, définit `ULTRALYTICS_HOME`, entraîne puis copie :

   * **Meilleurs poids** → `models/yolo11s/soccer_yolo.pt`
   * **Artefacts d’entraînement** → `models/yolo11s/train_artifacts/`
   * Les graphiques sélectionnés peuvent être copiés dans `results/` pour la doc.

**B) CLI (sans interface)**

````bash
# depuis soccer_vision/ (venv actif)
python -m notebooks.modules.cli \
  --model yolo11s.pt \
  --epochs 60 \
  --imgsz 640 \
  --batch 16 \
  --train_pct 0.9 \
  --device 0          # GPU 0 (utilisez "cpu" si pas de GPU)
# Sorties :
#  - models/yolo11s/soccer_yolo.pt
#  - models/yolo11s/train_artifacts/...
#  - runs/ (exécutions Ultralytics brutes)
````

### Inférence rapide

**Notebook :** `notebooks/02_test_and_demo.ipynb` (images/vidéos → enregistre dans `runs/`).

**One-liner (Python)**

````python
from ultralytics import YOLO
m = YOLO("soccer_vision/models/yolo11s/soccer_yolo.pt")
m.predict(
    source="soccer_vision/dataset/val/images",  # ou chemin vers fichier/dossier/vidéo
    save=True,
    conf=0.86,                                  # démarrez près du pic F1 ; ajustez selon besoin
    project="soccer_vision/runs",
    name="quick_predict",
    exist_ok=True
)
````

### Où trouver les résultats

* **Poids :** `soccer_vision/models/yolo11s/soccer_yolo.pt`
* **Artefacts d’entraînement (graphiques, courbes, matrice de confusion, args) :**
  `soccer_vision/models/yolo11s/train_artifacts/`
* **Graphiques sélectionnés pour la doc :** `soccer_vision/results/`
* **Exécutions Ultralytics brutes :** `soccer_vision/runs/`

> Remarque : Vous pouvez retrouver tous les résultats du modèle entraîné en fin de documentation **Soccer Vision** : [ici](soccer_vision.md)

### Conseils & dépannage

* **Pas de split `val/` :** Le *trainer* en crée un automatiquement à partir de `train/` (déplacement par défaut).
* **GPU non utilisé :** Installez la roue Torch **adaptée à votre CUDA** (voir commandes ci-dessus) ou utilisez `--device cpu`.
* **Seuil de confiance :** Démarrez l’inférence autour de **`conf≈0.86–0.90`** (pic F1 selon la doc) puis ajustez votre compromis FP/latence.
* **Dossier `runs` volumineux :** Vous pouvez nettoyer `soccer_vision/runs/` après avoir exporté les meilleurs poids.

---

### Dépannage courant

* **Impossible d’atteindre l’IP de l’ESP32 ?** Assurez-vous que l’ESP32 et l’ordinateur sont sur le **même Wi-Fi** et que votre routeur n’isole pas les clients.
* **Le flux saccade ?** Conservez **QVGA (320×240)** et une qualité JPEG modérée dans le firmware ; utilisez les modes d’ingestion **HTTPX** dans les applis Python.
* **Échec d’upload (ESP32-CAM) ?** Réentrez en bootloader (IO0→GND + RESET), baissez **Upload Speed** à `115200`, vérifiez le croisement TX/RX et assurez une **alimentation 5 V stable**.
* **Erreurs de permissions (venv) ?** Sous Windows PowerShell, exécutez une fois `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.