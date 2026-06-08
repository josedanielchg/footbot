# Mundos y escenarios

Los mundos de Gazebo viven en:

```text
simulation/ros2_ws/src/footbot_gazebo/worlds/
```

<p align="center">
  <img src="src/soccer-field.png" alt="Captura del campo de fútbol de FootBot" />
</p>

**Figura 1.** Mundo del campo de fútbol con paredes de límite, dos porterías, una
pelota central y equipos de robots en espejo.

Mundos importantes:

| Mundo | Propósito |
| --- | --- |
| `footbot_empty.sdf` | Mundo mínimo. |
| `footbot_camera_test.sdf` | Objetos de colores para validación de la cámara. |
| `footbot_ball_follow.sdf` | Escena de prueba del seguidor de pelota simple. |
| `footbot_ball_control.sdf` | Un robot más escenarios de pelota dinámica. |
| `footbot_ball_control_multi.sdf` | Tres carriles aislados de control de pelota. |
| `footbot_reach_goal.sdf` | Un robot, una pelota dinámica y una portería para validar la visión y el comportamiento de Reach Goal. |
| `footbot_opponent_detection.sdf` | Marcadores de posición para detección de oponentes. |
| `footbot_soccer_field.sdf` | Campo completo con paredes, porterías, pelota central y disposición de equipo de tres robots en espejo. |

Validar mundos:

```bash
ign sdf -k simulation/ros2_ws/src/footbot_gazebo/worlds/footbot_ball_control.sdf
ign sdf -k simulation/ros2_ws/src/footbot_gazebo/worlds/footbot_soccer_field.sdf
```

## Pelota dinámica

El modelo de la pelota naranja vive en:

```text
simulation/ros2_ws/src/footbot_gazebo/models/orange_ball/
```

Usa fricción, rebote reducido, decaimiento de velocidad y el plugin personalizado
`footbot_ball_drag_system` para que la pelota no ruede eternamente tras el
contacto.

## Modelo del robot

El modelo del robot se genera a partir de:

```text
simulation/ros2_ws/src/footbot_description/urdf/footbot.urdf.xacro
```

Frames importantes:

```text
base_footprint
base_link
left_wheel_link
right_wheel_link
camera_link
camera_optical_frame
caster_link
```
