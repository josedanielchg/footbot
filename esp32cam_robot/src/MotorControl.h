#ifndef MOTORCONTROL_H
#define MOTORCONTROL_H

#include <Arduino.h>

// Initialize motor pins
void setupMotors();

// --- Robot Movement Commands ---
void moveForward();
void moveBackward();
void turnLeft();
void turnRight();
void stopMotors();

// TODO: Speed control later:
// void setSpeed(int speed); // Speed 0-255
// void moveForward(int speed);

#endif // MOTORCONTROL_H