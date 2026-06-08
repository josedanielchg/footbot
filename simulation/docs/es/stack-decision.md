# Decisión del stack

## Host detectado

- Distribución: Ubuntu 22.04.4 LTS
- Codename: `jammy`
- Arquitectura: `x86_64`

Comandos de comprobación:

```bash
lsb_release -a
cat /etc/os-release
uname -m
```

## Stack seleccionado

- ROS 2: Humble Hawksbill
- Gazebo: Fortress
- Integración ROS/Gazebo: `ros-humble-ros-gz`

Este es el stack oficial y de bajo riesgo para Ubuntu 22.04. Mantiene el entorno
de simulación sobre una configuración de ROS 2 soportada en lugar de introducir
soluciones alternativas de versión.

## Por qué no Jazzy en este host

ROS 2 Jazzy apunta a Ubuntu 24.04 (`noble`) para los paquetes Debian oficiales.
Instalar Jazzy directamente en Ubuntu 22.04 requeriría un contenedor, una
actualización del SO del host, o una compilación desde fuente. Esas opciones
añaden riesgo y mantenimiento extra para este workspace.

Si el proyecto migra más adelante a Ubuntu 24.04, el stack recomendado debería
revisarse como:

- ROS 2: Jazzy Jalisco
- Gazebo: Harmonic
- Integración ROS/Gazebo: `ros-jazzy-ros-gz`

## Tabla de decisión de versiones

| Versión de Ubuntu | Codename | ROS 2 | Gazebo | Recomendación |
| --- | --- | --- | --- | --- |
| 22.04 | `jammy` | Humble | Fortress | Usar para este workspace |
| 24.04 | `noble` | Jazzy | Harmonic | Usar tras actualizar el host o en un contenedor 24.04 |
| Otra | varía | No adivinar | No adivinar | Consultar primero la documentación oficial de compatibilidad de ROS y Gazebo |

## Referencias

- Instalación de ROS 2 Humble en Ubuntu: https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html
- Instalación de ROS 2 Jazzy en Ubuntu: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html
- Matriz de instalación de Gazebo para ROS: https://gazebosim.org/docs/harmonic/ros_installation/
- Documentación de Gazebo Fortress: https://gazebosim.org/docs/fortress/install
