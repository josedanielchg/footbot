# Modes de simulation

Compilez et sourcez avant de lancer n'importe quel mode :

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Mode manuel de base

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py
```

Démarre Gazebo, fait apparaître (spawn) le robot, fait le pont des topics
`/cmd_vel`, `/odom` et caméra, et démarre le pont HTTP par défaut.

Exemple de commande HTTP :

```bash
curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"forward","speed":150}'
```

## Mode gestes natif ROS

```bash
ros2 launch footbot_bringup sim_gesture_control.launch.py show_debug_view:=true
```

Utilise la webcam de l'ordinateur, la détection des mains de MediaPipe, les topics
de gestes et `gesture_to_cmd_vel`.

## Suiveur de balle simple

```bash
ros2 launch footbot_bringup ball_following.launch.py show_debug_view:=true
```

C'est un simple détecteur HSV plus un suiveur de balle proportionnel. C'est utile
comme test de fumée de perception/contrôle, mais ce n'est pas le comportement de
foot principal.

## Contrôle de balle déterministe

```bash
ros2 launch footbot_bringup ball_control.launch.py scenario:=front show_debug_view:=true
```

C'est le comportement de foot autonome fondamental pour la possession de la balle.
Voir [ball-control.md](ball-control.md).

## Test multi-couloirs du contrôle de balle

```bash
ros2 launch footbot_bringup ball_control_multi.launch.py show_debug_view:=true
```

Exécute des scénarios isolés balle devant, loin et derrière dans un seul monde
avec des topics dans des namespaces séparés.

## Reach Goal avec la balle

```bash
ros2 launch footbot_bringup reach_goal.launch.py \
  model_path:=/media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws/src/footbot_soccer_vision/models/reach_goal_ball_goal/reach_goal_ball_goal_v1_best.pt \
  show_debug_view:=true \
  run_behavior:=true
```

Démarre un FootBot contrôlable, une balle dynamique devant lui, un but plus loin,
le pont de la caméra du robot sur `/camera/image_raw`, le détecteur YOLO de Reach
Goal sur `/soccer/detections`, l'estimateur d'état balle+but, le moniteur de score
de simulation sur `/soccer/goal_scored`, et la FSM reach-goal qui pousse la balle
vers le but.

Dans ce mode, seule la FSM de Reach Goal possède `/cmd_vel`. Passez
`run_behavior:=false` pour n'inspecter que la perception. Passez
`run_score_monitor:=false` uniquement lors du débogage de l'arbitre séparément.
Voir [reach-goal.md](reach-goal.md).

## Modes de foot uniquement perception

```bash
ros2 launch footbot_bringup opponent_detection.launch.py show_debug_view:=true
ros2 launch footbot_bringup soccer_detection.launch.py show_debug_view:=true
```

Ces modes observent les images caméra et publient des détections/images de
débogage. Ils ne possèdent pas `/cmd_vel`.

`soccer_detection.launch.py` utilise le topic caméra du terrain de foot
`/soccer/camera/image_raw`. La scène Reach-goal utilise le topic de la caméra
montée sur le robot `/camera/image_raw`.

## Visualisation du terrain de foot

```bash
ros2 launch footbot_bringup soccer_field.launch.py
```

Ouvre le terrain avec des murs, des buts, une balle centrale et des équipes
statiques en miroir.
