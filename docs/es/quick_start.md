# 🚀 Inicio rápido

Esta página te ayuda a pasar de cero → funcionando en minutos. Está organizada por sub-proyecto:

---
## Tabla de contenidos

- [1) `esp32cam_robot` — Grabar el firmware (Arduino IDE)](#1-esp32cam_robot--flash-the-firmware-arduino-ide)
- [2) `manual_control` — Teleoperación por gestos (laptop)](#2-manual_control--hand-gesture-teleoperation-laptop)
- [3) `auto_soccer_bot` — Seguidor de balón autónomo (laptop)](#3-auto_soccer_bot--autonomous-ball-follower-laptop)
- [4) `soccer_vision` — Reentrenar y probar YOLO personalizado (2 clases)](#4-soccer_vision--retrain--test-custom-yolo-2-classes)
- [Solución de problemas común](#common-troubleshooting)
---

## 1) `esp32cam_robot` — Grabar el firmware (Arduino IDE)

### Requisitos previos

* **Hardware:** ESP32-CAM (AI-Thinker), **USB-a-Serial (FTDI 3.3 V)**, cables jumper
* **Alimentación:** 5 V para la ESP32-CAM (pin **5V**); **GND común** compartido con el FTDI
* **Host:** Arduino IDE **2.x** (recomendado)

### A. Instalar la plataforma ESP32

1. Abre **Arduino IDE** → **File → Preferences** → *Additional Boards Manager URLs*
2. **Tools → Board → Boards Manager…** → busca **“esp32 by Espressif Systems”** → **Install**.

### B. Seleccionar la placa y opciones correctas

* **Board:** `ESP32 Arduino → AI Thinker ESP32-CAM`
* **Upload Speed:** `115200` (valor estable por defecto)
* **Flash Mode/Freq/Partition:** deja los valores por defecto
* **PSRAM:** `Enabled` (recomendado para la cámara)

### C. Cablear la ESP32-CAM para grabación

Para más información sobre el cableado haz clic [aquí](hardware-power.md)
* Para entrar en el bootloader: con IO0 a GND, presiona **RESET** una vez; mantén IO0-GND durante la carga.

> Después de subir el sketch, **desconecta IO0 de GND** y presiona **RESET** para ejecutar el programa.

### D. Abrir el sketch y configurar Wi-Fi / pines

1. En Arduino IDE, abre: `esp32cam_robot/esp32cam_robot.ino`
2. Completa tu **SSID/PASSWORD de Wi-Fi** y verifica cualquier definición de **GPIO / driver de motores** (en `config.h` o al inicio del sketch).
3. **Tools → Port:** selecciona el puerto COM de tu FTDI (`/dev/ttyUSB*` en Linux, `/dev/cu.*` en macOS, `COM*` en Windows).

### E. Subir y verificar

1. Haz clic en **Upload**. Si ves errores de sincronización, pulsa **RESET** una vez (IO0 debe estar a GND).
2. Al terminar la carga: quita **IO0–GND**, presiona **RESET**.
3. Abre el **Serial Monitor** a **115200** baudios. La ESP32-CAM debería imprimir su **dirección IP**.
4. Pruebas rápidas (ejemplos):

   * Snapshot: `http://<ESP32_IP>:80/capture`
   * Flujo MJPEG: `http://<ESP32_IP>:81/stream`
---

## 2) `manual_control` — Teleoperación por gestos (laptop)

### Instalación

**Requisitos previos**

* Python **3.10+** (recomendado 3.11)
* Una **webcam** funcional
* El robot ESP32 encendido y accesible en tu LAN

**1) Crear y activar el entorno (`venv_manual_control`)**

> Ejecuta esto desde la **raíz del repositorio** (carpeta padre de `manual_control/`).

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

**2) Instalar dependencias**

````bash
pip install -r manual_control/requirements.txt
````

**3) Configurar endpoints y opciones**

Edita `manual_control/config.py`:

* Define `ESP32_IP_ADDRESS = "..."` (IP del robot)
* Opcional: ajusta `WEBCAM_INDEX`, las confidencias de detección y los umbrales del mapeo de velocidad.

**4) Ejecutar (desde la raíz del repositorio)**

````bash
python -m manual_control.main
````

* Aparecerá una ventana de OpenCV con superposiciones de *landmarks*.
* Presiona **ESC** para salir.
* La consola mostrará las cargas útiles JSON y las respuestas HTTP.

---

## 3) `auto_soccer_bot` — Seguidor de balón autónomo (laptop)

### Instalación

**Requisitos previos**

* Python **3.10+** (recomendado 3.11)
* Robot ESP32 accesible en tu LAN y transmitiendo en `http://<ESP32_IP>:81/stream`

**1) Crear y activar el entorno (`venv_auto_soccer`)**

> Ejecuta esto desde la **raíz del repositorio** (carpeta padre de `auto_soccer_bot/`).

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

**2) Instalar dependencias**

````bash
pip install -r auto_soccer_bot/requirements.txt
````

**3) Configurar**

Edita `auto_soccer_bot/config_auto.py`:

* Define `ESP32_IP_ADDRESS = "..."` y ajusta los puertos si es necesario.
* Selecciona los pesos de **YOLO** en `models/` y sus umbrales.
* Ajusta las ganancias del controlador, el corredor objetivo y (opcionalmente) el *resize* en la ingesta.

**4) Ejecutar (desde la raíz del repositorio)**

````bash
python -m auto_soccer_bot.main
````

