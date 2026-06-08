# Guide de développement

## Limites

- Gardez le travail d'implémentation à l'intérieur de `simulation/` sauf si une tâche dit explicitement le contraire.
- Ne modifiez pas `esp32cam_robot/` ni `manual_control/` pour les refactors de simulation.
- Gardez les modes de simulation stables séparés des expériences.
- Ne committez pas la sortie de build générée, les datasets, les virtualenvs, les poids de modèles ni les caches.

## Lignes directrices par paquet

- Mettez les constantes partagées et les petits helpers dans `footbot_common`.
- Mettez les modifications du modèle du robot dans `footbot_description`.
- Mettez les mondes, modèles et plugins Gazebo dans `footbot_gazebo`.
- Mettez l'orchestration de lancement dans `footbot_bringup`.
- Mettez la perception générique dans `footbot_perception`.
- Mettez les outils YOLO et datasets spécifiques au foot dans `footbot_soccer_vision`.
- Mettez la FSM de comportement de foot, l'estimation d'état et les skills dans `footbot_soccer_behavior`.

## Checklist de validation

```bash
git status -sb
source /opt/ros/humble/setup.bash
cd simulation/ros2_ws
colcon build --symlink-install
source install/setup.bash
colcon list --base-paths src
ros2 pkg list | grep footbot
```

Compilez Python :

```bash
python3 -m py_compile src/footbot_soccer_behavior/footbot_soccer_behavior/**/*.py
```

Vérifiez les arguments de lancement :

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py --show-args
ros2 launch footbot_bringup ball_control.launch.py --show-args
ros2 launch footbot_bringup reach_goal.launch.py --show-args
```

Vérifiez SDF/URDF :

```bash
ros2 run xacro xacro src/footbot_description/urdf/footbot.urdf.xacro > /tmp/footbot.urdf
check_urdf /tmp/footbot.urdf
ign sdf -k src/footbot_gazebo/worlds/footbot_soccer_field.sdf
ign sdf -k src/footbot_gazebo/worlds/footbot_reach_goal.sdf
```

## Règles de documentation

Pour l'instant, gardez la documentation canonique en anglais dans
`simulation/docs/en/`. Séparez le comportement implémenté du comportement prévu.
Préférez des documents courts ciblés sur un sujet plutôt qu'un unique fichier de
référence géant.
