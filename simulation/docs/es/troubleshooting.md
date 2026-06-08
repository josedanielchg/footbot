# Resolución de problemas

## No se encuentra el paquete del workspace

```bash
source /opt/ros/humble/setup.bash
cd simulation/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 pkg list | grep footbot
```

## El robot no se mueve

Comprueba la propiedad del topic:

```bash
ros2 topic info /cmd_vel
ros2 topic echo /cmd_vel
```

Ejecuta solo un modo de control a la vez.

## Falta el topic de cámara

```bash
ros2 topic list | grep camera
ign topic -l | grep camera
```

Si Gazebo tiene el topic pero ROS no, inspecciona los argumentos de
`ros_gz_bridge` en el archivo de lanzamiento activo.

## El control de pelota gira para siempre

Comprueba la cámara del robot y la detección de la pelota:

```bash
ros2 topic hz /camera/image_raw
ros2 topic echo /ball_detection
ros2 topic echo /soccer/ball_state
ros2 topic echo /soccer/fsm_state
```

Usa `show_debug_view:=true` para ver el overlay del detector.

## Errores de import de YOLO o de NumPy

Reinstala las dependencias opcionales fijadas:

```bash
python3 -m pip install --user --force-reinstall -r simulation/requirements-yolo.txt
```

Evita NumPy 2.x con esta configuración de ROS/OpenCV/MediaPipe de Ubuntu 22.04.

## La pelota rueda demasiado tiempo

Confirma que el plugin de arrastre de la pelota está instalado y que el mundo lo
carga:

```bash
cd simulation/ros2_ws
colcon build --symlink-install --packages-select footbot_gazebo footbot_bringup
source install/setup.bash
```

Luego relanza la simulación. Los procesos de Gazebo existentes deben reiniciarse
para cargar un plugin recompilado.
