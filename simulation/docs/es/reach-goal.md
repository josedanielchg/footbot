# Reach Goal con la pelota

Reach Goal es el comportamiento autónomo de producción para conducir la pelota
hacia una portería visible. Un FootBot usa su cámara montada en el robot, un
detector YOLO de `ball`+`goal`, un estimador de estado derivado de la imagen,
skills acotadas y una máquina de estados finitos para empujar la pelota hacia una
portería visible. Cada decisión de control está guiada por la percepción; el
comportamiento nunca lee las poses ground-truth de Gazebo.

## Lanzamiento

Primero compila y haz source:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Ejecuta el comportamiento de Reach-goal con el modelo entrenado:

```bash
ros2 launch footbot_bringup reach_goal.launch.py \
  model_path:=/media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws/src/footbot_soccer_vision/models/reach_goal_ball_goal/reach_goal_ball_goal_v1_best.pt \
  show_debug_view:=true \
  run_behavior:=true
```

El lanzamiento inicia el mundo de Gazebo de reach-goal, hace spawn del FootBot,
hace spawn de la pelota, ejecuta el detector YOLO, abre el visor de depuración
opcional, e inicia el estimador de estado pelota+portería de reach-goal, el
monitor de puntuación de simulación y la FSM de reach-goal. **No** inicia el
puente HTTP, el controlador de gestos, el seguidor de pelota simple ni la FSM de
Control de pelota.

Establece `run_behavior:=false` para inspeccionar solo la percepción (sin
movimiento del robot).

## Argumentos de lanzamiento

```text
model_path              ruta absoluta a los pesos entrenados de ball+goal
run_behavior            inicia el estimador + FSM (por defecto true)
run_score_monitor       inicia el árbitro de puntuación de simulación (por defecto true)
show_debug_view         abre la ventana de imagen de depuración de YOLO (por defecto true)
confidence_threshold    umbral de score de YOLO (por defecto 0.25; bájalo para depurar)
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
/camera/image_raw          cámara del robot (entrada)
/soccer/detections         Detection2DArray de ball+goal de YOLO
/soccer/detections/debug_image
/soccer/ball_goal_state    footbot_soccer_msgs/BallGoalState (derivado de la imagen)
/soccer/reach_goal_fsm_state   std_msgs/String estado actual de la FSM
/soccer/goal_scored        std_msgs/Bool señal de gol del árbitro de simulación
/world/footbot_world/pose/info
                          tf2_msgs/TFMessage flujo de poses del mundo de Gazebo
/reach_goal/ball_pose          geometry_msgs/Pose opcional, entrada directa de pose de la pelota
/cmd_vel                   geometry_msgs/Twist (solo la FSM)
```

Inspecciónalos mientras el comportamiento se ejecuta:

```bash
ros2 topic echo /soccer/detections
ros2 topic echo /soccer/ball_goal_state
ros2 topic echo /soccer/reach_goal_fsm_state
ros2 topic echo /soccer/goal_scored
ros2 topic echo /cmd_vel
```

## Nodos

| Nodo | Paquete | Propósito |
| --- | --- | --- |
| `yolo_detector` | `footbot_soccer_vision` | Detección YOLO de `ball`+`goal` desde `/camera/image_raw`. |
| `ball_goal_state_estimator` | `footbot_soccer_behavior` | Convierte `Detection2DArray` en `BallGoalState`. |
| `reach_goal_fsm` | `footbot_soccer_behavior` | Elige skills y publica `/cmd_vel`. |
| `reach_goal_score_monitor` | `footbot_soccer_behavior` | Árbitro de simulación que detiene el episodio tras un gol marcado. |

## Mensaje de estado

`footbot_soccer_msgs/msg/BallGoalState` es únicamente derivado de la imagen:

```text
bool  ball_visible / goal_visible / stale
float ball_confidence / goal_confidence
float ball_center_error / goal_center_error   error horizontal normalizado
float ball_angle_rad / goal_angle_rad         orientación (bearing) desde el eje óptico
float ball_radius_px                          tamaño aparente de la pelota (proxy de rango)
float goal_width_px                           tamaño aparente de la portería
bool  has_ball_control                        conservador: cerca + centrada
bool  ball_goal_aligned                       pelota y portería comparten orientación
bool  goal_memory_active                      se está reutilizando la última orientación de la portería
float goal_memory_age_sec                     antigüedad de la portería recordada
```

`stale` significa que el pipeline de detección dejó de entregar frames.
`ball_visible` y `goal_visible` significan que cada objeto apareció en un frame
reciente.

La portería puede desaparecer de la cámara cuando el robot se acerca a la boca
abierta de la portería. El estimador mantiene una memoria temporal corta de la
última orientación válida de la portería mientras la pelota permanece controlada,
para que la FSM pueda terminar el dribbling en lugar de volver a `SEARCH_GOAL` por
una única pérdida temporal de YOLO. Si la pérdida ocurre después de que el robot
ya se haya comprometido con `DRIBBLE_TO_GOAL`, la FSM también puede entrar en
`COMMIT_TO_GOAL`: un empuje corto, lento y centrado en la pelota que no requiere
una detección fresca de la portería.

## Estados de la FSM

