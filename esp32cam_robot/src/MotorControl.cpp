#include "MotorControl.h"
#include "config.h" // If motor pins are defined there
#include <Arduino.h>

// --- Helper function for setting motor state ---
// state: 0=stop, 1=forward, -1=backward
void setMotor(int motorAPin1, int motorAPin2, int stateA, 
            int motorBPin1, int motorBPin2, int stateB)
{
    // Motor A Control
    digitalWrite(motorAPin2, stateA > 0 ? HIGH : LOW);
    digitalWrite(motorAPin1, stateA < 0 ? HIGH : LOW);

    // Motor B Control
    digitalWrite(motorBPin1, stateB > 0 ? HIGH : LOW);
    digitalWrite(motorBPin2, stateB < 0 ? HIGH : LOW);

    // Optional: Add PWM control using analogWrite or ledcWrite on Enable pins if used
    // analogWrite(MOTOR_A_ENABLE_PIN, speed); // Example
}

void setupMotors() {
    Serial.println("Setting up motor GPIO pins...");
    #if defined(MOTOR_A_PIN1) && defined(MOTOR_A_PIN2) && defined(MOTOR_B_PIN1) && defined(MOTOR_B_PIN2)
        pinMode(MOTOR_A_PIN1, OUTPUT);
        pinMode(MOTOR_A_PIN2, OUTPUT);
        pinMode(MOTOR_B_PIN1, OUTPUT);
        pinMode(MOTOR_B_PIN2, OUTPUT);

        stopMotors(); // Initialize motors in stopped state
        Serial.println("Motor pins configured.");
    #else
        Serial.println("WARNING: Motor pins not fully defined in config.h. Motor control disabled.");
    #endif
}

void moveForward() {
    Serial.println("COMMAND: Move Forward");
    #if defined(MOTOR_A_PIN1) && defined(MOTOR_A_PIN2) && defined(MOTOR_B_PIN1) && defined(MOTOR_B_PIN2)
        setMotor(MOTOR_A_PIN1, MOTOR_A_PIN2, 1,  // Motor A Forward
                 MOTOR_B_PIN1, MOTOR_B_PIN2, 1); // Motor B Forward
    #endif
}

void moveBackward() {
    Serial.println("COMMAND: Move Backward");
     #if defined(MOTOR_A_PIN1) && defined(MOTOR_A_PIN2) && defined(MOTOR_B_PIN1) && defined(MOTOR_B_PIN2)
        setMotor(MOTOR_A_PIN1, MOTOR_A_PIN2, -1, // Motor A Backward
                 MOTOR_B_PIN1, MOTOR_B_PIN2, -1);// Motor B Backward
    #endif
}

void turnLeft() {
    Serial.println("COMMAND: Turn Left");
     #if defined(MOTOR_A_PIN1) && defined(MOTOR_A_PIN2) && defined(MOTOR_B_PIN1) && defined(MOTOR_B_PIN2)
        setMotor(MOTOR_A_PIN1, MOTOR_A_PIN2, -1, // Motor A Backward
                 MOTOR_B_PIN1, MOTOR_B_PIN2, 1); // Motor B Forward
    #endif
}

void turnRight() {
    Serial.println("COMMAND: Turn Right");
    #if defined(MOTOR_A_PIN1) && defined(MOTOR_A_PIN2) && defined(MOTOR_B_PIN1) && defined(MOTOR_B_PIN2)
        setMotor(MOTOR_A_PIN1, MOTOR_A_PIN2, 1,  // Motor A Forward
                 MOTOR_B_PIN1, MOTOR_B_PIN2, -1);// Motor B Backward
    #endif
}

void stopMotors() {
    Serial.println("COMMAND: Stop Motors");
    #if defined(MOTOR_A_PIN1) && defined(MOTOR_A_PIN2) && defined(MOTOR_B_PIN1) && defined(MOTOR_B_PIN2)
        setMotor(MOTOR_A_PIN1, MOTOR_A_PIN2, 0, // Motor A Stop
                 MOTOR_B_PIN1, MOTOR_B_PIN2, 0);// Motor B Stop
    #endif
}