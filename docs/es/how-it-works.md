## ⚙️ Cómo funciona

Esta sección detalla el flujo de datos extremo a extremo y los lazos de control para el **Modo Manual** y el **Modo Automático**, tal como se resume en la **Figura 1**. La arquitectura general sigue el ciclo **sensar → interpretar → comandar → actuar**, donde el **portátil** aporta los módulos de percepción/decisión y el **ESP32** ejecuta la actuación de bajo nivel.

<p align="center">
  <img src="src/figure,1.png" alt="Figura 1. Arquitectura del sistema y flujo de datos para los modos manual y automático." />
</p>

**Figura 1.** Arquitectura del sistema y flujo de datos del Auto Soccer Bot (ESP32) en modos manual y automático.

---

## Tabla de contenidos

- [1) Control Manual (teleoperación por gestos)](#1-control-manual-teleoperación-por-gestos)
- [2) Modo Automático (visión en el bucle)](#2-modo-automático-visión-en-el-bucle)
- [Responsabilidades de los componentes](#responsabilidades-de-los-componentes)

---

### 1) Control Manual (teleoperación por gestos)

**Objetivo.** Permitir que un usuario dirija el robot con gestos de la mano capturados por la webcam del portátil.

**Pipeline.**
1. **Sensado — Webcam en el portátil.** Se capturan fotogramas RGB a la resolución nativa de la cámara y se envían al proceso local.
2. **Percepción — Detección y clasificación de gestos.** Cada fotograma se preprocesa y se pasa por el pipeline de gestos para inferir una clase de comando discreta (p. ej., *forward*, *left*, *right*, *backward*, *stop*).
3. **Decisión/Codificación — Codificador de comandos.** El gesto predicho se mapea a primitivas de movimiento (consignas lineales/angulares) y se codifica como solicitudes HTTP.
4. **Actuación — Robot ESP32.** Los comandos se envían por **Wi-Fi/HTTP** al ESP32, que analiza la carga útil y actualiza los PWM de los motores vía el driver.

**Notas.**
- Este bucle está **totalmente implementado** y corre en tiempo real en portátiles convencionales.
- La comunicación es sin estado (request/response); el portátil aplica limitación de tasa y *debounce* para evitar saturación de comandos.

<p align="center">
  <img src="../src/picture1.jpg" alt="Figura 2. Ejemplo de puntos clave de la mano y superposición de gestos usados para control manual." />
</p>

**Figura 2.** Superposición de la tubería de gestos mostrando puntos clave detectados para la teleoperación manual.

---

### 2) Modo Automático (visión en el bucle)

**Objetivo.** Cerrar el lazo percepción→control usando una pila de visión en el portátil alimentada por el flujo de la ESP32-CAM.

**Pipeline.**
1. **Sensado — ESP32-CAM (vídeo en streaming).** La ESP32-CAM expone un flujo MJPEG (o equivalente) por Wi-Fi.
2. **Percepción — Pipeline de visión en el portátil.** El portátil se suscribe al flujo y realiza detección de objetos para localizar:
   - **Pelota** — ✓ implementado (detector operativo en el bucle en vivo).
   - **Arco (Goal)** — **modelo entrenado y disponible** en [`soccer_vision`](soccer_vision.md), **aún no integrado** en el bucle en vivo.
   - **Oponente** — **modelo entrenado y disponible** en [`soccer_vision`](soccer_vision.md), **aún no integrado** en el bucle en vivo.
3. **Decisión — Controlador / máquina de estados.**
   - **Seguidor de pelota** — ✓ implementado (girar/avanzar según la pose de la pelota en imagen).
   - **Fusión multiobjeto** (pelota + arco + oponente) — ✗ no implementado; la máquina de estados mínima actual ignora arco/oponente aunque existan modelos.
4. **Actuación — Robot ESP32.** El movimiento elegido se codifica como comandos HTTP y se transmite al ESP32, que actualiza las salidas de motor.

**Notas.**
- La autonomía actual es **seguimiento de un único objetivo** (pelota). Los detectores de arco/oponente están entrenados (ver [`soccer_vision.md`](soccer_vision.md)) pero **no integrados** aún; por ello, funciones como alineación de tiro o evasión de colisiones están pendientes.
- Percepción y actuación están desacopladas, permitiendo futuras mejoras (p. ej., enganchar arco/oponente en la máquina de estados) sin cambios de firmware.

<p align="center">
  <img src="../src/picture2.jpg" alt="Figura 3. Detección de la pelota y estado del controlador durante el modo automático." />
</p>

**Figura 3.** Ejemplo del detector de pelota y estado del controlador durante la operación automática (la línea vertical izquierda marca el centro de la imagen; ‘Cmd’ muestra la orden emitida).

---

### Responsabilidades de los componentes

| Capa          | Componente                 | Responsabilidad                                                                                        | Estado                      |
|---------------|----------------------------|--------------------------------------------------------------------------------------------------------|-----------------------------|
| Sensado       | ESP32-CAM / Webcam laptop  | Captura de vídeo                                                                                       | ✓                           |
| Percepción    | Pipeline de visión (PC)    | **En vivo:** pelota (✓). **Modelos disponibles:** arco (✓), oponente (✓) — **integración PTE**         | Parcial                     |
| Decisión      | Controlador en el portátil | Seguidor de pelota (✓). Fusión multiobjeto con arco/oponente (✗, hay modelos pero no conectados)       | Parcial                     |
| Comunicación  | Wi-Fi/HTTP                 | Transporte de comandos (portátil → ESP32)                                                              | ✓                           |
| Actuación     | Firmware del robot ESP32   | Parseo de comandos; control PWM de motores                                                             | ✓                           |

**Leyenda:** ✓ Completado ✗ No implementado **PTE** Por integrar