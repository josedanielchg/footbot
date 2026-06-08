# Guía de desarrollo

## Límites

- Mantén el trabajo de implementación dentro de `simulation/` salvo que una tarea diga explícitamente lo contrario.
- No modifiques `esp32cam_robot/` ni `manual_control/` para refactors de simulación.
- Mantén separados los modos de simulación estables de los experimentos.
- No hagas commit de la salida de build generada, datasets, virtualenvs, pesos de modelos ni cachés.

## Pautas por paquete

- Pon las constantes compartidas y los helpers pequeños en `footbot_common`.
- Pon los cambios del modelo del robot en `footbot_description`.
- Pon los mundos, modelos y plugins de Gazebo en `footbot_gazebo`.
- Pon la orquestación de lanzamiento en `footbot_bringup`.
- Pon la percepción genérica en `footbot_perception`.
- Pon las herramientas de YOLO y datasets específicas de fútbol en `footbot_soccer_vision`.
- Pon la FSM de comportamiento de fútbol, la estimación de estado y las skills en `footbot_soccer_behavior`.

## Checklist de validación

```bash
git status -sb
source /opt/ros/humble/setup.bash
cd simulation/ros2_ws
colcon build --symlink-install
source install/setup.bash
colcon list --base-paths src
ros2 pkg list | grep footbot
```

Compila Python:

```bash
python3 -m py_compile src/footbot_soccer_behavior/footbot_soccer_behavior/**/*.py
```

Comprueba los argumentos de lanzamiento:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py --show-args
ros2 launch footbot_bringup ball_control.launch.py --show-args
ros2 launch footbot_bringup reach_goal.launch.py --show-args
```

Comprueba SDF/URDF:

```bash
ros2 run xacro xacro src/footbot_description/urdf/footbot.urdf.xacro > /tmp/footbot.urdf
check_urdf /tmp/footbot.urdf
ign sdf -k src/footbot_gazebo/worlds/footbot_soccer_field.sdf
ign sdf -k src/footbot_gazebo/worlds/footbot_reach_goal.sdf
```

## Reglas de documentación

Por ahora, mantén la documentación canónica en inglés en `simulation/docs/en/`.
Separa el comportamiento implementado del comportamiento planificado. Prefiere
documentos cortos enfocados en un tema antes que un único archivo de referencia
gigante.
