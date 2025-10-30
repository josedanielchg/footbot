## 🧪 Estado del proyecto

- **Control manual (teleoperación por gestos)** — ✅ **Funciona de extremo a extremo.**  
  Corre en tiempo real en un portátil usando **OpenCV + MediaPipe**; los comandos se envían como JSON por HTTP a `/move` con **limitación de tasa y antirrebote**. Estable en hardware convencional.

- **Modo automático (visión en el bucle)** — 🟡 **Capas construidas, no totalmente integradas.**  
  - **Ingesta de flujo:** lector MJPEG de **HTTPX** desde `http://<ESP32_IP>:81/stream` — **listo**.  
  - **Percepción:**  
    - **Balón** — detector **activo** en el bucle.  
    - **Portería** y **Oponente** — modelos **entrenados y disponibles** en [`soccer_vision.md`](soccer_vision.md), pero **aún no conectados** al bucle en vivo.  
  - **Decisión:** mini **máquina de estados** con **seguidor de balón** únicamente (sin fusión multiobjeto por ahora).  
  - **Actuación:** POST HTTP a `/move` — **listo**.

- **Limitación actual** — La autonomía es de **objetivo único (balón)**; funciones como **alineación de tiro** y **evitación de oponentes** dependen de integrar portería/oponente en el controlador.

- **Próximos pasos (corto plazo)**  
  1) Conectar **portería/oponente** al bus de percepción.  
  2) Ampliar la máquina de estados con **fusión multiobjeto** y transiciones.  
  3) Afinar umbrales/ganancias y añadir pruebas de regresión en lazo cerrado.