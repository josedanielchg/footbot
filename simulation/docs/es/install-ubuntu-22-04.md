# Instalación en Ubuntu 22.04

Esta guía instala el stack de simulación para Ubuntu 22.04 (`jammy`):

- ROS 2 Humble Hawksbill
- Gazebo Fortress mediante el emparejamiento ROS/Gazebo por defecto
- `ros-humble-ros-gz`
- Herramientas de desarrollo de ROS

## 1. Confirmar el host

```bash
lsb_release -a
cat /etc/os-release
uname -m
```

Resultado esperado para esta configuración:

- `Release: 22.04`
- `Codename: jammy`
- Arquitectura como `x86_64` o `aarch64`

## 2. Configurar el locale y los repositorios

```bash
sudo apt update
sudo apt install -y software-properties-common curl locales
sudo add-apt-repository universe

sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

## 3. Añadir la fuente apt de ROS 2

```bash
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
```

## 4. Actualizar el sistema antes de instalar ROS

```bash
sudo apt update
sudo apt upgrade
```

En Ubuntu 22.04, este paso es importante antes de instalar `ros-humble-desktop`.

## 5. Instalar ROS 2 Humble y la integración con Gazebo

```bash
sudo apt install -y ros-humble-desktop ros-dev-tools ros-humble-ros-gz
```

`ros-humble-ros-gz` instala la integración de Gazebo soportada por defecto para ROS 2 Humble. Para este stack, eso significa Gazebo Fortress.

## 6. Hacer source de ROS 2

Para la terminal actual:

```bash
source /opt/ros/humble/setup.bash
```

Para futuras terminales Bash:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

## Notas

- No instales ROS 2 Jazzy directamente en Ubuntu 22.04 para este workspace.
- No instales emparejamientos no predeterminados como Humble con Harmonic salvo que el proyecto migre intencionadamente las versiones del stack.
- Prefiere `ign gazebo` para verificar Gazebo Fortress.
