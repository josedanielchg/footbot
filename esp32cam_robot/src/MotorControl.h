#ifndef MOTORCONTROL_H
#define MOTORCONTROL_H

#include <Arduino.h>

// Initialize motor pins
void setupMotors();

// --- Robot Movement Commands ---
void moveForward(int speed);
void moveBackward(int speed);
void turnLeft(int speed);
void turnRight(int speed);
void stopMotors();              // stopMotors typically doesn't take speed, it implies 0

// TODO: Speed control later:
// void setSpeed(int speed); // Speed 0-255
// void moveForward(int speed);

#endif // MOTORCONTROL_H