#ifndef CONFIG_H
#define CONFIG_H

#define CAMERA_MODEL_AI_THINKER

// WiFi Credentials
// #define WIFI_SSID "General"
// #define WIFI_PASSWORD "MaDu$2022"
#define WIFI_SSID "General"
#define WIFI_PASSWORD "MaDu$2022"

// #define WIFI_SSID "wifimkhAP"
// #define WIFI_PASSWORD "2832460X"

// Web Server Ports
#define HTTP_CONTROL_PORT 80
#define HTTP_STREAM_PORT 81

// Pin Configuration (Using AI Thinker values from camera_pins.h)
#define LED_PIN 4 // Pin 4 is the flash LED on AI Thinker

// TODO: Motors pins here later, e.g.
#define MOTOR_A_PIN1 13
#define MOTOR_A_PIN2 12
#define MOTOR_A_ENABLE_PIN 2 // Optional, for speed control

#define MOTOR_B_PIN1 14
#define MOTOR_B_PIN2 15
#define MOTOR_B_ENABLE_PIN 4 // Optional, for speed control

#endif // CONFIG_H