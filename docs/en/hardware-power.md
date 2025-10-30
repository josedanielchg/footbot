# 🔌 Hardware & Power — Electronics & Wiring Guide

---

## Table of Contents
- [List of Components](#list-of-components)
- [Circuit Design Layout](#circuit-design-layout)
- [Connections & Topology](#connections--topology)
- [Power Notes & Safety](#power-notes--safety)
- [Placeholders to Fill Later](#placeholders-to-fill-later)

---

## List of Components

### ESP32-CAM (AI-Thinker)
- **Role:** On-board camera + Wi-Fi; hosts HTTP servers and motor endpoints.
- **Power:** **5 V** input (5V pin); typical peaks **~300–500 mA** with camera/LED.
<p align="center">
  <img src="../src/Pinlayout_ESPCam.jpg" alt="ESP32-CAM pinout" width="520" />
</p>

### L298N Dual H-Bridge Motor Driver
- **Role:** Power/level stage that drives two DC motors and distributes battery power.
- **Supply (Vs):** **3.3 V lithium** (see power notes below).
- **Logic:** 5 V (from onboard regulator on L298N or external 5 V).

> **Note:** Many L298N boards expect **Vs ≥ 5–7 V** for reliable operation. If you must keep a **3.3 V** battery, consider a **boost converter** to 5–7.4 V **or** a **low-voltage motor driver** (e.g., TB6612FNG) instead of L298N.

### Two DC Gear Motors
- **Rated voltage:** **6 V**
- **No-load speed:** **≈ 360 rpm**
- **Shaft diameter:** **3 mm**
- **Motor diameter:** **12 mm**
- **Body length (without shaft):** **≈ 26 mm**
- **Output shaft axial length:** **≈ 10 mm** (flat ~**4.4 mm**)
- **Stall torque:** **≈ 16 kgf·cm**
- **Running torque:** **≈ 2 kgf·cm**
- **Product weight:** **≈ 0.010 kg**
- **Motor size:** **≈ 36 × 12 mm**
- **Shaft size:** **≈ 3 × 2.5 mm** (D × L)

### Battery Pack
- **Chemistry / Voltage:** **Lithium, 3.3 V** (capacity unknown / not specified)
- **Master Switch:** Inline **power switch** controlling the **L298N supply input (Vs)**.

---

## Circuit Design Layout

<p align="center">
  <img src="../src/circuit_overview.png" alt="Circuit overview: ESP32-CAM, L298N, battery, motors" width="640" />
  <br><em>Figure A — Circuit overview</em>
</p>

<p align="center">
  <img src="../src/wiring_diagram.jpeg" alt="Wiring diagram: pin-to-pin connections and power rails" width="640" />
  <br><em>Figure B — Wiring diagram</em>
</p>

---

## Connections & Topology

- The **battery (3.3 V lithium)** feeds the **L298N Vs** through the **master switch**.
- The **two DC motors** connect to **OUT1/OUT2** and **OUT3/OUT4** on the L298N.
- The **ESP32-CAM** connects its **motor control GPIOs** to the L298N **IN1…IN4** (and **ENA/ENB** if PWM-enabled).
- **Grounds:** **Common GND** must be shared among **battery, L298N, and ESP32-CAM**.
- The **ESP32-CAM** itself is powered at **5 V** on its **5V pin**

---

## Power Notes & Safety

- **3.3 V battery → L298N:** L298N typically underperforms below 5 V. For best results:
  - Use a **boost converter** (3.3 V → 5–7.4 V) for **Vs**, **or**
  - Swap to a **low-drop, low-voltage driver** (e.g., **TB6612FNG**, DRV8833).
- **ESP32-CAM 5 V rail:** Ensure a **stable 5 V** supply capable of **≥ 500 mA** peaks (camera + Wi-Fi + LED).
- **Common ground** is mandatory to avoid erratic motor control.
- Add an **inline fuse** and proper **wire gauge** on the battery line if you later move to higher current packs.
