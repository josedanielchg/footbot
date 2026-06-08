# Arquitectura

La capa de simulación está aislada bajo `simulation/` y no debería requerir
cambios en `esp32cam_robot/` ni en `manual_control/`.

## Flujo de datos principal

```text
Mundo de Gazebo
  -> modelo del robot desde footbot_description
  -> topics de cámara y odometría de Gazebo Transport
  -> ros_gz_bridge
  -> topics de ROS
```

El movimiento usa:

```text
/cmd_vel -> ros_gz_bridge -> plugin DiffDrive de Gazebo -> robot simulado
```

La percepción de cámara usa:

```text
cámara de Gazebo -> /camera/image_raw -> nodo de percepción -> topics de detección/depuración
```

El control de pelota usa:

```text
/camera/image_raw
  -> footbot_perception ball_detector
  -> /ball_detection
  -> footbot_soccer_behavior ball_state_estimator
  -> /soccer/ball_state
  -> footbot_soccer_behavior ball_control_fsm
  -> /cmd_vel
```

Reach Goal usa:

```text
/camera/image_raw
  -> footbot_soccer_vision yolo_detector
  -> /soccer/detections
  -> footbot_soccer_behavior ball_goal_state_estimator
  -> /soccer/ball_goal_state
  -> footbot_soccer_behavior reach_goal_fsm
  -> /cmd_vel
```

El conteo de goles de Reach Goal es lógica de árbitro de simulación:

```text
/world/footbot_world/pose/info
  -> footbot_soccer_behavior reach_goal_score_monitor
  -> /soccer/goal_scored
  -> reach_goal_fsm estado GOAL_SCORED
```

El monitor de puntuación detiene el episodio después de que la pelota entra en la
zona de gol. El robot no lo usa para navegar.

## Propiedad del control

Solo un nodo o puente activo debería publicar comandos significativos en
`/cmd_vel` a la vez.

| Modo | Propietario de `/cmd_vel` |
| --- | --- |
| Simulación base/manual | comandos humanos por topic de ROS o puente HTTP |
| Control por gestos | `gesture_to_cmd_vel` |
| Seguidor de pelota simple | `ball_follower` |
| Control de pelota | `ball_control_fsm` |
| Reach Goal | `reach_goal_fsm` |
| Detección de oponente/portería | ninguno |
| Visualización del campo de fútbol | ninguno |

## Código compartido

`footbot_common` contiene las constantes compartidas de topics, frames,
dimensiones y pequeños helpers matemáticos. Debe permanecer ligero y reutilizable.
La lógica específica de comportamiento pertenece a `footbot_soccer_behavior`, no
al código común.

## Dirección de arquitectura planificada

Usar orquestación con FSM o FSM jerárquica para el comportamiento de alto nivel,
skills para primitivas de movimiento acotadas, control determinista donde sea
práctico, y módulos de política opcionales en el futuro para experimentos
tácticos.
