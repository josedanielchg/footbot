#include "LedControl.h"
#include "config.h"             // For LED_PIN
#include <Arduino.h>
#include "esp32-hal-ledc.h"     // For ledc functions

#define LED_LEDC_CHANNEL 2
#define LED_LEDC_FREQ 5000
#define LED_LEDC_RESOLUTION 8   // 8-bit resolution (0-255)

// State variables
static int currentLedDuty = 0;
static bool ledIsStreaming = false;
static bool ledInitialized = false;

void setupLed() {
#if defined(LED_PIN) && LED_PIN >= 0
    // Configure LEDC peripheral
    // ledcSetup(LED_LEDC_CHANNEL, LED_LEDC_FREQ, LED_LEDC_RESOLUTION);

    // Attach the channel to the GPIO pin
    ledcAttach(LED_PIN, LED_LEDC_FREQ, LED_LEDC_RESOLUTION); 

    Serial.printf("LED Flash configured on Pin %d using LEDC channel %d\n", LED_PIN, LED_LEDC_CHANNEL);
    ledInitialized = true;
    controlLed(false); // Start with LED off
#else
    Serial.println("LED Flash pin not defined or invalid. Skipping LED setup.");
    ledInitialized = false;
#endif
}

void controlLed(bool state, int intensity) {
    if (!ledInitialized) return;

    int duty = state ? intensity : 0;
    if (state && ledIsStreaming && (intensity > 255)) {
      duty = 255;
    }
    ledcWrite(LED_LEDC_CHANNEL, duty);
    // Serial.printf("LED (Pin %d) state: %s, intensity/duty: %d\n", LED_PIN, state ? "ON" : "OFF", duty);
}

void setLedIntensity(int duty) {
    if (!ledInitialized) return;
    currentLedDuty = constrain(duty, 0, 255); // Ensure duty is within 0-255
    Serial.printf("LED Intensity set to: %d\n", currentLedDuty);
    // Re-apply the intensity if the LED is supposed to be on (e.g., during streaming)
    if (ledIsStreaming) {
        controlLed(true, currentLedDuty);
    }
}

void setLedStreamingState(bool isStreaming) {
    if (!ledInitialized) return;
    ledIsStreaming = isStreaming;
    // Turn LED on/off based on streaming state and current intensity setting
    controlLed(ledIsStreaming, currentLedDuty);
}

// Function to get current intensity (might be needed by handlers)
int getLedIntensity() {
    return currentLedDuty;
}