# Décision du stack

## Hôte détecté

- Distribution : Ubuntu 22.04.4 LTS
- Codename : `jammy`
- Architecture : `x86_64`

Commandes de vérification :

```bash
lsb_release -a
cat /etc/os-release
uname -m
```

## Stack sélectionné

- ROS 2 : Humble Hawksbill
- Gazebo : Fortress
- Intégration ROS/Gazebo : `ros-humble-ros-gz`

C'est le stack officiel et à faible risque pour Ubuntu 22.04. Il maintient
l'environnement de simulation sur une configuration ROS 2 prise en charge au lieu
d'introduire des contournements de version.

## Pourquoi pas Jazzy sur cet hôte

ROS 2 Jazzy vise Ubuntu 24.04 (`noble`) pour les paquets Debian officiels.
Installer Jazzy directement sur Ubuntu 22.04 nécessiterait un conteneur, une mise
à niveau du système d'exploitation de l'hôte, ou une compilation depuis les
sources. Ces options ajoutent du risque et de la maintenance supplémentaire pour
ce workspace.

Si le projet migre plus tard vers Ubuntu 24.04, le stack recommandé devrait être
réexaminé comme suit :

- ROS 2 : Jazzy Jalisco
- Gazebo : Harmonic
- Intégration ROS/Gazebo : `ros-jazzy-ros-gz`

## Tableau de décision des versions

| Version d'Ubuntu | Codename | ROS 2 | Gazebo | Recommandation |
| --- | --- | --- | --- | --- |
| 22.04 | `jammy` | Humble | Fortress | À utiliser pour ce workspace |
| 24.04 | `noble` | Jazzy | Harmonic | À utiliser après mise à niveau de l'hôte ou dans un conteneur 24.04 |
| Autre | varie | Ne pas deviner | Ne pas deviner | Vérifier d'abord la documentation officielle de compatibilité de ROS et Gazebo |

## Références

- Installation de ROS 2 Humble sur Ubuntu : https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html
- Installation de ROS 2 Jazzy sur Ubuntu : https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html
- Matrice d'installation de Gazebo pour ROS : https://gazebosim.org/docs/harmonic/ros_installation/
- Documentation de Gazebo Fortress : https://gazebosim.org/docs/fortress/install
