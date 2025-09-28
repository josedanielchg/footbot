## Project Structure

The project is organized into several main directories, each serving a specific purpose:

- `auto_soccer_bot/`: This folder contains all the code and resources related to the automatic mode of the robot. Inside, you'll find everything needed for the robot to function autonomously, from object detection logic to the commands that the laptop sends to the robot. For more detailed documentation, see [Automatic Mode](docs/automatic_mode.md).

- `ESP32CAM_robot/`: This directory holds the configuration and code for the ESP32 itself. Here, you will find the setup for motor control, the request handlers that allow it to receive HTTP requests, the camera controller logic, and the Wi-Fi connection setup. This is essentially the ESP32 acting as a web server and a camera streaming device. More details can be found in the [ESP32 Web Server Documentation](docs/esp32_web_server.md).

- `manual_control/`: This folder includes everything related to the manual control mode. It contains the Python scripts used on the laptop for hand gesture recognition and the logic to send those commands back to the ESP32. It also handles the communication layer for transmitting these instructions. More information is available in the [Manual Control Documentation](docs/manual_mode.md).

- `docs/`: This directory contains all the documentation files, including the architecture overview, mode explanations, and future improvements. Each section in this README links to a detailed document in this folder.