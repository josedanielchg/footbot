## Soccer Vision (`soccer_vision/`) — Architecture et fonctionnement
---

### Table des matières
- [À quoi sert ce module](#à-quoi-sert-ce-module)
- [Label Studio (annotation → export YOLO)](#label-studio-annotation--export-yolo)
- [Responsabilités des fichiers (résumé)](#responsabilités-des-fichiers-résumé)
- [Structure des dossiers (haut niveau)](#structure-des-dossiers-haut-niveau)
- [Installation](#installation)
- [Résultats](#résultats)

---

### À quoi sert ce module
Ce module fournit le flux complet **YOLOv11** pour détecter **deux classes** sur le terrain :
- `goal`
- `opponent`

Il inclut des contrôles/partitions robustes du jeu de données, un notebook & une CLI pour entraîner/ré-entraîner, des artefacts clairement organisés (courbes + meilleurs poids), ainsi qu’un notebook de démo pour l’inférence par lots sur images/vidéos.

---

### Label Studio (annotation → export YOLO)

**Démarrer Label Studio**
```bash
label-studio
````

Ouvrez [http://localhost:8080](http://localhost:8080) et :

1. **Créez un projet** (p. ex., “Soccer Vision”).
2. **Interface d’annotation** : ajoutez l’outil **Boîte englobante** avec **deux labels** :

   * `goal`
   * `opponent`
3. **Importez les images** et **annotez**.
4. **Exportez** → choisissez le format **YOLO (v5/v8/v11)**. Vous obtiendrez :

   * `images/` (vos images brutes)
   * `labels/` (fichiers `.txt` YOLO)
   * `classes.txt` (**doit contenir exactement** `goal` et `opponent` dans l’ordre utilisé)
   * (optionnel) `notes.json`

**Placez l’export ici :**

````
soccer_vision/
  dataset/
    train/
      images/
      labels/
    # (optionnel) val/
    classes.txt   # contient : goal, opponent
````

> 💡 **Notes**
>
> * **N’ajoutez pas** de classe “background” à `classes.txt`.
> * Si `val/` est absent, la pipeline d’entraînement créera un *split* à partir de `train/` (déplacement par défaut ; utilisez `--copy_split` pour copier).
> * Conservez l’alignement image–label (`xxx.jpg` ↔ `xxx.txt`).

---

### Responsabilités des fichiers (résumé)

| Chemin                               | Type           | Rôle / Ce que fait le fichier                                                                                                                                                                                                                                                                                | Paramètres / comportements clés                                                                                                             |
| ------------------------------------ | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `notebooks/01_retrain_yolo.ipynb`    | Notebook       | Télécharge `dataset.zip` (Drive), normalise vers `soccer_vision/dataset/`, valide la structure, lance l’entraînement **en direct** via `train_yolo()`, copie les meilleurs poids + artefacts, écrit une cellule de synthèse compacte.                                                                        | `MODEL_BACKBONE` (par défaut `yolo11s.pt`), `EPOCHS`, `DEVICE`, etc. Conserve toujours les artefacts dans `soccer_vision/`.                 |
| `notebooks/02_test_and_demo.ipynb`   | Notebook       | Télécharge `test_data.zip` et `yolo11s.zip` (poids) depuis Drive, normalise vers `soccer_vision/test_data/` et `soccer_vision/models/yolo11s/`, exécute l’inférence sur **images/** et **videos/**, affiche une grille d’aperçu, enregistre les sorties dans `runs/`.                                        | `CONF_THRESH`, sélection auto du device (GPU si dispo).                                                                                     |
| `notebooks/modules/train.py`         | Module         | Cœur d’entraînement. Valide le dataset, (option) crée le **split val**, écrit `data.yaml`, fixe `ULTRALYTICS_HOME`, lance Ultralytics YOLO, puis copie `best.pt` → `models/<subdir>/soccer_yolo.pt` et le dossier **train_artifacts/**. Lance aussi une passe de prédiction rapide sur `dataset/val/images`. | `train_yolo()` avec `model`, `epochs`, `imgsz`, `batch`, `device`, `train_pct`, `copy_split`, `out_subdir`, etc. Retourne un `TrainResult`. |
| `notebooks/modules/data_utils.py`    | Module         | Utilitaires de pipeline de données.                                                                                                                                                                                                                                                                          | `verify_dataset_or_exit`, `split_if_needed`, `write_data_yaml`, `read_classes`, `ensure_dir`.                                               |
| `notebooks/modules/paths.py`         | Module         | Détection robuste de la racine du repo & chemins communs.                                                                                                                                                                                                                                                    | `find_repo_root()`, `base_paths()`. Respecte `SOCCER_VISION_ROOT`.                                                                          |
| `notebooks/modules/logging_utils.py` | Module         | Journalisation homogène pour notebooks/CLI.                                                                                                                                                                                                                                                                  | `get_logger()`, *singleton* `log`.                                                                                                          |
| `notebooks/modules/cli.py`           | Module (CLI)   | Point d’entrée en ligne de commande mappant les arguments → `train_yolo()`.                                                                                                                                                                                                                                  | `python -m notebooks.modules.cli --help`                                                                                                    |
| `main.py`                            | Fin adaptateur | Ré-exporte la CLI (`from notebooks.modules.cli import main`).                                                                                                                                                                                                                                                | Permet `python soccer_vision/main.py ...`.                                                                                                  |
| `requirements.txt`                   | Dépendances    | Dépendances Python pour entraînement/inférence.                                                                                                                                                                                                                                                              | Installer Torch (build CUDA si besoin) et Ultralytics.                                                                                      |
| `dataset/`                           | Données        | Dataset YOLO : `train/` et (optionnel) `val/`.                                                                                                                                                                                                                                                               | `classes.txt` doit lister `goal`, `opponent`.                                                                                               |
| `models/`                            | Artefacts      | Poids exportés + artefacts d’entraînement copiés.                                                                                                                                                                                                                                                            | ex. `models/yolo11s/soccer_yolo.pt`, `train_artifacts/`.                                                                                    |
| `runs/`                              | Artefacts      | Dossiers Ultralytics bruts (train et predict).                                                                                                                                                                                                                                                               | Vous pouvez purger d’anciens *runs* après export.                                                                                           |
| `results/`                           | Graphiques     | Sélection de courbes copiées depuis les artefacts d’entraînement pour la doc.                                                                                                                                                                                                                                | Utilisées par la cellule de synthèse du notebook de ré-entraînement.                                                                        |

---

### Structure des dossiers (haut niveau)

````
soccer_vision/
├─ dataset/
│  ├─ train/{images,labels}/
│  ├─ val/{images,labels}/
│  └─ classes.txt
├─ models/
│  └─ yolo11s/
│     ├─ soccer_yolo.pt
│     └─ train_artifacts/   # plots, courbes, matrices de confusion, args.yaml, ...
├─ runs/
├─ results/                  # copies sélectionnées pour la doc / synthèse du notebook
├─ notebooks/
│  ├─ 01_retrain_yolo.ipynb
│  ├─ 02_test_and_demo.ipynb
│  └─ modules/
│     ├─ cli.py
│     ├─ data_utils.py
│     ├─ logging_utils.py
│     ├─ paths.py
│     └─ train.py
├─ main.py
└─ requirements.txt
````

---

### Installation

> Créez le *venv* **dans** `soccer_vision/`, installez les dépendances, puis choisissez une méthode de noyau (kernel).

**1) Créer & activer**

* **Windows (PowerShell)**

  ````powershell
  cd soccer_vision
  python -m venv .venv
  .\.venv\Scripts\activate
  python -m pip install --upgrade pip
  ````
* **macOS / Linux**

  ````bash
  cd soccer_vision
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip
  ````

**2) Installer les dépendances**

````bash
pip install -r requirements.txt
# Torch GPU (ex. CUDA 12.1)
# pip install --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio
# CPU uniquement :
# pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
pip install -U "ultralytics>=8.3.220"
````

**3) Choisir UNE méthode de noyau**

* **A) Noyau enregistré**

  ````bash
  python -m ipykernel install --user --name=sv-soccer --display-name "Python (soccer_vision)"
  ````

  Puis sélectionnez **Python (soccer_vision)** dans Jupyter/VS Code.
* **B) Infaillible (serveur depuis le venv)**

  ````bash
  python -m pip install notebook ipykernel   # si manquant
  python -m notebook
  ````

  Ouvrez `soccer_vision/notebooks/` et exécutez les notebooks.
  *(VS Code → “Jupyter: Select Interpreter to start Jupyter server” → choisissez `.venv\Scripts\python.exe`.)*

**4) Cellule de vérification rapide (dans le notebook)**

````python
import sys, torch, ultralytics
print("Python :", sys.executable)
print("Torch :", torch.__version__, "| CUDA :", torch.version.cuda, "| cuda_available :", torch.cuda.is_available())
print("Ultralytics :", ultralytics.__version__)
````

---

### Résultats (YOLO11S — 2 classes : `goal`, `opponent`)

> Les artefacts d’entraînement sont enregistrés sous `soccer_vision/results/`.
> Points clés : **mAP@0.5 ≈ 0,991**, **pic F1 ≈ 0,86–0,90**, très faible confusion inter-classes.

<table>
<tr>
  <td align="center">
    <img src="../../soccer_vision/results/F1_curve.png" width="300"><br>
    <sub><b>F1–Confiance</b><br>
    Équilibre précision/rappel vs seuil. Pic ≈ <b>0,856</b> → bon <code>conf</code> par défaut.</sub>
  </td>
  <td align="center">
    <img src="../../soccer_vision/results/P_curve.png" width="300"><br>
    <sub><b>Précision–Confiance</b><br>
    La précision reste ~1,0 jusqu’à ~0,90 de seuil → peu de faux positifs aux réglages usuels.</sub>
  </td>
</tr>
<tr>
  <td align="center" >
    <img src="../../soccer_vision/results/R_curve.png" width="300"><br>
    <sub><b>Rappel–Confiance</b><br>
    Rappel élevé à faibles seuils ; chute après ~0,9 → explique le pic de F1.</sub>
  </td>
  <td align="center">
    <img src="../../soccer_vision/results/PR_curve.png" width="300"><br>
    <sub><b>Courbe PR</b><br>
    AP par classe : <b>goal ≈ 0,995</b>, <b>opponent ≈ 0,987</b>, mAP@0.5 global <b>≈ 0,991</b>.</sub>
  </td>
</tr>
<tr>
  <td align="center" colspan="2">
    <img src="../../soccer_vision/results/confusion_matrix_normalized.png" width="700"><br>
    <sub><b>Matrice de confusion (normalisée)</b><br>
    Correct sur la diagonale. <b>goal ≈ 1,00</b> ; <b>opponent ≈ 0,95</b> avec ~5% manqués comme arrière-plan.</sub>
  </td>
</tr>
<tr>
  <td align="center" colspan="2">
    <img src="../../soccer_vision/results/results.png" width="600"><br>
    <sub><b>Grille des courbes d’entraînement</b><br>
    Les pertes diminuent ; précision/rappel et mAP de validation montent → apprentissage sain sans divergence.</sub>
  </td>
</tr>
</table>

**Lots d’entraînement exemples** (augmentations + labels)

<p align="center">
  <img src="../../soccer_vision/results/train_batch0.jpg"   width="49%">
  <img src="../../soccer_vision/results/train_batch1.jpg"   width="49%"><br>
  <img src="../../soccer_vision/results/train_batch2.jpg"   width="49%">
  <img src="../../soccer_vision/results/train_batch1450.jpg" width="49%">
  <img src="../../soccer_vision/results/train_batch1451.jpg" width="49%">
</p>

**Interprétation & conseils**

* Démarrez l’inférence avec **`conf≈0,86–0,90`** (pic F1), puis ajustez selon votre tolérance à la latence/aux FP.
* La matrice de confusion montre **quasi parfait pour `goal`** et **très bon pour `opponent`** ; quelques opposants sont manqués à des seuils très élevés.
* En contexte plus bruité, envisagez de **baisser légèrement `conf`** (p. ex., 0,7–0,8) pour récupérer du rappel, ou ré-entraîner avec des négatifs plus variés.
