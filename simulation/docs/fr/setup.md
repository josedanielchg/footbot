# Configuration

Le stack de simulation pris en charge est :

```text
Ubuntu 22.04 jammy
ROS 2 Humble Hawksbill
Gazebo Fortress
ros-humble-ros-gz
Python 3.10
```

Utilisez [install-ubuntu-22-04.md](install-ubuntu-22-04.md) pour les étapes
détaillées d'installation avec apt. La décision du stack et les notes de migration
future se trouvent dans [stack-decision.md](stack-decision.md).

## Vérifications de base

```bash
source /opt/ros/humble/setup.bash
ros2 doctor
ros2 pkg list | grep ros_gz
ign gazebo --versions
```

Résultat attendu :

- La CLI ROS 2 est disponible.
- `ros_gz_bridge` et `ros_gz_sim` sont détectables.
- Gazebo indique des versions Fortress/Ignition Gazebo.

## Dépendances Python optionnelles

Perception des gestes :

```bash
python3 -m pip install --user --force-reinstall "numpy==1.26.4" "mediapipe==0.10.14"
```

Vision de foot par YOLO :

```bash
python3 -m pip install --user -r simulation/requirements-yolo.txt
```

Gardez NumPy en `1.26.4` pour ce flux de travail Ubuntu 22.04. NumPy 2.x peut
casser les wheels binaires de ROS, OpenCV, Matplotlib et MediaPipe.

## Premier build

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot
source /opt/ros/humble/setup.bash
cd simulation/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

Vérifiez la visibilité des paquets :

```bash
colcon list --base-paths src
ros2 pkg list | grep footbot
```
