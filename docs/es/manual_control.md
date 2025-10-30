## Control manual (`manual_control/`) — Arquitectura y Operación
---

### Tabla de contenidos
- [Qué hace este módulo](#what-this-module-does)
- [Lenguajes y runtime](#languages--runtime)
  - [Librerías núcleo (detalles)](#core-libraries-details)
- [Estructura de carpetas (alto nivel)](#folder-structure-high-level)
- [Responsabilidades de archivos (resumen)](#file-responsibilities-summary)
- [Instalación](#installation)
- [Comandos de mano — mapa gesto → comando](#hand-commands--gesture--command-map)
---

### Qué hace este módulo
Este módulo del lado del host implementa **teleoperación guiada por gestos**. La webcam del portátil proporciona fotogramas que se procesan para detectar **puntos de referencia de la mano** (MediaPipe). La **mano derecha** codifica la **dirección** (adelante/izquierda/derecha/atrás/alto), y la **mano izquierda** controla la **velocidad** (distancia pulgar–índice). Los comandos se empaquetan como JSON y se envían por **HTTP** al endpoint del ESP32 `/move`. El bucle es asíncrono y tiene **limitación de tasa** para evitar inundar al robot.

**Pipeline (sensar → interpretar → comandar):**
1. **Captura de cámara** (OpenCV)  
2. **Detección de mano y landmarks** (MediaPipe Hands)  
3. **Clasificación de gestos** (dirección) + **estimación de velocidad** (mano izquierda)  
4. **Codificador de comando y transporte** (HTTP `POST /move`, JSON)  
5. **Visualización** (landmarks superpuestos; ESC para salir)

---

### Lenguajes y runtime
- **Lenguaje:** Python 3.10+ (probado con 3.11)
- **Librerías núcleo:** `opencv-python`, `mediapipe`, `httpx`, `asyncio`
- **Interfaz de red:** HTTP (JSON) hacia el ESP32 en `http://<ESP32_IP>:80/move`

#### Librerías núcleo (detalles)

<p align="center">
  <!-- Añade tus logos aquí -->
  <img src="../src/vendor/opencv_logo.jpg" alt="Logo OpenCV" height="76" style="margin-right:18px;" />
  <img src="../src/vendor/mediapipe_logo.jpg" alt="Logo MediaPipe" height="60" />
</p>

- **OpenCV** — captura de cámara (`VideoCapture`), conversiones RGB↔BGR, visualización en ventana, superposición en fotogramas (texto de velocidad, etc.).
- **MediaPipe Hands** — seguidor de mano **21-landmark** en tiempo real usado así:
  - El fotograma de entrada se invierte a **vista selfie** y se convierte a **RGB**.
  - `Hands.process()` devuelve `multi_hand_landmarks` y **handedness** por mano.
  - Extraemos landmarks para las manos **Right** y **Left**.  
    - **Mano derecha → dirección** vía `GestureClassifier.classify_gesture()` usando lógica de “dedo arriba/abajo” basada en tip vs. MCP.  
    - **Mano izquierda → velocidad** vía `GestureClassifier.calculate_speed_from_left_hand()`, mapeando la **distancia pulgar–índice** (en píxeles, normalizada por el tamaño del fotograma) a un rango acotado `[MIN_SPEED, MAX_SPEED]`.
  - Umbrales de confianza y número máximo de manos se configuran en `config.py` (`MIN_DETECTION_CONFIDENCE`, `MIN_TRACKING_CONFIDENCE`, `MAX_NUM_HANDS`).

<p align="center">
  <!-- Marcador de imagen de guía de landmarks de la mano -->
  <img src="../src/vendor/hand-landmarks.png" alt="Guía de landmarks de la mano (21 puntos) de MediaPipe" />
</p>

**Figura — Landmarks de la mano.** Seguimos la indexación de MediaPipe mostrada arriba para calcular estados de dedos (tip vs. MCP) y la distancia pulgar–índice de la mano izquierda usada para el control de velocidad.

---

### Estructura de carpetas (alto nivel)
````

manual_control/
├─ application.py             # Orquesta el ciclo de vida y el bucle principal (async)
├─ camera_manager.py          # Envoltorio de captura de webcam (OpenCV)
├─ config.py                  # IP/puerto, timeouts, umbrales de gesto/velocidad, índice de webcam
├─ detection_manager_base.py  # Base abstracta para detectores
├─ gesture_classifier.py      # Mapeo gesto → comando; estimación de velocidad mano izquierda
├─ hand_detector.py           # Envoltorio de MediaPipe Hands + utilidades de dibujo
├─ main.py                    # Punto de entrada (asyncio.run)
├─ robot_communicator.py      # Cliente HTTP asíncrono con rate limiting/backoff
└─ requirements.txt           # Dependencias fijadas

````

> Detalles de endpoints y payloads aparecen en la sección de API. Abajo se mapea el **propósito principal** de cada archivo.

---

### Responsabilidades de archivos (resumen)

| Ruta | Tipo | Propósito principal | Clases / funciones clave | Notas |
|---|---|---|---|---|
| `application.py` | Orquestador | Inicializa cámara, detector, comunicaciones; ejecuta el bucle asíncrono; renderiza overlay | `Application`, `start_application()` | Pegamento central del módulo. |
| `camera_manager.py` | IO | Abrir/cerrar webcam; leer fotogramas de forma segura | `CameraManager.initialize()`, `get_frame()`, `release()` | Usa OpenCV VideoCapture. |
| `config.py` | Config | Endpoints de red, timeouts; constantes de gesto; mapeo de velocidad; índice de webcam | constants | **Configura aquí `ESP32_IP_ADDRESS`.** |
| `detection_manager_base.py` | Abstracción | Interfaz para detectores enchufables | `DetectionManager` (ABC) | Permite intercambiar detectores futuros. |
| `gesture_classifier.py` | Lógica | Mano derecha → dirección; distancia mano izquierda → velocidad | `classify_gesture()`, `calculate_speed_from_left_hand()` | Umbrales desde `config.py`. |
| `hand_detector.py` | Percepción | Envoltorio de MediaPipe Hands; extracción de landmarks y dibujo | `HandDetector.initialize()`, `process_frame()`, `get_detection_data()` | Vista selfie (flip) activada. |
| `robot_communicator.py` | Transporte | Cliente HTTP async; dedup y limitación de tasa de posts | `RobotCommunicator.send_command()` | Publica JSON a `/move`; maneja timeouts. |
| `main.py` | Entrada | Lanza la aplicación con `asyncio.run` | — | Ejecutar como `python -m manual_control.main`. |
| `requirements.txt` | Dependencias | Dependencias de runtime fijadas para reproducibilidad | — | `opencv-python`, `mediapipe`, `httpx`, `asyncio`. |

---

### Instalación

**Prerequisitos**
- Python **3.10+** (recomendado 3.11)
- Una **webcam** funcional
- El robot ESP32 encendido y accesible en tu LAN

**1) Crear y activar el entorno (`venv_manual_control`)**

> Ejecuta esto desde la **raíz del repositorio** (padre de `manual_control/`).

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

* Edita `manual_control/config.py`:

  * Define `ESP32_IP_ADDRESS = "..."` (IP del robot)
  * Opcional: ajusta `WEBCAM_INDEX`, confianzas de detección y umbrales de mapeo de velocidad.

**4) Ejecutar (desde la raíz del repo)**

````bash
python -m manual_control.main
````

* Aparecerá una ventana de OpenCV con los landmarks superpuestos.
* **ESC** para salir.
* La consola muestra payloads JSON y respuestas HTTP.

---

### Comandos de mano — mapa gesto → comando

Usa la **mano DERECHA** para órdenes **direccionales** y la **mano IZQUIERDA** para modular la **velocidad** (distancia pulgar–índice). Añade las fotos ilustrativas abajo.

| Comando      | Notas                                                          |
| ------------ | -------------------------------------------------------------- |
| **forward**  | Los cinco dedos **abajo** (replegados).                        |
| **backward** | Pulgar **arriba**, otros cuatro **arriba**.                    |
| **left**     | Pulgar e índice **arriba**, otros **abajo**.                   |
| **right**    | Pulgar **abajo**, índice–anular **arriba**, meñique **abajo**. |
| **stop**     | Los cinco dedos **extendidos**.                                |

> La velocidad se calcula a partir de la **distancia pulgar–índice de la mano IZQUIERDA** y se muestra en la superposición de vídeo.

<img src="../src/picture3.png" alt="Ejemplo de overlay / landmarks de mano" />