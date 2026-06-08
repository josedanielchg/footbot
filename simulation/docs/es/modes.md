# Modos de simulación

Compila y haz source antes de lanzar cualquier modo:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Modo manual base

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py
```

Inicia Gazebo, hace spawn del robot, puentea los topics `/cmd_vel`, `/odom` y de
cámara, e inicia el puente HTTP por defecto.

Ejemplo de comando HTTP:

```bash
curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"forward","speed":150}'
```

## Modo de gestos nativo de ROS

```bash
ros2 launch footbot_bringup sim_gesture_control.launch.py show_debug_view:=true
```

Usa la webcam del ordenador, la detección de manos de MediaPipe, los topics de
gestos y `gesture_to_cmd_vel`.

## Seguidor de pelota simple

```bash
ros2 launch footbot_bringup ball_following.launch.py show_debug_view:=true
```

Es un detector HSV simple más un seguidor de pelota proporcional. Es útil como
prueba de humo de percepción/control, pero no es el comportamiento de fútbol
principal.

## Control de pelota determinista

```bash
ros2 launch footbot_bringup ball_control.launch.py scenario:=front show_debug_view:=true
```

Es el comportamiento de fútbol autónomo fundamental para la posesión de la
pelota. Consulta [ball-control.md](ball-control.md).

## Prueba multi-carril de control de pelota

```bash
ros2 launch footbot_bringup ball_control_multi.launch.py show_debug_view:=true
```

Ejecuta escenarios aislados de pelota al frente, lejos y detrás en un mismo mundo
con topics en namespaces separados.

## Reach Goal con la pelota

```bash
ros2 launch footbot_bringup reach_goal.launch.py \
  model_path:=/media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws/src/footbot_soccer_vision/models/reach_goal_ball_goal/reach_goal_ball_goal_v1_best.pt \
  show_debug_view:=true \
  run_behavior:=true
```

Inicia un FootBot controlable, una pelota dinámica frente a él, una portería más
adelante, el puente de la cámara del robot en `/camera/image_raw`, el detector
YOLO de Reach Goal en `/soccer/detections`, el estimador de estado pelota+portería,
el monitor de puntuación de simulación en `/soccer/goal_scored`, y la FSM de
reach-goal que empuja la pelota hacia la portería.

En este modo, solo la FSM de Reach Goal posee `/cmd_vel`. Pasa
`run_behavior:=false` para inspeccionar únicamente la percepción. Pasa
`run_score_monitor:=false` solo cuando depures el árbitro por separado. Consulta
[reach-goal.md](reach-goal.md).

## Modos de fútbol solo de percepción

```bash
ros2 launch footbot_bringup opponent_detection.launch.py show_debug_view:=true
ros2 launch footbot_bringup soccer_detection.launch.py show_debug_view:=true
```

Estos modos observan imágenes de cámara y publican detecciones/imágenes de
depuración. No poseen `/cmd_vel`.

`soccer_detection.launch.py` usa el topic de cámara del campo de fútbol
`/soccer/camera/image_raw`. La escena de Reach-goal usa el topic de la cámara
montada en el robot `/camera/image_raw`.

## Visualización del campo de fútbol

```bash
ros2 launch footbot_bringup soccer_field.launch.py
```

Abre el campo con paredes, porterías, una pelota central y equipos estáticos en
espejo.
