# Robot Football Project

## Description

This project is a robot football player controlled by an ESP32. The robot can operate in two modes: manual control and automatic mode. In manual control mode, the robot receives instructions via hand gestures detected by a webcam and sent to the ESP32. In automatic mode, the ESP32 camera streams video to a laptop that processes the images, performs object detection to locate the ball and the goal, and sends movement commands back to the robot. The robot can move forward, left, right, and backward based on these commands.

## Index

- [Project Architecture](docs/architecture.md): Explains how the ESP32 acts as a web server, handles requests, and streams video. Also details the role of the laptop as the decision-making unit.

- [Project Structure](docs/structure.md): General guide of the project folder structure

- [Chassis Design](docs/chassis_design.md): Describes the physical design and construction of the robot chassis.

- [Electronic Design](docs/electronic_design.md): Covers the electronic assembly, including motors, L298N shield, batteries, and integration with the ESP32.

- [Manual Mode](docs/manual_mode.md): Explains the Python libraries used for hand gesture recognition and how manual control is implemented.

- [Automatic Mode](docs/automatic_mode.md): Describes the libraries and methods for object detection and color detection.

- [Results](docs/results.md): Presents the results of the project, including performance metrics and observations.

- [Future Improvements](docs/future_improvements.md): Discusses possible improvements and enhancements for the robot.

