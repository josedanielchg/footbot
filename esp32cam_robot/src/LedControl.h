#ifndef LEDCONTROL_H
#define LEDCONTROL_H

#include <Arduino.h>

// Sets up the LED pin and PWM if needed
void setupLed();

// Controls the LED state (on/off) and intensity (for PWM)
// intensity: 0 = off, >0 = on (value used for PWM duty cycle if applicable)
void controlLed(bool state, int intensity = 255);

// Sets the duty cycle for PWM control (used by web handler)
void setLedIntensity(int duty);

// Indicates if the LED should be on during streaming
void setLedStreamingState(bool isStreaming);


#endif // LEDCONTROL_H