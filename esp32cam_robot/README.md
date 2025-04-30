## Project structure

esp32cam_robot/
├── esp32cam_robot.ino          # Main sketch file (minimal)
├── partitions.csv           
├── ci.json                  
└── src/                        # Source files library
    ├── config.h                # WiFi Credentials, Pins, Ports
    ├── camera_pins.h           # Original pin definitions (keep for reference/inclusion)
    ├── camera_index.h          # Original HTML data
    ├── WifiManager.h           # Header for WiFi functions
    ├── WifiManager.cpp         # Implementation for WiFi functions
    ├── CameraController.h      # Header for Camera setup & control
    ├── CameraController.cpp    # Implementation for Camera setup & control
    ├── LedControl.h            # Header for LED control
    ├── LedControl.cpp          # Implementation for LED control
    ├── WebServerManager.h      # Header for Web Server setup & routing
    ├── WebServerManager.cpp    # Implementation for Web Server setup & routing
    ├── WebRequestHandlers.h    # Header for specific HTTP request handlers
    ├── WebRequestHandlers.cpp  # Implementation for HTTP request handlers
    └── MotorControl.h          # Header for Motor control (Placeholder)
    └── MotorControl.cpp        # Implementation for Motor control (Placeholder)