```text
SEARCH_BALL          sin pelota a la vista, rota para escanear
APPROACH_BALL        pelota visible, conduce hacia ella (frena al crecer)
CONTROL_BALL         pelota en la zona de control frontal, la mantiene centrada
SEARCH_GOAL          pelota controlada, portería no vista, rota sosteniendo la pelota
ALIGN_BALL_TO_GOAL   pelota+portería visibles pero desalineadas, gira suave con la pelota
DRIBBLE_TO_GOAL      pelota alineada con la portería, avanza
COMMIT_TO_GOAL       fallback cerca de portería, empuja despacio solo centrando la pelota
RECOVER_BALL         control perdido, retrocede y readquiere la pelota
STOP_SAFE            percepción obsoleta o parada de emergencia, velocidad cero
GOAL_SCORED          el árbitro de simulación detectó gol, velocidad cero para siempre
```

La FSM es dueña de las transiciones; las skills solo producen comandos `Twist`
acotados. Perder `has_ball_control` desde cualquier estado de posesión cae a
`RECOVER_BALL`. La percepción obsoleta fuerza `STOP_SAFE`, y el comportamiento
reanuda la búsqueda una vez que vuelven detecciones frescas. La FSM publica un
`Twist` cero al apagarse.

Cuando `/soccer/goal_scored` se vuelve true, la FSM transiciona a `GOAL_SCORED` y
sigue publicando velocidad cero hasta que se reinicie el lanzamiento/la sesión.

`COMMIT_TO_GOAL` es un fallback sin reentrenamiento para pérdidas de portería a
corta distancia. Solo se activa después de `DRIBBLE_TO_GOAL`, mientras la pelota
permanece visible y bajo control. Usa `ball_angle_rad` para mantener la pelota
centrada y espera a que el árbitro de simulación reporte `/soccer/goal_scored`.
Sale a recuperación si se pierde el control de la pelota o si el ángulo de la
pelota crece demasiado, y cae a `SEARCH_GOAL` si expira el timeout del commit.

## Valores por defecto compartidos

Los valores por defecto del estimador y la FSM están documentados en:

```text
simulation/ros2_ws/src/footbot_soccer_behavior/config/reach_goal.yaml
```

El estimador usa el ancho de la cámara (`640`) y el FOV horizontal (`1.047` rad)
para convertir los centros de los bounding boxes en orientaciones, y el radio
aparente de la pelota como un proxy de rango aproximado. Esto es apropiado para
simulación, no un estimador 3D calibrado.

Valores por defecto del commit de Reach Goal:

```text
commit_to_goal_enabled: true
commit_to_goal_timeout_sec: 4.0
commit_to_goal_linear_velocity: 0.06
commit_to_goal_ball_angular_kp: 0.45
commit_to_goal_max_ball_angle_rad: 0.35
commit_to_goal_requires_ball_visible: true
```

## Propiedad de `/cmd_vel`

En modo reach-goal, solo `reach_goal_fsm` publica `/cmd_vel`. No ejecutes otro
propietario de `/cmd_vel` (puente HTTP, control por gestos, seguidor de pelota o
la FSM de Control de pelota) al mismo tiempo, o los comandos se pelearán.

## Resolución de problemas de detección de portería

El comportamiento depende de que el modelo YOLO detecte la `goal`. La pelota suele
ser fácil; la portería es más difícil.

1. Baja el umbral para confirmar que la portería es detectable siquiera:

   ```bash
   ros2 launch footbot_bringup reach_goal.launch.py \
     model_path:=/absolute/path/to/reach_goal_ball_goal_v1_best.pt \
     confidence_threshold:=0.05 \
     show_debug_view:=true
   ```

2. Inspecciona las detecciones y la tasa:

   ```bash
   ros2 topic echo /soccer/detections
   ros2 topic hz /soccer/detections
   ```

3. Si la portería sigue sin aparecer, mejora el dataset/modelo (**no** codifiques
   a mano la pose de la portería ni uses el ground truth de Gazebo):
   - Captura imágenes de cámara de la escena de reach-goal con `image_capture`.
   - Etiqueta más ejemplos de `goal` en Label Studio.
   - Vuelve a ejecutar `prepare_reach_goal_dataset.py`, valida y reentrena.
     Consulta [perception-and-datasets.md](perception-and-datasets.md).

`COMMIT_TO_GOAL` solo ayuda después de que el robot ya haya visto la portería y se
haya alineado con ella. Si el modelo nunca detecta la portería al inicio, baja el
umbral de confianza para depurar o mejora el dataset.

Opcionalmente, ajusta el visual de la portería simulada en
`footbot_gazebo/worlds/footbot_reach_goal.sdf` para que se parezca más a las
imágenes de entrenamiento, pero mantenla visible para la cámara del robot y
distinta de la pelota.

## Detección de gol

La puntuación usa lógica de árbitro de simulación, no percepción del robot. El
lanzamiento puentea el flujo de poses del mundo de Gazebo desde
`/world/footbot_world/pose/info`, y `reach_goal_score_monitor` extrae la pose de
`reach_goal_ball` de ese mensaje. También puede consumir `/reach_goal/ball_pose`
si en una futura configuración de Gazebo hay disponible un puente directo de pose
del modelo. El monitor publica `/soccer/goal_scored` una vez que la pelota
permanece dentro de la zona de gol el tiempo suficiente:

```text
ball_x >= 1.68
abs(ball_y) <= 0.38
ball_z <= 0.20
hold time >= 0.15 s
```

Esto permite que el comportamiento de reach-goal se detenga limpiamente tras un
gol sin dar al robot ninguna información de ground-truth para navegar.

## Límites actuales

Este comportamiento conduce un robot para empujar la pelota hacia una portería y
detiene el episodio cuando el árbitro de simulación detecta un gol. No roba a
oponentes, no coordina un equipo ni usa aprendizaje por refuerzo.
