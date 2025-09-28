## Project Architecture

The core architecture of this robot football project revolves around an ESP32 acting as a web server. In essence, the ESP32 receives HTTP requests from a laptop on the same local Wi-Fi network. These requests contain simple instructions for the robot's movement or mode changes. 

For example, a typical request might look like this:

```

GET /move?direction=forward HTTP/1.1
Host: 192.168.1.100

```

In this setup, the laptop is essentially the "brain" of the operation. It handles all the image processing tasks, such as object detection to find the ball and the goal, and then sends corresponding commands to the ESP32. The ESP32 then interprets these commands and moves the robot accordingly.

Additionally, the ESP32 has an endpoint that provides a live video stream. This allows you to see in real time what the robot’s camera is capturing, making it easier to monitor the robot's environment and ensure it is correctly identifying objects. Essentially, the ESP32 camera acts as the robot's eyes, while the laptop processes the visual data and sends back simple movement instructions.
