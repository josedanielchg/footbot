# Contrôle de balle

Le contrôle de balle est le seul comportement de foot autonome actuellement
implémenté. Il utilise une perception déterministe, une estimation d'état, des
skills et une FSM.

<p align="center">
  <img src="src/ball-control-debug.png" alt="Capture de débogage du contrôle de balle" />
</p>

**Figure 1.** Contrôle de balle s'exécutant dans Gazebo avec la visionneuse
d'images de débogage montrant la balle orange détectée et le retour d'état.

## Lancement

Compilez et sourcez d'abord :

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Exécutez le comportement de contrôle de balle à scénario unique :

```bash
ros2 launch footbot_bringup ball_control.launch.py scenario:=front show_debug_view:=true
```

Scénarios :

```text
front
left
right
far
close
misaligned
```

## Test multi-couloirs

Le lancement multi-couloirs démarre trois scénarios séparés par des murs dans un
seul monde Gazebo :

```text
front   la balle commence devant le robot
far     la balle commence plus loin
behind  la balle commence derrière le robot, donc le robot doit tourner pour chercher
```

Lancer sans fenêtres de débogage :

```bash
ros2 launch footbot_bringup ball_control_multi.launch.py
```

Lancer avec les fenêtres d'image de débogage :

```bash
ros2 launch footbot_bringup ball_control_multi.launch.py show_debug_view:=true
```

Dans un autre terminal, sourcez le workspace :

```bash
source /opt/ros/humble/setup.bash
source /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws/install/setup.bash
```

Listez les topics spécifiques à chaque couloir :

```bash
ros2 topic list | grep ball_control
```

Inspectez l'état de la FSM de chaque couloir :

```bash
ros2 topic echo /ball_control/front/soccer/fsm_state
ros2 topic echo /ball_control/far/soccer/fsm_state
ros2 topic echo /ball_control/behind/soccer/fsm_state
```

Inspectez l'état estimé de la balle :

```bash
ros2 topic echo /ball_control/front/soccer/ball_state
ros2 topic echo /ball_control/far/soccer/ball_state
ros2 topic echo /ball_control/behind/soccer/ball_state
```

Inspectez les commandes de vitesse :

```bash
ros2 topic echo /ball_control/front/cmd_vel
ros2 topic echo /ball_control/far/cmd_vel
ros2 topic echo /ball_control/behind/cmd_vel
```

Comportement attendu :

- `front` : détecte la balle rapidement et s'en approche.
- `far` : s'approche plus lentement car la balle commence plus loin.
- `behind` : tourne pour chercher avant de pouvoir s'aligner avec la balle.
- Chaque couloir utilise des topics isolés sous `/ball_control/<lane>/`.

## Topics

```text
/camera/image_raw
/ball_detection
/ball/debug_image
/soccer/ball_state
/soccer/fsm_state
/cmd_vel
```

## Nœuds

| Nœud | Paquet | Rôle |
| --- | --- | --- |
| `ball_detector` | `footbot_perception` | Détection HSV de la balle orange depuis la caméra du robot. |
| `ball_state_estimator` | `footbot_soccer_behavior` | Convertit `Detection2D` en `BallState`. |
| `ball_control_fsm` | `footbot_soccer_behavior` | Choisit les skills et publie `/cmd_vel`. |

## États de la FSM

```text
SEARCH_BALL
ALIGN_TO_BALL
APPROACH_BALL
CONTACT_BALL
CONTROL_BALL
ROTATE_WITH_BALL
RECOVER_BALL
STOP_SAFE
```

La FSM possède les transitions. Les skills ne produisent que des commandes `Twist`
bornées pour l'état actuel.

## Valeurs par défaut partagées

Les paramètres par défaut sont documentés dans :

```text
simulation/ros2_ws/src/footbot_soccer_behavior/config/ball_control.yaml
```

L'estimateur utilise le rayon apparent de la balle et le FOV de la caméra pour
estimer une portée approximative. C'est adapté à la simulation, mais ce n'est pas
un estimateur de pose 3D calibré.

## Limites actuelles

Ce comportement ne tire pas, ne marque pas de buts, ne vole pas la balle aux
adversaires, ne coordonne pas une équipe et n'utilise pas l'apprentissage par
renforcement.
