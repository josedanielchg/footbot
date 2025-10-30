## Estructura del repositorio

La base de código está dividida en **cuatro módulos de nivel superior**, cada uno responsable de una parte distinta del sistema. La documentación vive en `docs/` y, más adelante, se incluyen guías específicas por módulo.

---

## Tabla de contenidos

- [Módulos de nivel superior](#modulos-de-nivel-superior)
- [Lenguajes y herramientas](#lenguajes-y-herramientas)
- [Entornos de Python (uno por módulo en el host)](#entornos-de-python-uno-por-modulo-en-el-host)

---

### Módulos de nivel superior

- **`esp32cam_robot/` — Firmware embebido (en el robot)**
  - Firmware para ESP32-CAM que expone **endpoints HTTP de control** y **transmisión de video**.
  - Subsistemas: aprovisionamiento Wi-Fi, servidor web y manejadores de solicitudes, drivers de motor/LED, control de cámara.
  - **Lenguaje/Herramientas:** C++ (núcleo Arduino para ESP32), Arduino IDE o PlatformIO.

- **`manual_control/` — Teleoperación por gestos (host)**
  - Captura con webcam, **detección y clasificación de mano/gestos**, mapeo de comandos, cliente HTTP hacia el robot.
  - **Lenguaje/Herramientas:** Python; ver `requirements.txt` para dependencias de visión/ejecución.
  - Punto de entrada: `main.py`.

- **`auto_soccer_bot/` — Modo automático (autonomía en el host)**
  - Ingesta del stream de la ESP32-CAM, **detección de balón**, lógica de decisión (**seguidor de balón implementado**), cliente HTTP.
  - Incluye pesos YOLO exportados en `models/` para ejecuciones locales.
  - **Lenguaje/Herramientas:** Python; punto de entrada `main.py`.

- **`soccer_vision/` — Entrenamiento y evaluación de modelos (YOLOv11, 2 clases: `goal` y `opponent`)**
  - Estructura de dataset (`train/`, `val/`), CLI y notebooks de entrenamiento, tester rápido de inferencia y **artefactos** (curvas, matrices de confusión, pesos guardados).
  - **Lenguaje/Herramientas:** Python con la pila Ultralytics/YOLO (ver `requirements.txt`).

<br>

> Carpetas de soporte
> - **`docs/`**: documentación multilingüe (`en/`, `es/`, `fr/`).  
> - **`LICENSE` / `README.md`**: licencia y vista general de alto nivel.

---

### Lenguajes y herramientas (ampliado)

- **Firmware (robot):** C++ con el **núcleo Arduino para ESP32**  
  - **Placa/SDK:** AI-Thinker ESP32-CAM, `esp32-camera`, `esp_http_server`, `WiFi.h`, **LEDC PWM** para motores, **PSRAM** opcional.  
  - **Build:** Arduino IDE 2.x (recomendado) o PlatformIO. `partitions.csv` personalizado. Parsing JSON vía **ArduinoJson**.

- **Módulos en el host:** **Python 3.10+** (probado 3.11) con **un entorno virtual por módulo** (`manual_control/`, `auto_soccer_bot/`, `soccer_vision/`).  
  Soporte OS: Windows, macOS, Linux.

- **Pila de visión por computador y ML**
  - **Ultralytics YOLO (v8/v11, backend PyTorch)**  
    - **Uso en:** `soccer_vision/` (entrenar/retarinar **goal/opponent**); `auto_soccer_bot/` (inferencia).  
    - **Artefactos:** pesos `.pt` exportados en `models/`, ejecuciones crudas en `runs/`, gráficas seleccionadas en `results/`.  
    - **Aceleración:** CPU por defecto; build CUDA opcional para GPU.
  - **MediaPipe (Hands)**  
    - **Uso en:** `manual_control/` para **landmarks de mano en tiempo real** → clasificación de gestos (forward/back/left/right/stop).  
    - **Por qué:** latencia muy baja en CPU; robusto a iluminación/pose; no requiere GPU.
  - **OpenCV (cv2)**  
    - **Uso en:** E/S y decodificación de frames, captura de webcam, superposiciones gráficas, conversiones **HSV** y morfología (detector por color), ventanas, pre/post-proceso ligero.  
    - **Notas:** mantener las operaciones ligeras para reducir la latencia extremo a extremo.
  - **HTTPX (async)**  
    - **Uso en:** `auto_soccer_bot/` para **ingesta MJPEG** desde `http://<ESP32_IP>:81/stream` (parseo multipart) y **POST JSON** a `/move`.  
    - **Por qué:** parseo explícito de boundaries, control de backpressure y timeouts robustos.
  - **NumPy / librerías estándar**  
    - **Uso en:** operaciones sobre arreglos, matemáticas, bucles `asyncio`, configuraciones/logging simples.

- **Modelos/Artefactos:** **Pesos `.pt` de PyTorch**, carpetas de ejecuciones de Ultralytics (curvas de entrenamiento, matrices de confusión), imágenes de resultados seleccionadas para la documentación.

- **Anotación y notebooks:** **Label Studio** para etiquetado del dataset (export YOLO). Notebooks de **Jupyter/VS Code** para entrenamiento y demos (`soccer_vision/notebooks/`).

- **Configuración y docs:** JSON/YAML para ajustes; **Markdown** para docs (multilingüe en `docs/en|es|fr`). Diagramas de arquitectura opcionales (Mermaid/PNG).

- **CLI y utilidades (opcionales):** `curl` para probar endpoints, `ffplay/VLC` para validar el stream, `ipykernel` para kernels de notebooks fijados.

---

### Entornos de Python (uno por módulo en el host)

Para mantener las dependencias limpias y reproducibles, el código del host usa **tres entornos de Python aislados**—uno por cada módulo basado en Python:

1. **`auto_soccer_bot/`** — modo automático (visión + controlador)  
2. **`manual_control/`** — teleoperación por gestos  
3. **`soccer_vision/`** — entrenamiento y evaluación para detección de **goal/opponent**

Cada módulo incluye su propio `requirements.txt`. Crea y activa el entorno **dentro del directorio del módulo**.
