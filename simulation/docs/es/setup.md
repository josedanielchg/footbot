# Configuración

El stack de simulación soportado es:

```text
Ubuntu 22.04 jammy
ROS 2 Humble Hawksbill
Gazebo Fortress
ros-humble-ros-gz
Python 3.10
```

Usa [install-ubuntu-22-04.md](install-ubuntu-22-04.md) para los pasos detallados
de instalación con apt. La decisión del stack y las notas de migración futura
están en [stack-decision.md](stack-decision.md).

## Comprobaciones base

```bash
source /opt/ros/humble/setup.bash
ros2 doctor
ros2 pkg list | grep ros_gz
ign gazebo --versions
```

Resultado esperado:

- La CLI de ROS 2 está disponible.
- `ros_gz_bridge` y `ros_gz_sim` son detectables.
- Gazebo informa versiones de Fortress/Ignition Gazebo.

## Dependencias de Python opcionales

Percepción de gestos:

```bash
python3 -m pip install --user --force-reinstall "numpy==1.26.4" "mediapipe==0.10.14"
```

Visión de fútbol con YOLO:

```bash
python3 -m pip install --user -r simulation/requirements-yolo.txt
```

Mantén NumPy en `1.26.4` para este flujo de trabajo de Ubuntu 22.04. NumPy 2.x
puede romper los wheels binarios de ROS, OpenCV, Matplotlib y MediaPipe.

## Primer build

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot
source /opt/ros/humble/setup.bash
cd simulation/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

Comprueba la visibilidad de los paquetes:

```bash
colcon list --base-paths src
ros2 pkg list | grep footbot
```
