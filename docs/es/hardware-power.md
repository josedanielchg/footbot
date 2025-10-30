# 🔌 Hardware y Alimentación — Guía de Electrónica y Cableado

---

## Tabla de contenidos
- [Lista de componentes](#list-of-components)
- [Diseño del circuito](#circuit-design-layout)
- [Conexiones y topología](#connections--topology)
- [Notas de alimentación y seguridad](#power-notes--safety)
- [Pendientes por completar](#placeholders-to-fill-later)

---

## Lista de componentes

### ESP32-CAM (AI-Thinker)
- **Función:** Cámara integrada + Wi-Fi; aloja servidores HTTP y endpoints del motor.
- **Alimentación:** Entrada **5 V** (pin **5V**); picos típicos **~300–500 mA** con cámara/LED.
<p align="center">
  <img src="../src/Pinlayout_ESPCam.jpg" alt="Distribución de pines ESP32-CAM" width="520" />
</p>

### Controlador de motores L298N (Doble puente H)
- **Función:** Etapa de potencia/nivel que acciona dos motores DC y distribuye la energía de la batería.
- **Suministro (Vs):** **3.3 V de litio** (ver notas de alimentación más abajo).
- **Lógica:** 5 V (del regulador integrado en el L298N o de una fuente externa de 5 V).

> **Nota:** Muchas placas L298N esperan **Vs ≥ 5–7 V** para operar de forma fiable. Si debes mantener una batería de **3.3 V**, considera un **convertidor elevador** a 5–7.4 V **o** un **driver de bajo voltaje** (p. ej., TB6612FNG) en lugar del L298N.

### Dos motores DC con reductora
- **Voltaje nominal:** **6 V**
- **Velocidad en vacío:** **≈ 360 rpm**
- **Diámetro del eje:** **3 mm**
- **Diámetro del motor:** **12 mm**
- **Longitud del cuerpo (sin eje):** **≈ 26 mm**
- **Longitud axial del eje de salida:** **≈ 10 mm** (plano ~**4.4 mm**)
- **Par de bloqueo (stall):** **≈ 16 kgf·cm**
- **Par en operación:** **≈ 2 kgf·cm**
- **Peso del producto:** **≈ 0.010 kg**
- **Tamaño del motor:** **≈ 36 × 12 mm**
- **Tamaño del eje:** **≈ 3 × 2.5 mm** (D × L)

### Paquete de baterías
- **Química / Voltaje:** **Litio, 3.3 V** (capacidad desconocida / no especificada)
- **Interruptor principal:** **Interruptor en línea** que controla la **entrada de alimentación (Vs) del L298N**.

---

## Diseño del circuito

<p align="center">
  <img src="../src/circuit_overview.png" alt="Visión general: ESP32-CAM, L298N, batería, motores" width="640" />
  <br><em>Figura A — Vista general del circuito</em>
</p>

<p align="center">
  <img src="../src/wiring_diagram.jpeg" alt="Diagrama de cableado: conexiones pin a pin y rieles de alimentación" width="640" />
  <br><em>Figura B — Diagrama de cableado</em>
</p>

---

## Conexiones y topología

- La **batería (3.3 V litio)** alimenta el **Vs del L298N** a través del **interruptor principal**.
- Los **dos motores DC** se conectan a **OUT1/OUT2** y **OUT3/OUT4** en el L298N.
- La **ESP32-CAM** conecta sus **GPIO de control de motor** a **IN1…IN4** del L298N (y **ENA/ENB** si se habilita PWM).
- **Tierras:** Debe compartirse **GND común** entre **batería, L298N y ESP32-CAM**.
- La **ESP32-CAM** se alimenta a **5 V** por su **pin 5V**.

---

## Notas de alimentación y seguridad

- **Batería de 3.3 V → L298N:** El L298N normalmente rinde por debajo de 5 V. Para mejores resultados:
  - Usa un **convertidor elevador** (3.3 V → 5–7.4 V) para **Vs**, **o**
  - Cambia a un **driver de bajo consumo/bajo voltaje** (p. ej., **TB6612FNG**, DRV8833).
- **Riel de 5 V de la ESP32-CAM:** Asegura una **fuente de 5 V estable** capaz de **≥ 500 mA** en picos (cámara + Wi-Fi + LED).
- La **tierra común** es obligatoria para evitar control errático de los motores.
- Añade un **fusible en serie** y **calibre de cable** adecuado en la línea de batería si más adelante usas paquetes de mayor corriente.