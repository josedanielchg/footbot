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
void stopMotors();

void arcLeft(int speed, float turn_ratio); // turn_ratio 0.0-1.0 (0 = forward, 1 = pivot)
void arcRight(int speed, float turn_ratio);

#endif // MOTORCONTROL_H