# Simulación FootBot — ROS 2 + Gazebo 🤖⚽

[English](../../README.md) · [Español](README.md) · [Français](../fr/README.md)

> Migración «simulation-first» de FootBot usando **ROS 2 Humble** y **Gazebo
> Fortress**. Esta capa mantiene disponibles como referencia las apps legacy de
> ESP32 y Python, a la vez que añade spawn del robot, datos de cámara simulada,
> control nativo de ROS, percepción de fútbol y experimentos autónomos de control
> de pelota.

<p align="center">
  <img src="src/simulation-overview.png" alt="Captura del overview de la simulación de FootBot" />
</p>

**Figura 1.** FootBot generado en Gazebo con la cámara simulada del robot, la
iluminación y los objetos de validación visibles.

---

## De un vistazo

- 🤖 **Modelo del robot:** modelo Xacro de FootBot con ruedas, rueda loca (caster), cámara y plugins de Gazebo.
- 🎮 **Control:** `/cmd_vel`, HTTP `/move` legacy y control por gestos nativo de ROS.
- 👁️ **Percepción:** cámara simulada, detección HSV de la pelota, plumbing del detector YOLO y herramientas de datasets.
- ⚽ **Mundos de fútbol:** pruebas de cámara, escenarios de control de pelota, pruebas multi-carril, porterías, paredes y equipos.
- 🧠 **Autonomía:** FSM deterministas de Control de pelota y Reach Goal; robar la pelota y la estrategia de equipo están solo planificadas.

> **Regla de control:** ejecuta solo un propietario de `/cmd_vel` a la vez.

---

## Tabla de contenidos

- 📚 [Índice de docs](README.md)
- 🚀 [Configuración](setup.md)
- 🧱 [Workspace](workspace.md)
- 🧭 [Arquitectura](architecture.md)
- 🎮 [Modos de simulación](modes.md)
- ⚽ [Control de pelota](ball-control.md)
- 🥅 [Reach goal con la pelota](reach-goal.md)
- 👁️ [Percepción y datasets](perception-and-datasets.md)
- 🌍 [Mundos y escenarios](worlds-and-scenarios.md)
- 🧪 [Resolución de problemas](troubleshooting.md)
- 🛠️ [Guía de desarrollo](development-guide.md)
- 🗺️ [Etapas de fútbol planificadas](planned-soccer-stages.md)

---

## Inicio rápido

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Simulación base:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py
```

Ejemplo actual de control de pelota autónomo:

```bash
ros2 launch footbot_bringup ball_control.launch.py scenario:=front show_debug_view:=true
```

Escena de visión de reach-goal:

```bash
ros2 launch footbot_bringup reach_goal.launch.py show_debug_view:=true
```

Vista general del campo de fútbol:

```bash
ros2 launch footbot_bringup soccer_field.launch.py
```

Preparación del dataset de YOLO:

```bash
python3 simulation/ros2_ws/src/footbot_soccer_vision/datasets/validate_yolo_dataset.py \
  --dataset-dir simulation/ros2_ws/src/footbot_soccer_vision/datasets/exports/reach_goal_ball_goal_v1 \
  --require-splits train val
```

Consulta los [modos de simulación](modes.md) para el resto de los comandos de
lanzamiento.
