## Estructura del repositorio

El código se divide en **cuatro módulos de nivel superior**, cada uno responsable de una parte del sistema. La documentación está en `docs/`, y las guías detalladas por módulo aparecen en secciones posteriores.

---

### Módulos de nivel superior

- **`esp32cam_robot/` — Firmware embebido (en el robot)**
  - Firmware para ESP32-CAM que expone **endpoints HTTP de control** y **transmisión de video**.
  - Subsistemas: provisión Wi-Fi, servidor web y *handlers* de solicitudes, control de motores/LED, control de cámara.
  - **Lenguaje/Herramientas:** C++ (núcleo Arduino para ESP32), Arduino IDE o PlatformIO.

- **`manual_control/` — Teleoperación por gestos (host)**
  - Captura por webcam, **detección y clasificación de gestos**, mapeo de comandos y cliente HTTP hacia el robot.
  - **Lenguaje/Herramientas:** Python; ver `requirements.txt` para dependencias de visión/ejecución.
  - Punto de entrada: `main.py`.

- **`auto_soccer_bot/` — Modo automático (autonomía en host)**
  - Ingesta del *stream* de ESP32-CAM, **detección de balón**, lógica de decisión (**seguidor de balón implementado**), cliente HTTP.
  - Incluye pesos YOLO exportados en `models/` para ejecuciones locales.
  - **Lenguaje/Herramientas:** Python; punto de entrada `main.py`.

- **`opponent-detector/` — Entrenamiento y evaluación de modelos**
  - Estructura de *dataset* (`train/`, `val/`), script de *training*, prueba de inferencia y **artefactos** (curvas, matrices de confusión, pesos guardados).
  - **Lenguaje/Herramientas:** Python con la pila Ultralytics/YOLO (ver `requirements.txt`).

> Carpetas de soporte  
> - **`docs/`**: documentación multilingüe (`en/`, `es/`, `fr/`).  
> - **`LICENSE` / `README.md`**: licencia y panorama general.

---

### Lenguajes y herramientas

- **Firmware (robot):** C++ con el **núcleo Arduino para ESP32** (sketch `esp32cam_robot.ino`, fuentes C++ en `src/`).
- **Módulos en host:** **Python 3.x** para percepción, decisión y telemetría.
- **Modelos/Artefactos:** Pesos PyTorch `.pt`.
- **Configuración y docs:** JSON/YAML, Markdown.

---

### Entornos de Python (uno por módulo en host)

Para mantener dependencias limpias y reproducibles, el código en host usa **tres entornos de Python aislados**—uno por cada módulo basado en Python:

1. **`auto_soccer_bot/`** — modo automático (visión + controlador)  
2. **`manual_control/`** — teleoperación por gestos  
3. **`opponent-detector/`** — entrenamiento y evaluación

Cada módulo incluye su propio `requirements.txt`. Crea y activa el entorno **dentro del directorio del módulo**.