# Dépannage

## Paquet du workspace introuvable

```bash
source /opt/ros/humble/setup.bash
cd simulation/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 pkg list | grep footbot
```

## Le robot ne bouge pas

Vérifiez la propriété du topic :

```bash
ros2 topic info /cmd_vel
ros2 topic echo /cmd_vel
```

N'exécutez qu'un seul mode de contrôle à la fois.

## Topic caméra manquant

```bash
ros2 topic list | grep camera
ign topic -l | grep camera
```

Si Gazebo a le topic mais pas ROS, inspectez les arguments de `ros_gz_bridge` dans
le fichier de lancement actif.

## Le contrôle de balle tourne indéfiniment

Vérifiez la caméra du robot et la détection de la balle :

```bash
ros2 topic hz /camera/image_raw
ros2 topic echo /ball_detection
ros2 topic echo /soccer/ball_state
ros2 topic echo /soccer/fsm_state
```

Utilisez `show_debug_view:=true` pour voir la superposition (overlay) du détecteur.

## Erreurs d'import YOLO ou NumPy

Réinstallez les dépendances optionnelles épinglées :

```bash
python3 -m pip install --user --force-reinstall -r simulation/requirements-yolo.txt
```

Évitez NumPy 2.x avec cette configuration ROS/OpenCV/MediaPipe d'Ubuntu 22.04.

## La balle roule trop longtemps

Confirmez que le plugin de traînée de la balle est installé et que le monde le
charge :

```bash
cd simulation/ros2_ws
colcon build --symlink-install --packages-select footbot_gazebo footbot_bringup
source install/setup.bash
```

Puis relancez la simulation. Les processus Gazebo existants doivent être redémarrés
pour charger un plugin recompilé.
