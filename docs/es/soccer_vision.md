## Soccer Vision (`soccer_vision/`) — Arquitectura y Operación
---

### Tabla de contenidos
- [Qué hace este módulo](#qué-hace-este-módulo)
- [Label Studio (anotación → exportación a YOLO)](#label-studio-anotación--exportación-a-yolo)
- [Responsabilidades de archivos (resumen)](#responsabilidades-de-archivos-resumen)
- [Estructura de carpetas (alto nivel)](#estructura-de-carpetas-alto-nivel)
- [Instalación](#instalación)
- [Resultados](#resultados)

---

### Qué hace este módulo
Este módulo proporciona el flujo completo con **YOLOv11** para detectar **dos clases** en el campo:
- `goal`
- `opponent`

Incluye validaciones sólidas del dataset y *splitting*, un notebook y una CLI para entrenar/reenrenar, artefactos organizados (gráficas + mejores pesos), y un notebook de demostración para inferencia por lotes en imágenes/videos.

---

### Label Studio (anotación → exportación a YOLO)

**Iniciar Label Studio**
```bash
label-studio
````

Abre [http://localhost:8080](http://localhost:8080) y:

1. **Crea un proyecto** (p. ej., “Soccer Vision”).
2. **Interfaz de etiquetado**: añade la herramienta **Bounding Box** con **dos etiquetas**:

   * `goal`
   * `opponent`
3. **Importa imágenes** y **anota**.
4. **Exporta** → elige formato **YOLO (v5/v8/v11)**. Obtendrás:

   * `images/` (tus imágenes originales)
   * `labels/` (archivos `.txt` de YOLO)
   * `classes.txt` (**debe contener exactamente** `goal` y `opponent` en el orden usado)
   * (opcional) `notes.json`

**Coloca la exportación en:**

````
soccer_vision/
  dataset/
    train/
      images/
      labels/
    # (opcional) val/
    classes.txt   # contiene: goal, opponent
````

> 💡 **Notas**
>
> * **No** agregues una clase “background” a `classes.txt`.
> * Si falta `val/`, la tubería de entrenamiento creará un *split* desde `train/` (mueve por defecto; usa `--copy_split` para copiar).
> * Mantén alineados los pares imagen–label (`xxx.jpg` ↔ `xxx.txt`).

---

### Responsabilidades de archivos (resumen)

| Ruta                                 | Tipo           | Propósito / Qué hace                                                                                                                                                                                                                                                                                                | Parámetros / comportamientos clave                                                                                                         |
| ------------------------------------ | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `notebooks/01_retrain_yolo.ipynb`    | Notebook       | Descarga `dataset.zip` (Drive), normaliza a `soccer_vision/dataset/`, valida la estructura, ejecuta entrenamiento **en vivo** vía `train_yolo()`, copia los mejores pesos + artefactos, y escribe una celda de resumen de resultados compacta.                                                                      | `MODEL_BACKBONE` (por defecto `yolo11s.pt`), `EPOCHS`, `DEVICE`, etc. Siempre guarda artefactos dentro de `soccer_vision/`.                |
| `notebooks/02_test_and_demo.ipynb`   | Notebook       | Descarga `test_data.zip` y `yolo11s.zip` (pesos) desde Drive, normaliza a `soccer_vision/test_data/` y `soccer_vision/models/yolo11s/`, corre inferencia sobre **images/** y **videos/**, muestra una cuadrícula de vista previa y guarda salidas en `runs/`.                                                       | `CONF_THRESH`, selección automática de dispositivo (GPU si disponible).                                                                    |
| `notebooks/modules/train.py`         | Módulo         | Núcleo de entrenamiento. Valida el dataset, (opcionalmente) crea **val split**, escribe `data.yaml`, fija `ULTRALYTICS_HOME`, lanza Ultralytics YOLO, luego copia `best.pt` → `models/<subdir>/soccer_yolo.pt` y los **train_artifacts/** completos. También ejecuta una predicción rápida en `dataset/val/images`. | `train_yolo()` con `model`, `epochs`, `imgsz`, `batch`, `device`, `train_pct`, `copy_split`, `out_subdir`, etc. Devuelve un `TrainResult`. |
| `notebooks/modules/data_utils.py`    | Módulo         | Utilidades para la canalización de datos.                                                                                                                                                                                                                                                                           | `verify_dataset_or_exit`, `split_if_needed`, `write_data_yaml`, `read_classes`, `ensure_dir`.                                              |
| `notebooks/modules/paths.py`         | Módulo         | Detección robusta de la raíz del repositorio y rutas comunes.                                                                                                                                                                                                                                                       | `find_repo_root()`, `base_paths()`. Respeta `SOCCER_VISION_ROOT`.                                                                          |
| `notebooks/modules/logging_utils.py` | Módulo         | *Logging* consistente entre notebooks/CLI.                                                                                                                                                                                                                                                                          | `get_logger()`, *singleton* `log`.                                                                                                         |
| `notebooks/modules/cli.py`           | Módulo (CLI)   | Punto de entrada de línea de comandos que mapea *args* → `train_yolo()`.                                                                                                                                                                                                                                            | `python -m notebooks.modules.cli --help`                                                                                                   |
| `main.py`                            | *Thin wrapper* | Reexporta la CLI (`from notebooks.modules.cli import main`).                                                                                                                                                                                                                                                        | Permite `python soccer_vision/main.py ...`.                                                                                                |
| `requirements.txt`                   | Deps           | Dependencias Python para entrenamiento/inferencia.                                                                                                                                                                                                                                                                  | Instala Torch (con CUDA si aplica) y Ultralytics.                                                                                          |
| `dataset/`                           | Datos          | Dataset YOLO: `train/` y (opcional) `val/`.                                                                                                                                                                                                                                                                         | `classes.txt` debe listar `goal`, `opponent`.                                                                                              |
| `models/`                            | Artefactos     | Pesos exportados + artefactos de entrenamiento copiados.                                                                                                                                                                                                                                                            | p. ej., `models/yolo11s/soccer_yolo.pt`, `train_artifacts/`.                                                                               |
| `runs/`                              | Artefactos     | Carpetas *raw* de Ultralytics (train y predict).                                                                                                                                                                                                                                                                    | Se pueden limpiar *runs* antiguos tras exportar.                                                                                           |
| `results/`                           | Gráficas       | Gráficas seleccionadas copiadas desde los artefactos de entrenamiento para la documentación.                                                                                                                                                                                                                        | Usadas por la celda de resumen en el notebook de reentrenamiento.                                                                          |

---

### Estructura de carpetas (alto nivel)

````
soccer_vision/
├─ dataset/
│  ├─ train/{images,labels}/
│  ├─ val/{images,labels}/
│  └─ classes.txt
├─ models/
│  └─ yolo11s/
│     ├─ soccer_yolo.pt
│     └─ train_artifacts/   # plots, curves, confusion matrices, args.yaml, ...
├─ runs/
├─ results/                  # copias seleccionadas para docs / resumen del notebook
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

### Instalación

> Crea el *venv* **dentro** de `soccer_vision/`, instala dependencias y luego elige un método de *kernel*.

**1) Crear y activar**

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

**2) Instalar dependencias**

````bash
pip install -r requirements.txt
# Torch con GPU (ejemplo CUDA 12.1)
# pip install --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio
# Solo CPU:
# pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
pip install -U "ultralytics>=8.3.220"
````

**3) Elige UN método de kernel**

* **A) Kernel registrado**

  ````bash
  python -m ipykernel install --user --name=sv-soccer --display-name "Python (soccer_vision)"
  ````

  Luego selecciona **Python (soccer_vision)** en Jupyter/VS Code.
* **B) A prueba de balas (servidor desde el venv)**

  ````bash
  python -m pip install notebook ipykernel   # si falta
  python -m notebook
  ````

  Abre `soccer_vision/notebooks/` y ejecuta los notebooks.
  *(VS Code → “Jupyter: Select Interpreter to start Jupyter server” → elige `.venv\Scripts\python.exe`.)*

**4) Celda rápida de verificación (en el notebook)**

````python
import sys, torch, ultralytics
print("Python:", sys.executable)
print("Torch:", torch.__version__, "| CUDA:", torch.version.cuda, "| cuda_available:", torch.cuda.is_available())
print("Ultralytics:", ultralytics.__version__)
````

---

### Resultados (YOLO11S — 2 clases: `goal`, `opponent`)

> Los artefactos de entrenamiento se guardan en `soccer_vision/results/`.
> Conclusiones rápidas: **mAP@0.5 ≈ 0.991**, **pico F1 ≈ 0.86–0.90**, confusión entre clases muy baja.

<table>
<tr>
  <td align="center">
    <img src="../../soccer_vision/results/F1_curve.png" width="300"><br>
    <sub><b>F1–Confianza</b><br>
    Balance entre precisión/recobrado vs. umbral. Pico ≈ <b>0.856</b> → buen <code>conf</code> por defecto.</sub>
  </td>
  <td align="center">
    <img src="../../soccer_vision/results/P_curve.png" width="300"><br>
    <sub><b>Precisión–Confianza</b><br>
    La precisión se mantiene ~1.0 hasta ~0.90 de umbral → pocas falsas alarmas en ajustes típicos.</sub>
  </td>
</tr>
<tr>
  <td align="center" >
    <img src="../../soccer_vision/results/R_curve.png" width="300"><br>
    <sub><b>Recall–Confianza</b><br>
    Alto *recall* a umbrales bajos; cae tras ~0.9 → explica el pico de F1.</sub>
  </td>
  <td align="center">
    <img src="../../soccer_vision/results/PR_curve.png" width="300"><br>
    <sub><b>Curva PR</b><br>
    AP por clase: <b>goal ≈ 0.995</b>, <b>opponent ≈ 0.987</b>, global <b>mAP@0.5 ≈ 0.991</b>.</sub>
  </td>
</tr>
<tr>
  <td align="center" colspan="2">
    <img src="../../soccer_vision/results/confusion_matrix_normalized.png" width="700"><br>
    <sub><b>Matriz de confusión (normalizada)</b><br>
    Correcto en la diagonal. <b>goal ≈ 1.00</b>; <b>opponent ≈ 0.95</b> con ~5% perdidos como fondo.</sub>
  </td>
</tr>
<tr>
  <td align="center" colspan="2">
    <img src="../../soccer_vision/results/results.png" width="600"><br>
    <sub><b>Cuadrícula de curvas de entrenamiento</b><br>
    Las pérdidas decrecen; precisión/recall y mAP de validación suben → aprendizaje sano sin divergencia.</sub>
  </td>
</tr>
</table>

**Lotes de entrenamiento de ejemplo** (aumentaciones + etiquetas)

<p align="center">
  <img src="../../soccer_vision/results/train_batch0.jpg"   width="49%">
  <img src="../../soccer_vision/results/train_batch1.jpg"   width="49%"><br>
  <img src="../../soccer_vision/results/train_batch2.jpg"   width="49%">
  <img src="../../soccer_vision/results/train_batch1450.jpg" width="49%">
  <img src="../../soccer_vision/results/train_batch1451.jpg" width="49%">
</p>

**Interpretación y consejos**

* Empieza la inferencia con **`conf≈0.86–0.90`** (pico de F1), luego ajusta según tu tolerancia a latencia/FP.
* La matriz de confusión muestra **casi perfecto para `goal`** y **sólido para `opponent`**; algunos oponentes se pierden con umbrales muy altos.
* Si despliegas en material más ruidoso, considera **bajar un poco `conf`** (p. ej., 0.7–0.8) para recuperar *recall*, o reentrena con negativos más diversos.