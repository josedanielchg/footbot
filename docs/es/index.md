# Auto Soccer Bot — Robot Futbolista con ESP32 🤖⚽️

[English](../../README.md) · [Español](#) · [Français](../fr/index.md)

> Robot con ESP32 que juega al fútbol en **dos modos** — **manual** por gestos de la mano y **automático** con seguimiento del balón usando visión en el portátil.

---

## 🇪🇸 Español

### Introducción
Este proyecto es un **robot futbolista controlado por un ESP32**. Funciona en dos modos:

- **Control manual** — Una webcam en el portátil detecta **gestos de la mano**; el portátil interpreta el gesto y **envía comandos al ESP32** para mover el robot.  
- **Modo automático** — La ESP32-CAM transmite vídeo a un portátil que realiza **detección de objetos** (balón, arco/portería, oponente) y **envía comandos de movimiento** (adelante, izquierda, derecha, atrás) de vuelta al robot.

> **Estado actual:** Completamos el **seguimiento del balón** (detección + toma de decisiones) y entrenamos un **detector de oponentes**. **No** finalizamos el **detector de arcos/portería** ni la **fusión de decisiones multi-objeto** (oponente + arco).

---

## Tabla de contenidos

- 📚 **Documentación (multilenguaje)**
  - 🇬🇧 [Docs — EN](../../README.md)
  - 🇪🇸 [Docs — ES](#)
  - 🇫🇷 [Docs — FR](../fr/index.md)
- 🧭 [**Cómo funciona**](#cómo-funciona)
- 🗂️ **Estructura del repositorio**
- 🧪 **Estado del proyecto**
- 🚀 **Inicio rápido**
- ⚙️ **Componentes**
  - Firmware (ESP32-CAM): [`/esp32cam_robot`](esp32cam_robot/README.md)
  - Control manual (gestos): [`/manual_control`](manual_control/)
  - Modo automático (visión + control): [`/auto_soccer_bot`](auto_soccer_bot/)
  - Entrenamiento del detector de oponentes: [`/opponent-detector`](opponent-detector/README.md)
- 📄 **Licencia**

---

## Cómo funciona

<p align="center">
  <img src="src/figure,1.png" alt="Figura 1. Arquitectura del sistema" />
</p>

**Figura 1.** Arquitectura y flujo de datos del Auto Soccer Bot (ESP32) en modos manual y automático.
