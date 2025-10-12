# Hardware & Power — Electronics & Wiring Guide
---

## List of Components

* **ESP32-CAM (AI-Thinker)**

  * Role: on-board camera + Wi-Fi; runs the HTTP servers and motor endpoints.
  * Power: **5 V** input (on 5V pin); typical peak ~**300–500 mA** with camera/LED.
  <p align="center">
    <img src="../src/Pinlayout_ESPCam.jpg" alt="ESP32-CAM pinout" width="500px" />
    </p>

* **L298N Dual H-Bridge Motor Driver**

  * Role: level/power stage that drives two DC motors and distributes battery power.
  * Supply (Vs): **<BATTERY_VOLTAGE_V> V** *(TODO: fill later; e.g., 7.4 V for 2S Li-ion or 12 V pack)*
  * Logic: 5 V (from on-board regulator or external 5 V).

* **Two DC Gear Motors**

  * Specs (placeholders to fill):
    * Rated voltage: **<MOTOR_RATED_VOLTAGE_V> V**
    * Stall current: **<MOTOR_STALL_CURRENT_A> A** (per motor)
    * No-load current: **<MOTOR_NOLOAD_CURRENT_A> A**

* **Battery Pack**

  * Chemistry/voltage placeholder: **<BATTERY_CHEMISTRY>**, **<BATTERY_VOLTAGE_V> V**, **<BATTERY_CAPACITY_mAh> mAh**.

---

## Circuit Design Layout

> Coming Soon

---

### Placeholders to fill later (Remove later)

* `<BATTERY_VOLTAGE_V>`, `<BATTERY_CAPACITY_mAh>`, `<MOTOR_RATED_VOLTAGE_V>`, `<MOTOR_STALL_CURRENT_A>`, `<MOTOR_NOLOAD_CURRENT_A>`, `<5V_REGULATOR_CURRENT_A>`, `<SWITCH_CURRENT_A>`, `<AWG>`, `<AWG_5V>`, and all `<GPIO_…>` values.
* Image files for the **ESP32-CAM pinout**, **L298N module**, **motors**, **power switch**, **battery**, and the **wiring diagram**.