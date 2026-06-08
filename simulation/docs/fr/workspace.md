# Workspace

Le workspace ROS 2 se trouve dans :

```text
simulation/ros2_ws/
```

Les dossiers générés sont ignorés par Git :

```text
simulation/ros2_ws/build/
simulation/ros2_ws/install/
simulation/ros2_ws/log/
```

## Paquets

| Paquet | Type de build | Responsabilité |
| --- | --- | --- |
| `footbot_common` | `ament_python` | Constantes partagées de topics, frames, géométrie et mathématiques. |
| `footbot_description` | `ament_cmake` | Modèle Xacro du robot, frames, roues, capteur caméra, configuration RViz. |
| `footbot_gazebo` | `ament_cmake` | Mondes Gazebo, modèles, configuration du pont, plugin de traînée de la balle. |
| `footbot_bringup` | `ament_cmake` | Orchestration de lancement pour tous les modes de simulation. |
| `footbot_bridge` | `ament_python` | Pont HTTP `/move` compatible ESP32 vers `/cmd_vel` de ROS. |
| `footbot_perception` | `ament_python` | Webcam, détection des mains, détection HSV de la balle, visionneuse d'images de débogage. |
| `footbot_control` | `ament_python` | Contrôleurs geste-à-vitesse et suiveur de balle simple. |
| `footbot_soccer_msgs` | `ament_cmake` | Messages de comportement de foot personnalisés comme `BallState`. |
| `footbot_soccer_behavior` | `ament_python` | Estimation d'état, skills et FSM du contrôle de balle. |
| `footbot_soccer_vision` | `ament_python` | Perception de foot par YOLO, capture de datasets, outils d'augmentation. |

## Compiler et sourcer

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Sourcez à nouveau `install/setup.bash` après chaque build et dans chaque nouveau
terminal.

## Vérifications utiles

```bash
colcon list --base-paths src
ros2 pkg executables footbot_perception
ros2 pkg executables footbot_soccer_behavior
ros2 launch footbot_bringup ball_control.launch.py --show-args
```