* Una ventana de depuración opcional mostrará detecciones y el estado de la dirección.
* Los *logs* imprimirán tiempos por cuadro, el comando elegido y las respuestas HTTP.

---

## 4) `soccer_vision` — Reentrenar y probar YOLO personalizado (2 clases)

Este módulo permite **(re)entrenar** YOLOv11 para detectar **dos clases** en el campo: `goal` y `opponent`, y luego **ejecutar inferencia rápida** sobre imágenes/videos. Coincide con la guía completa [aquí](soccer_vision.md).

### Instalación

**Requisitos previos**

* Python **3.10+** (3.11 recomendado)
* (Opcional) GPU compatible con CUDA + build de PyTorch correspondiente
* (Opcional) **Label Studio** para la anotación si crearás un dataset nuevo

**1) Crear y activar un venv (dentro del módulo)**

> Haz esto **dentro** de la carpeta `soccer_vision/`.

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

**2) Instalar dependencias**

````bash
pip install -r requirements.txt
# Opcional: elige el build de Torch adecuado para tu máquina
# Ejemplo GPU (CUDA 12.1):
# pip install --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio
# Solo CPU:
# pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
````

### Preparar el dataset (Label Studio → export YOLO)

1. Inicia Label Studio:

   ````bash
   label-studio
   ````
2. En [http://localhost:8080](http://localhost:8080) crea un proyecto (p. ej., “Soccer Vision”), agrega **Bounding Box** con etiquetas:

   * `goal`
   * `opponent`
3. Anota → **Export** como **YOLO (v5/v8/v11)**.
4. Coloca la exportación en:

   ````
   soccer_vision/
     dataset/
       train/
         images/
         labels/
       # (opcional) val/
       classes.txt   # debe contener exactamente: goal, opponent
   ````

   *Si falta `val/`, el entrenamiento creará una partición a partir de `train/`*

### Entrenar (elige UNA vía)

**A) Notebook (recomendado la primera vez)**

1. Lanza Jupyter desde el **venv activado**:

   ````bash
   python -m pip install notebook ipykernel  # si falta
   python -m notebook
   ````
2. Abre `notebooks/01_retrain_yolo.ipynb` y **Run All**.
   El notebook valida el dataset, crea `data.yaml`, configura `ULTRALYTICS_HOME`, entrena y copia:

   * **Mejores pesos** → `models/yolo11s/soccer_yolo.pt`
   * **Artefactos de entrenamiento** → `models/yolo11s/train_artifacts/`
   * Las gráficas seleccionadas pueden copiarse a `results/` para la documentación.

**B) CLI (sin interfaz gráfica)**

````bash
# desde soccer_vision/ (venv activo)
python -m notebooks.modules.cli \
  --model yolo11s.pt \
  --epochs 60 \
  --imgsz 640 \
  --batch 16 \
  --train_pct 0.9 \
  --device 0          # GPU 0 (usa "cpu" si no hay GPU)
# Salidas:
#  - models/yolo11s/soccer_yolo.pt
#  - models/yolo11s/train_artifacts/...
#  - runs/ (ejecuciones crudas de Ultralytics)
````

### Inferencia rápida

**Notebook:** `notebooks/02_test_and_demo.ipynb` (imágenes/videos → guarda salidas en `runs/`).

**One-liner (Python)**

````python
from ultralytics import YOLO
m = YOLO("soccer_vision/models/yolo11s/soccer_yolo.pt")
m.predict(
    source="soccer_vision/dataset/val/images",  # o ruta a archivo/carpeta/video
    save=True,
    conf=0.86,                                  # comienza cerca del pico de F1; ajusta según necesites
    project="soccer_vision/runs",
    name="quick_predict",
    exist_ok=True
)
````

### Dónde encontrar los resultados

* **Pesos:** `soccer_vision/models/yolo11s/soccer_yolo.pt`
* **Artefactos de entrenamiento (gráficas, curvas, matriz de confusión, args):**
  `soccer_vision/models/yolo11s/train_artifacts/`
* **Gráficas seleccionadas para docs:** `soccer_vision/results/`
* **Ejecuciones crudas de Ultralytics:** `soccer_vision/runs/`

> Nota: Puedes ver todos los resultados del modelo entrenado al final de la documentación de **Soccer Vision**: [aquí](soccer_vision.md)

### Consejos y solución de problemas

* **Sin partición `val/`:** El *trainer* crea una automáticamente desde `train/` (mueve por defecto).
* **La GPU no se usa:** Instala la rueda de Torch **que corresponda a tu CUDA** (ver comandos arriba) o usa `--device cpu`.
* **Umbral de confianza:** Comienza la inferencia alrededor de **`conf≈0.86–0.90`** (pico de F1 según la doc) y ajusta según tu equilibrio FP/latencia.
* **Carpeta `runs` muy grande:** Puedes depurar `soccer_vision/runs/` después de exportar los mejores pesos.

---

### Solución de problemas común

* **No puedes alcanzar la IP de la ESP32?** Asegúrate de que la ESP32 y la laptop estén en la **misma Wi-Fi** y que tu router no aísle clientes.
* **El stream se entrecorta?** Mantén **QVGA (320×240)** y calidad JPEG moderada en el firmware; usa los modos de ingesta **HTTPX** en las apps Python.
* **Falla la carga (ESP32-CAM)?** Entra otra vez al bootloader (IO0→GND + RESET), baja **Upload Speed** a `115200`, revisa el cruce TX/RX y asegura una **alimentación de 5 V estable**.
* **Errores de permisos (venv)?** En Windows PowerShell, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.