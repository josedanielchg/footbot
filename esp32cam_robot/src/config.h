#ifndef CONFIG_H
#define CONFIG_H

#define CAMERA_MODEL_AI_THINKER

// WiFi Credentials
#define WIFI_SSID "Daniel WiFi"
#define WIFI_PASSWORD "28324600"

// Web Server Ports
#define HTTP_CONTROL_PORT 80
#define HTTP_STREAM_PORT 81

// Pin Configuration (Using AI Thinker values from camera_pins.h)
#define LED_PIN 4 // Pin 4 is the flash LED on AI Thinker

// TODO: Motors pins here later, e.g.
// #define MOTOR_A_PIN1 12
// #define MOTOR_A_PIN2 13
// #define MOTOR_B_PIN1 14
// #define MOTOR_B_PIN2 15

#endif // CONFIG_H