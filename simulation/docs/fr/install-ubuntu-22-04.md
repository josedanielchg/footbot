# Installation sur Ubuntu 22.04

Ce guide installe le stack de simulation pour Ubuntu 22.04 (`jammy`) :

- ROS 2 Humble Hawksbill
- Gazebo Fortress via l'appariement ROS/Gazebo par défaut
- `ros-humble-ros-gz`
- Outils de développement ROS

## 1. Confirmer l'hôte

```bash
lsb_release -a
cat /etc/os-release
uname -m
```

Résultat attendu pour cette configuration :

- `Release: 22.04`
- `Codename: jammy`
- Architecture telle que `x86_64` ou `aarch64`

## 2. Configurer la locale et les dépôts

```bash
sudo apt update
sudo apt install -y software-properties-common curl locales
sudo add-apt-repository universe

sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

## 3. Ajouter la source apt de ROS 2

```bash
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
```

## 4. Mettre à jour le système avant d'installer ROS

```bash
sudo apt update
sudo apt upgrade
```

Sur Ubuntu 22.04, cette étape est importante avant d'installer `ros-humble-desktop`.

## 5. Installer ROS 2 Humble et l'intégration Gazebo

```bash
sudo apt install -y ros-humble-desktop ros-dev-tools ros-humble-ros-gz
```

`ros-humble-ros-gz` installe l'intégration Gazebo prise en charge par défaut pour ROS 2 Humble. Pour ce stack, cela signifie Gazebo Fortress.

## 6. Sourcer ROS 2

Pour le terminal actuel :

```bash
source /opt/ros/humble/setup.bash
```

Pour les futurs terminaux Bash :

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

## Notes

- N'installez pas ROS 2 Jazzy directement sur Ubuntu 22.04 pour ce workspace.
- N'installez pas d'appariements non par défaut comme Humble avec Harmonic, sauf si le projet migre intentionnellement les versions du stack.
- Préférez `ign gazebo` pour la vérification de Gazebo Fortress.
