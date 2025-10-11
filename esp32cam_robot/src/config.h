#ifndef CONFIG_H
#define CONFIG_H

#define CAMERA_MODEL_AI_THINKER

// WiFi Credentials
#define WIFI_SSID "General"
#define WIFI_PASSWORD "MaDu$2022"

// Web Server Ports
#define HTTP_CONTROL_PORT 80
#define HTTP_STREAM_PORT 81

// Pin Configuration (Using AI Thinker values from camera_pins.h)
#define LED_PIN 4

#define MOTOR_A_PIN1 13
#define MOTOR_A_PIN2 12
#define MOTOR_A_ENABLE_PIN 2

#define MOTOR_B_PIN1 14
#define MOTOR_B_PIN2 15
#define MOTOR_B_ENABLE_PIN 4

#endif // CONFIG_H