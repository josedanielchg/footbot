## 🎯 Conclusión, Resultados y Desafíos

### Conclusión
Este proyecto demuestra un bucle completo **percibir → interpretar → ordenar → actuar** en dos modos:
- **Manual Control** — ✅ Totalmente operativo. Teleoperación por gestos en tiempo real desde la webcam del portátil (MediaPipe + OpenCV) con comandos JSON a `/move` limitados en frecuencia. Ver [`manual_control/`](manual_control.md).
- **Automatic Mode** — 🟡 Fundamentos en marcha. El flujo (ingesta HTTPX → detección híbrida → máquina de estados → `/move`) funciona con **seguidor de pelota**. Los detectores de **Goal** y **Opponent** están **entrenados y documentados** en [`soccer_vision.md`](soccer_vision.md) pero **aún no integrados** en la máquina de estados. Ver [`auto_soccer_bot/`](auto_soccer_bot.md).

### Resultados actuales
- **Teleoperación manual**: Estable a tasas interactivas en portátiles comunes; control fluido gracias a **limitación de tasa + antirrebote**.
- **Autonomía (pelota)**: Seguimiento robusto mediante **detector híbrido** (YOLO programado + HSV por fotograma) y una **FSM** que centra y avanza con giros suaves.
- **Streaming**: Menor retardo percibido tras cambiar a **HTTPX** con retención de **“solo el último fotograma”**; MJPEG **QVGA** reduce coste de decodificación.

### Desafíos clave y mitigaciones
- **Latencia / buffering del stream** → Cambio a **HTTPX** con parseo multipart explícito y descarte de fotogramas obsoletos.
- **Robustez vs. velocidad en percepción** → **YOLO cada _N_ fotogramas** + **HSV** en todos; salida unificada `(cx, cy, area)`.
- **Saturación de comandos** → **Deduplicación + límites de tasa** en el comunicador para no saturar el ESP32.
- **Oscilaciones del controlador** → **Corredor objetivo**, contadores de confirmación y *grace timeouts* en la FSM para alineación más estable.

### Próximos pasos
1. **Cablear las salidas de goal/opponent** desde [`soccer_vision`](soccer_vision.md) al bucle en vivo.
2. **Ampliar la FSM** con **fusión multiobjeto** (pelota + arco + oponente) para alineación de tiro y evitación de colisiones.
3. **Evaluación cuantitativa**: pruebas curadas (precisión/recuerdo, latencias) y *checks* de regresión para mantener el comportamiento.