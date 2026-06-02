# Install On Ubuntu 22.04

This guide installs the simulation stack for Ubuntu 22.04 (`jammy`):

- ROS 2 Humble Hawksbill
- Gazebo Fortress through the default ROS/Gazebo pairing
- `ros-humble-ros-gz`
- ROS development tools

## 1. Confirm Host

```bash
lsb_release -a
cat /etc/os-release
uname -m
```

Expected result for this setup:

- `Release: 22.04`
- `Codename: jammy`
- Architecture such as `x86_64` or `aarch64`

## 2. Configure Locale And Repositories

```bash
sudo apt update
sudo apt install -y software-properties-common curl locales
sudo add-apt-repository universe

sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

## 3. Add ROS 2 Apt Source

```bash
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
```

## 4. Update System Before Installing ROS

```bash
sudo apt update
sudo apt upgrade
```

On Ubuntu 22.04, this step is important before installing `ros-humble-desktop`.

## 5. Install ROS 2 Humble And Gazebo Integration

```bash
sudo apt install -y ros-humble-desktop ros-dev-tools ros-humble-ros-gz
```

`ros-humble-ros-gz` installs the default supported Gazebo integration for ROS 2 Humble. For this stack, that means Gazebo Fortress.

## 6. Source ROS 2

For the current terminal:

```bash
source /opt/ros/humble/setup.bash
```

For future Bash terminals:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

## Notes

- Do not install ROS 2 Jazzy directly on Ubuntu 22.04 for this workspace.
- Do not install non-default pairings such as Humble with Harmonic unless the project intentionally migrates stack versions.
- Prefer `ign gazebo` for Gazebo Fortress verification.
