## Control manual (`manual_control/`) — Arquitectura y Operación
---

### Índice
- [Qué hace este módulo](#qué-hace-este-módulo)
- [Lenguajes y entorno de ejecución](#lenguajes-y-entorno-de-ejecución)
  - [Bibliotecas núcleo (detalles)](#bibliotecas-núcleo-detalles)
- [Estructura de carpetas (alto nivel)](#estructura-de-carpetas-alto-nivel)
- [Responsabilidades de archivos (resumen)](#responsabilidades-de-archivos-resumen)
- [Instalación](#instalación)
- [Comandos de mano — mapa gesto → comando](#comandos-de-mano--mapa-gesto--comando)
---

### Qué hace este módulo
Este módulo del lado del portátil implementa la **teleoperación por gestos**. La webcam del portátil provee *frames* que se procesan para detectar **puntos de referencia de la mano** (MediaPipe). La **mano derecha** define la **dirección** (adelante/izquierda/derecha/atrás/stop) y la **mano izquierda** controla la **velocidad** (distancia pulgar–índice). Los comandos se empaquetan como JSON y se envían por **HTTP** al endpoint `/move` del ESP32. El bucle es asíncrono y con **limitación de tasa** para no saturar al robot.

**Pipeline (sensar → interpretar → ordenar):**
1. **Captura de cámara** (OpenCV)  
2. **Detección de manos y *landmarks*** (MediaPipe Hands)  
3. **Clasificación de gestos** (dirección) + **estimación de velocidad** (mano izquierda)  
4. **Codificación y transporte del comando** (HTTP `POST /move`, JSON)  
5. **Visualización** (superposición de *landmarks*; ESC para salir)

---

### Lenguajes y entorno de ejecución
- **Lenguaje:** Python 3.10+ (probado con 3.11)
- **Bibliotecas núcleo:** `opencv-python`, `mediapipe`, `httpx`, `asyncio`
- **Interfaz de red:** HTTP (JSON) hacia `http://<ESP32_IP>:80/move`

#### Bibliotecas núcleo (detalles)

<p align="center">
  <!-- Espacio para logos -->
  <img src="../src/vendor/opencv_logo.jpg" alt="OpenCV logo" height="76" style="margin-right:18px;" />
  <img src="../src/vendor/mediapipe_logo.jpg" alt="MediaPipe logo" height="60" />
</p>

- **OpenCV** — captura de cámara (`VideoCapture`), conversiones RGB↔BGR, ventana de visualización y superposiciones (texto de velocidad, etc.).
- **MediaPipe Hands** — *tracker* de mano con **21 *landmarks*** en tiempo real usado así:
  - El *frame* de entrada se invierte a **vista selfie** y se convierte a **RGB**.
  - `Hands.process()` devuelve `multi_hand_landmarks` y **lateralidad** por mano.
  - Extraemos *landmarks* de **Derecha** e **Izquierda**.  
    - **Derecha → dirección** mediante `GestureClassifier.classify_gesture()` usando la lógica “dedo arriba/abajo” (comparación punta vs. MCP).  
    - **Izquierda → velocidad** con `GestureClassifier.calculate_speed_from_left_hand()`, mapeando la **distancia pulgar–índice** (en píxeles, normalizada por tamaño de imagen) a `[MIN_SPEED, MAX_SPEED]`.
  - Umbrales de confianza y número máximo de manos se configuran en `config.py` (`MIN_DETECTION_CONFIDENCE`, `MIN_TRACKING_CONFIDENCE`, `MAX_NUM_HANDS`).

<p align="center">
  <!-- Guía de landmarks de la mano -->
  <img src="../src/vendor/hand-landmarks.png" alt="Guía de landmarks de la mano (21 puntos)" />
</p>

**Figura — *Landmarks* de la mano.** Seguimos la indexación de MediaPipe para calcular estados de dedos (punta vs. MCP) y la distancia pulgar–índice de la mano izquierda usada para el control de velocidad.

---

### Estructura de carpetas (alto nivel)
```

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

> Los detalles de endpoints y *payloads* se cubren en la sección de API. Abajo mapeamos el **propósito principal** de cada archivo.

---

### Responsabilidades de archivos (resumen)

| Ruta | Tipo | Propósito principal | Clases / funciones clave | Notas |
|---|---|---|---|---|
| `application.py` | Orquestador | Inicializa cámara, detector y comunicaciones; ejecuta el bucle asíncrono; dibuja la superposición | `Application`, `start_application()` | Núcleo de unión del módulo. |
| `camera_manager.py` | IO | Abrir/cerrar webcam; lectura de *frames* | `CameraManager.initialize()`, `get_frame()`, `release()` | OpenCV `VideoCapture`. |
| `config.py` | Config | Endpoints de red, *timeouts*; constantes de gestos; mapeo de velocidad; índice de webcam | constantes | **Configura `ESP32_IP_ADDRESS` aquí.** |
| `detection_manager_base.py` | Abstracción | Interfaz para detectores intercambiables | `DetectionManager` (ABC) | Permite futuros detectores. |
| `gesture_classifier.py` | Lógica | Mano derecha → dirección; distancia izquierda → velocidad | `classify_gesture()`, `calculate_speed_from_left_hand()` | Umbrales en `config.py`. |
| `hand_detector.py` | Percepción | Envoltura de MediaPipe Hands; extracción/dibujo de *landmarks* | `initialize()`, `process_frame()`, `get_detection_data()` | Vista selfie habilitada. |
| `robot_communicator.py` | Transporte | Cliente HTTP asíncrono; desduplicación y *rate limiting* | `send_command()` | Envía JSON a `/move`. |
| `main.py` | Entrada | Lanza la app con `asyncio.run` | — | Ejecutar `python -m manual_control.main`. |
| `requirements.txt` | Dependencias | Versionado de *runtime* | — | `opencv-python`, `mediapipe`, `httpx`, `asyncio`. |

---

### Instalación

**Prerrequisitos**
- Python **3.10+** (recomendado 3.11)
- Una **webcam** funcional
- El robot ESP32 encendido y accesible en tu red

**1) Crear y activar el entorno (`venv_manual_control`)**

> Ejecuta estos comandos desde la **raíz del repositorio** (carpeta padre de `manual_control/`).

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
  * Opcional: ajusta `WEBCAM_INDEX`, confidencias de detección y umbrales de velocidad.

**4) Ejecutar (desde la raíz del repositorio)**

````bash
python -m manual_control.main
````

* Se abrirá una ventana de OpenCV con los *landmarks*.
* **ESC** para salir.
* La consola muestra los JSON enviados y las respuestas HTTP.

---

### Comandos de mano — mapa gesto → comando

Usa la **mano DERECHA** para las **direcciones** y la **mano IZQUIERDA** para la **velocidad** (distancia pulgar–índice). Inserta aquí tus imágenes ilustrativas.

| Comando      | Notas                                                          |
| ------------ | -------------------------------------------------------------- |
| **forward**  | Los cinco dedos **abajo** (flexionados).                       |
| **backward** | Pulgar **arriba**, otros cuatro **arriba**.                    |
| **left**     | Pulgar e índice **arriba**, resto **abajo**.                   |
| **right**    | Pulgar **abajo**, índice–anular **arriba**, meñique **abajo**. |
| **stop**     | Los cinco dedos **extendidos**.                                |

> La velocidad se calcula con la distancia pulgar–índice de la **mano izquierda** y se muestra en la superposición de vídeo.

<img src="../src/picture3.png" alt="Ejemplo de landmarks/gesto" />