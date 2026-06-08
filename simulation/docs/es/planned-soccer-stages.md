# Etapas de fútbol planificadas

Esta hoja de ruta describe hacia dónde va el stack de fútbol simulado. La base
estable es intencionadamente determinista: los topics de percepción alimentan a
los estimadores de estado, los estimadores de estado alimentan a las máquinas de
estados finitos, y exactamente un controlador posee `/cmd_vel` en cada modo de
lanzamiento.

## Fundamentos implementados

### Control de pelota

Objetivo: demostrar que un FootBot puede encontrar, aproximarse, hacer contacto y
mantener la pelota naranja en una zona de control frontal.

Comportamiento actual:

- Usa el detector HSV de pelota de `footbot_perception`.
- Convierte `Detection2D` en `BallState`.
- Ejecuta una FSM determinista con estados de búsqueda, alineación, aproximación,
  contacto, control, rotación-con-pelota, recuperación y parada segura.
- Proporciona mundos de validación de un solo escenario y multi-carril.

Foco de validación:

- El robot no debería moverse sin un estado de pelota fresco.
- La pelota debería permanecer lo bastante cerca para un contacto controlado.
- Las pruebas multi-carril deberían aislar los topics para que varios escenarios
  puedan ejecutarse en una misma sesión de Gazebo.

### Reach Goal

Objetivo: empujar la pelota hacia una portería visible usando la percepción de la
cámara del robot.

Comportamiento actual:

- Usa un detector YOLO de `ball` + `goal`.
- Convierte `Detection2DArray` en `BallGoalState`.
- Mantiene una memoria temporal corta de la portería cuando esta desaparece cerca
  de la boca.
- Usa `COMMIT_TO_GOAL` para mantener un empuje lento y centrado en la pelota tras
  pérdidas de la portería a corta distancia, sin usar las poses de Gazebo para
  navegar.
- Usa `reach_goal_fsm` como único propietario de `/cmd_vel`.
- Usa `reach_goal_score_monitor` como lógica de árbitro de simulación para
  detenerse tras un gol.

Foco de validación:

- El modelo debería detectar tanto la pelota como la portería en la aproximación
  inicial.
- La memoria de la portería debería cubrir pérdidas breves de YOLO mientras la
  pelota permanece controlada.
- `COMMIT_TO_GOAL` debería llevar el empuje final cuando la portería desaparece
  cerca de la boca, y luego detenerse una vez que `/soccer/goal_scored` se active.
- `/soccer/goal_scored` debería detener el robot una vez que la pelota entre en la
  zona de gol.

## Siguiente: mejoras del dribbling dirigido a portería

Objetivo: hacer Reach Goal más fiable antes de añadir oponentes.

Ideas para la implementación:

- Añadir más imágenes cercanas a la portería al dataset, especialmente cuando los
  postes están parcialmente visibles o la boca de la portería llena el cuadro.
- Mejorar la readquisición de la portería tras una pérdida temporal combinando la
  memoria temporal con un comportamiento de escaneo suave que preserve el control
  de la pelota.
- Reemplazar el fallback de commit actual por una percepción a corta distancia más
  robusta una vez que el dataset incluya suficientes ejemplos cercanos a portería.
- Ajustar la velocidad de dribbling, la ganancia angular y la duración de
  recuperación para que el robot empuje la pelota en lugar de sobrepasarla.
- Añadir rutas de recuperación para fallos comunes: la pelota se escapa a
  izquierda/derecha, la pelota se atasca cerca de un poste, o el robot llega a la
  portería sin la pelota.
- Registrar métricas simples como tiempo hasta el primer control, tiempo hasta el
  gol, duración de la memoria de portería, número de pérdidas de control y pose
  final de la pelota.

Forma de lanzamiento esperada:

- Mantener un lanzamiento dedicado de Reach Goal.
- Mantener `/cmd_vel` en propiedad de `reach_goal_fsm`.
- Mantener la puntuación como lógica de árbitro de simulación, no como percepción
  del robot.

## Planificado: interacción con oponentes

Objetivo: detectar un oponente con la pelota y disputar la posesión sin
desestabilizar los comportamientos base.

Ideas para la implementación:

- Usar el paquete de visión de fútbol para detectar las clases `opponent`, `robot`
  o `teammate` desde la cámara del robot.
- Añadir una estimación de posesión derivada de la imagen: pelota cerca del
  oponente, pelota cerca de uno mismo, o pelota libre.
- Empezar con robots oponentes estáticos o guionizados antes de añadir oponentes
  activos.
- Añadir estados de FSM para observar, aproximarse-al-oponente, disputar-pelota,
  recuperar-pelota y parada-segura.
- Mantener el comportamiento de colisión y seguridad conservador; la primera
  versión debería disputar despacio y recuperarse limpiamente.

Foco de validación:

- El robot nunca debería usar las poses del oponente de Gazebo para tomar
  decisiones.
- La detección de oponentes no debería publicar comandos de movimiento
  directamente.
- Los modos de lanzamiento de oponentes deberían estar separados del Control de
  pelota y de Reach Goal.

## Planificado: juego en equipo

Objetivo: soportar tres robots por bando con roles claros y propiedad de comandos
aislada.

Ideas para la implementación:

- Definir roles como portero, defensor y atacante.
- Empezar con formaciones fijas alrededor de la pelota central y las porterías.
- Añadir namespaces por robot para los topics de cámara, detecciones, estado,
  estado de FSM y `/cmd_vel`.
- Compartir solo información de alto nivel al principio, como "pelota visible",
  "portería visible", "el robot tiene el control" u "objetivo de rol".
- Explorar un comportamiento de pase simple después de que cada robot pueda
  controlar y aproximarse a la pelota de forma independiente.

Foco de validación:

- Cada robot debería tener exactamente un propietario de comandos.
- Los namespaces deben evitar colisiones de topics de cámara, detección y
  `/cmd_vel`.
- El comportamiento de equipo debería seguir permitiendo que los modos de un solo
  robot se ejecuten sin cambios.

## Líneas de investigación

Objetivo: comparar métodos tácticos solo después de que las bases deterministas
sean medibles.

Enfoques candidatos:

- FSM heurísticas para primeras tácticas predecibles.
- Árboles de comportamiento (behavior trees) si las transiciones de FSM se vuelven
  difíciles de mantener.
- Planificación tipo MCTS o SPO para elecciones tácticas de horizonte corto.
- RL o MARL solo después de que la simulación tenga reset estable, puntuación,
  métricas y escenarios reproducibles.

Reglas para los experimentos:

- Mantener las políticas de investigación en modos de lanzamiento separados.
- No reemplazar las bases deterministas hasta que un método nuevo sea más fácil de
  depurar y medible mejor.
- Registrar métricas y casos de fallo antes de añadir código de política más
  complejo.
