# Reach Goal avec la balle

Reach Goal est le comportement autonome de production pour conduire la balle dans
un but visible. Un FootBot utilise sa caméra montée sur le robot, un détecteur
YOLO `ball`+`goal`, un estimateur d'état dérivé de l'image, des skills bornées et
une machine à états finis pour pousser la balle vers un but visible. Chaque
décision de contrôle est guidée par la perception ; le comportement ne lit jamais
les poses ground-truth de Gazebo.

## Lancement

Compilez et sourcez d'abord :

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Exécutez le comportement Reach-goal avec le modèle entraîné :

```bash
ros2 launch footbot_bringup reach_goal.launch.py \
  model_path:=/media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws/src/footbot_soccer_vision/models/reach_goal_ball_goal/reach_goal_ball_goal_v1_best.pt \
  show_debug_view:=true \
  run_behavior:=true
```

Le lancement démarre le monde Gazebo de reach-goal, fait apparaître le FootBot,
fait apparaître la balle, exécute le détecteur YOLO, ouvre la visionneuse de
débogage optionnelle, et démarre l'estimateur d'état balle+but de reach-goal, le
moniteur de score de simulation et la FSM reach-goal. Il ne démarre **pas** le pont
HTTP, le contrôleur de gestes, le suiveur de balle simple ni la FSM de Contrôle de
balle.

Mettez `run_behavior:=false` pour n'inspecter que la perception (sans mouvement du
robot).

## Arguments de lancement

```text
model_path              chemin absolu vers les poids entraînés ball+goal
run_behavior            démarre l'estimateur + FSM (par défaut true)
run_score_monitor       démarre l'arbitre de score de simulation (par défaut true)
show_debug_view         ouvre la fenêtre d'image de débogage YOLO (par défaut true)
confidence_threshold    seuil de score YOLO (par défaut 0.25 ; baissez-le pour déboguer)
detections_topic        /soccer/detections
ball_goal_state_topic   /soccer/ball_goal_state
fsm_state_topic         /soccer/reach_goal_fsm_state
goal_scored_topic       /soccer/goal_scored
ball_pose_topic         /reach_goal/ball_pose
world_pose_topic        /world/footbot_world/pose/info
ball_entity_name        reach_goal_ball
cmd_vel_topic           /cmd_vel
camera_topic            /camera/image_raw
```

## Topics

```text
/camera/image_raw          caméra du robot (entrée)
/soccer/detections         Detection2DArray ball+goal de YOLO
/soccer/detections/debug_image
/soccer/ball_goal_state    footbot_soccer_msgs/BallGoalState (dérivé de l'image)
/soccer/reach_goal_fsm_state   std_msgs/String état actuel de la FSM
/soccer/goal_scored        std_msgs/Bool signal de but de l'arbitre de simulation
/world/footbot_world/pose/info
                          tf2_msgs/TFMessage flux de poses du monde Gazebo
/reach_goal/ball_pose          geometry_msgs/Pose optionnel, entrée directe de pose de la balle
/cmd_vel                   geometry_msgs/Twist (FSM uniquement)
```

Inspectez-les pendant que le comportement s'exécute :

```bash
ros2 topic echo /soccer/detections
ros2 topic echo /soccer/ball_goal_state
ros2 topic echo /soccer/reach_goal_fsm_state
ros2 topic echo /soccer/goal_scored
ros2 topic echo /cmd_vel
```

## Nœuds

| Nœud | Paquet | Rôle |
| --- | --- | --- |
| `yolo_detector` | `footbot_soccer_vision` | Détection YOLO `ball`+`goal` depuis `/camera/image_raw`. |
| `ball_goal_state_estimator` | `footbot_soccer_behavior` | Convertit `Detection2DArray` en `BallGoalState`. |
| `reach_goal_fsm` | `footbot_soccer_behavior` | Choisit les skills et publie `/cmd_vel`. |
| `reach_goal_score_monitor` | `footbot_soccer_behavior` | Arbitre de simulation qui arrête l'épisode après un but marqué. |

