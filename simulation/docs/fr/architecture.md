# Architecture

La couche de simulation est isolée sous `simulation/` et ne devrait pas nécessiter
de modifications dans `esp32cam_robot/` ni `manual_control/`.

## Flux de données principal

```text
Monde Gazebo
  -> modèle du robot depuis footbot_description
  -> topics de caméra et d'odométrie de Gazebo Transport
  -> ros_gz_bridge
  -> topics ROS
```

Le déplacement utilise :

```text
/cmd_vel -> ros_gz_bridge -> plugin DiffDrive de Gazebo -> robot simulé
```

La perception caméra utilise :

```text
caméra Gazebo -> /camera/image_raw -> nœud de perception -> topics de détection/débogage
```

Le contrôle de balle utilise :

```text
/camera/image_raw
  -> footbot_perception ball_detector
  -> /ball_detection
  -> footbot_soccer_behavior ball_state_estimator
  -> /soccer/ball_state
  -> footbot_soccer_behavior ball_control_fsm
  -> /cmd_vel
```

Reach Goal utilise :

```text
/camera/image_raw
  -> footbot_soccer_vision yolo_detector
  -> /soccer/detections
  -> footbot_soccer_behavior ball_goal_state_estimator
  -> /soccer/ball_goal_state
  -> footbot_soccer_behavior reach_goal_fsm
  -> /cmd_vel
```

Le comptage des buts de Reach Goal relève de la logique d'arbitre de simulation :

```text
/world/footbot_world/pose/info
  -> footbot_soccer_behavior reach_goal_score_monitor
  -> /soccer/goal_scored
  -> reach_goal_fsm état GOAL_SCORED
```

Le moniteur de score arrête l'épisode après que la balle entre dans la zone de
but. Le robot ne l'utilise pas pour naviguer.

## Propriété du contrôle

Un seul nœud ou pont actif devrait publier des commandes significatives sur
`/cmd_vel` à la fois.

| Mode | Propriétaire de `/cmd_vel` |
| --- | --- |
| Simulation de base/manuelle | commandes humaines via topic ROS ou pont HTTP |
| Contrôle par gestes | `gesture_to_cmd_vel` |
| Suiveur de balle simple | `ball_follower` |
| Contrôle de balle | `ball_control_fsm` |
| Reach Goal | `reach_goal_fsm` |
| Détection d'adversaire/de but | aucun |
| Visualisation du terrain de foot | aucun |

## Code partagé

`footbot_common` contient les constantes partagées de topics, de frames, de
dimensions et de petits helpers mathématiques. Il doit rester léger et
réutilisable. La logique spécifique à un comportement appartient à
`footbot_soccer_behavior`, pas au code commun.

## Direction d'architecture prévue

Utiliser une orchestration par FSM ou FSM hiérarchique pour le comportement de
haut niveau, des skills pour les primitives de mouvement bornées, du contrôle
déterministe lorsque c'est pratique, et d'éventuels futurs modules de politique
pour les expériences tactiques.
