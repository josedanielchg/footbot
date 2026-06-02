# Stack Decision

## Host Detected

- Distribution: Ubuntu 22.04.4 LTS
- Codename: `jammy`
- Architecture: `x86_64`

Check commands:

```bash
lsb_release -a
cat /etc/os-release
uname -m
```

## Selected Stack

- ROS 2: Humble Hawksbill
- Gazebo: Fortress
- ROS/Gazebo integration: `ros-humble-ros-gz`

This is the official, low-risk stack for Ubuntu 22.04. It keeps the simulation environment on a supported ROS 2 setup instead of introducing version workarounds.

## Why Not Jazzy On This Host

ROS 2 Jazzy targets Ubuntu 24.04 (`noble`) for official Debian packages. Installing Jazzy directly on Ubuntu 22.04 would require a container, a host OS upgrade, or a source build. Those options add risk and extra maintenance for this workspace.

If the project later moves to Ubuntu 24.04, the recommended stack should be revisited as:

- ROS 2: Jazzy Jalisco
- Gazebo: Harmonic
- ROS/Gazebo integration: `ros-jazzy-ros-gz`

## Version Decision Table

| Ubuntu version | Codename | ROS 2 | Gazebo | Recommendation |
| --- | --- | --- | --- | --- |
| 22.04 | `jammy` | Humble | Fortress | Use for this workspace |
| 24.04 | `noble` | Jazzy | Harmonic | Use after host upgrade or in a 24.04 container |
| Other | varies | Do not guess | Do not guess | Check official ROS and Gazebo compatibility docs first |

## References

- ROS 2 Humble Ubuntu install: https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html
- ROS 2 Jazzy Ubuntu install: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html
- Gazebo ROS installation matrix: https://gazebosim.org/docs/harmonic/ros_installation/
- Gazebo Fortress docs: https://gazebosim.org/docs/fortress/install
