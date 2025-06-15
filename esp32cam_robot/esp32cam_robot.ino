// Main sketch file for ESP32-CAM Robot

// Include headers for different modules
#include "src/config.h"           // For configuration constants
#include "src/WifiManager.h"      // For connecting to WiFi
#include "src/CameraController.h" // For initializing the camera
#include "src/LedControl.h"       // For controlling the LED
#include "src/MotorControl.h"     // For controlling motors
#include "src/WebServerManager.h" // For starting the web server

void setup() {
  // Start Serial communication
  Serial.begin(115200);
  Serial.println("\n\n--- ESP32-CAM Robot Booting ---");

  // Initialize components
  setupLed();       // Setup the LED pin
  setupMotors();    // Setup motor control       pins (placeholder)

  // Initialize the camera
  if (!initCamera()) {
    Serial.println("FATAL: Camera Initialization Failed. Halting.");
    while(1) { delay(1000); } // Stop execution
  }

  // Connect to WiFi
  if (!connectWiFi()) {
     Serial.println("FATAL: WiFi Connection Failed. Halting.");
     while(1) { delay(1000); } // Stop execution
  }

  // Start the Web Server
  if (!startWebServer()) {
      Serial.println("FATAL: Failed to start Web Server. Halting.");
      while(1) { delay(1000); } // Stop execution
  }

  Serial.println("--- Setup Complete ---");
  Serial.print("Camera Stream: http://");
  Serial.print(WiFi.localIP());
  Serial.println(":");
  Serial.print(HTTP_STREAM_PORT); // Use defined port
  Serial.println("/stream");

  Serial.print("Control Interface: http://");
  Serial.print(WiFi.localIP());
  Serial.println(":");
  Serial.print(HTTP_CONTROL_PORT); // Use defined port
  Serial.println("/");
}

void loop() {
  // The web server runs in its own tasks.
  // Motor control logic triggered by handlers could go here if needed, but usually better handled directly within the handler or dedicated motor task.
  delay(10000); // Nothing actively needed in the main loop for this server model (for now)
}