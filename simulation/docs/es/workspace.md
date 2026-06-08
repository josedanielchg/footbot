# Workspace

El workspace de ROS 2 vive en:

```text
simulation/ros2_ws/
```

Las carpetas generadas están ignoradas por Git:

```text
simulation/ros2_ws/build/
simulation/ros2_ws/install/
simulation/ros2_ws/log/
```

## Paquetes

| Paquete | Tipo de build | Responsabilidad |
| --- | --- | --- |
| `footbot_common` | `ament_python` | Constantes compartidas de topics, frames, geometría y matemáticas. |
| `footbot_description` | `ament_cmake` | Modelo Xacro del robot, frames, ruedas, sensor de cámara, configuración de RViz. |
| `footbot_gazebo` | `ament_cmake` | Mundos de Gazebo, modelos, configuración del puente, plugin de arrastre de la pelota. |
| `footbot_bringup` | `ament_cmake` | Orquestación de lanzamiento para todos los modos de simulación. |
| `footbot_bridge` | `ament_python` | Puente HTTP `/move` compatible con ESP32 hacia `/cmd_vel` de ROS. |
| `footbot_perception` | `ament_python` | Webcam, detección de manos, detección HSV de la pelota, visor de imágenes de depuración. |
| `footbot_control` | `ament_python` | Controladores de gesto-a-velocidad y seguidor de pelota simple. |
| `footbot_soccer_msgs` | `ament_cmake` | Mensajes personalizados de comportamiento de fútbol como `BallState`. |
| `footbot_soccer_behavior` | `ament_python` | Estimación de estado, skills y FSM del control de pelota. |
| `footbot_soccer_vision` | `ament_python` | Percepción de fútbol con YOLO, captura de datasets, herramientas de aumento. |

## Compilar y hacer source

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Haz source de `install/setup.bash` de nuevo después de cada build y en cada
terminal nueva.

## Comprobaciones útiles

```bash
colcon list --base-paths src
ros2 pkg executables footbot_perception
ros2 pkg executables footbot_soccer_behavior
ros2 launch footbot_bringup ball_control.launch.py --show-args
```