## Message d'état

`footbot_soccer_msgs/msg/BallGoalState` est uniquement dérivé de l'image :

```text
bool  ball_visible / goal_visible / stale
float ball_confidence / goal_confidence
float ball_center_error / goal_center_error   erreur horizontale normalisée
float ball_angle_rad / goal_angle_rad         relèvement (bearing) depuis l'axe optique
float ball_radius_px                          taille apparente de la balle (proxy de portée)
float goal_width_px                           taille apparente du but
bool  has_ball_control                        conservateur : proche + centrée
bool  ball_goal_aligned                       balle et but partagent un relèvement
bool  goal_memory_active                      le dernier relèvement du but est réutilisé
float goal_memory_age_sec                     âge du but mémorisé
```

`stale` signifie que le pipeline de détection a cessé de fournir des frames.
`ball_visible` et `goal_visible` signifient que chaque objet est apparu dans une
frame récente.

Le but peut disparaître de la caméra lorsque le robot s'approche de l'entrée
ouverte du but. L'estimateur conserve une courte mémoire temporelle du dernier
relèvement valide du but tant que la balle reste contrôlée, afin que la FSM puisse
terminer le dribble au lieu de revenir à `SEARCH_GOAL` à cause d'une seule perte
temporaire de YOLO. Si la perte survient après que le robot s'est déjà engagé dans
`DRIBBLE_TO_GOAL`, la FSM peut aussi entrer dans `COMMIT_TO_GOAL` : une poussée
courte, lente et centrée sur la balle qui ne nécessite pas une nouvelle détection
du but.

## États de la FSM

```text
SEARCH_BALL          aucune balle en vue, tourne pour balayer
APPROACH_BALL        balle visible, conduit vers elle (ralentit quand elle grandit)
CONTROL_BALL         balle dans la zone de contrôle frontale, la garde centrée
SEARCH_GOAL          balle contrôlée, but non vu, tourne en gardant la balle
ALIGN_BALL_TO_GOAL   balle+but visibles mais mal alignés, tourne doucement avec la balle
DRIBBLE_TO_GOAL      balle alignée avec le but, avance
COMMIT_TO_GOAL       fallback près du but, pousse lentement en centrant seulement la balle
RECOVER_BALL         contrôle perdu, recule et réacquiert la balle
STOP_SAFE            perception obsolète ou arrêt d'urgence, vitesse nulle
GOAL_SCORED          l'arbitre de simulation a détecté un but, vitesse nulle pour toujours
```

La FSM possède les transitions ; les skills ne produisent que des commandes `Twist`
bornées. Perdre `has_ball_control` depuis n'importe quel état de possession bascule
vers `RECOVER_BALL`. La perception obsolète force `STOP_SAFE`, et le comportement
reprend la recherche une fois que des détections fraîches reviennent. La FSM publie
un `Twist` nul à l'arrêt.

Lorsque `/soccer/goal_scored` devient true, la FSM passe à `GOAL_SCORED` et
continue de publier une vitesse nulle jusqu'à ce que le lancement/la session soit
redémarré.

`COMMIT_TO_GOAL` est un fallback sans réentraînement pour les pertes du but à
courte distance. Il ne s'active qu'après `DRIBBLE_TO_GOAL`, tant que la balle reste
visible et sous contrôle. Il utilise `ball_angle_rad` pour garder la balle centrée
et attend que l'arbitre de simulation signale `/soccer/goal_scored`. Il sort vers la
récupération si le contrôle de la balle est perdu ou si l'angle de la balle devient
trop grand, et il revient à `SEARCH_GOAL` si le délai (timeout) du commit expire.

## Valeurs par défaut partagées

Les valeurs par défaut de l'estimateur et de la FSM sont documentées dans :

```text
simulation/ros2_ws/src/footbot_soccer_behavior/config/reach_goal.yaml
```

L'estimateur utilise la largeur de la caméra (`640`) et le FOV horizontal (`1.047`
rad) pour transformer les centres des bounding boxes en relèvements, et le rayon
apparent de la balle comme proxy de portée approximatif. C'est adapté à la
simulation, pas un estimateur 3D calibré.

Valeurs par défaut du commit de Reach Goal :

```text
commit_to_goal_enabled: true
commit_to_goal_timeout_sec: 4.0
commit_to_goal_linear_velocity: 0.06
commit_to_goal_ball_angular_kp: 0.45
commit_to_goal_max_ball_angle_rad: 0.35
commit_to_goal_requires_ball_visible: true
```

## Propriété de `/cmd_vel`

En mode reach-goal, seul `reach_goal_fsm` publie `/cmd_vel`. N'exécutez pas un
autre propriétaire de `/cmd_vel` (pont HTTP, contrôle par gestes, suiveur de balle
ou la FSM de Contrôle de balle) en même temps, sinon les commandes se disputeront.

## Dépannage de la détection du but

Le comportement dépend du fait que le modèle YOLO détecte le `goal`. La balle est
généralement facile ; le but est plus difficile.

1. Baissez le seuil pour confirmer que le but est détectable du tout :

   ```bash
   ros2 launch footbot_bringup reach_goal.launch.py \
     model_path:=/absolute/path/to/reach_goal_ball_goal_v1_best.pt \
     confidence_threshold:=0.05 \
     show_debug_view:=true
   ```

2. Inspectez les détections et le débit :

   ```bash
   ros2 topic echo /soccer/detections
   ros2 topic hz /soccer/detections
   ```

3. Si le but n'apparaît toujours pas, améliorez le dataset/modèle (**ne** codez
   **pas** en dur la pose du but et n'utilisez pas le ground truth de Gazebo) :
   - Capturez des images caméra de la scène reach-goal avec `image_capture`.
   - Étiquetez plus d'exemples de `goal` dans Label Studio.
   - Relancez `prepare_reach_goal_dataset.py`, validez et réentraînez. Voir
     [perception-and-datasets.md](perception-and-datasets.md).

`COMMIT_TO_GOAL` n'aide qu'après que le robot a déjà vu le but et s'est aligné avec
lui. Si le modèle ne détecte jamais le but au début, baissez le seuil de confiance
pour déboguer ou améliorez le dataset.

Optionnellement, ajustez le visuel du but simulé dans
`footbot_gazebo/worlds/footbot_reach_goal.sdf` pour qu'il corresponde mieux aux
images d'entraînement, mais gardez-le visible pour la caméra du robot et distinct
de la balle.

## Détection du but marqué

Le score utilise la logique d'arbitre de simulation, pas la perception du robot.
Le lancement fait le pont du flux de poses du monde Gazebo depuis
`/world/footbot_world/pose/info`, et `reach_goal_score_monitor` extrait la pose de
`reach_goal_ball` de ce message. Il peut aussi consommer `/reach_goal/ball_pose` si
un pont direct de pose de modèle est disponible dans une future configuration
Gazebo. Le moniteur publie `/soccer/goal_scored` une fois que la balle reste à
l'intérieur de la zone de but assez longtemps :

```text
ball_x >= 1.68
abs(ball_y) <= 0.38
ball_z <= 0.20
hold time >= 0.15 s
```

Cela permet au comportement reach-goal de s'arrêter proprement après un but sans
donner au robot aucune information de ground-truth pour naviguer.

## Limites actuelles

Ce comportement conduit un robot pour pousser la balle vers un but et arrête
l'épisode lorsque l'arbitre de simulation détecte un but. Il ne vole pas la balle
aux adversaires, ne coordonne pas une équipe et n'utilise pas l'apprentissage par
renforcement.
