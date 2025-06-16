#include "MotorControl.h"
#include "config.h"
#include <Arduino.h>
#include "esp32-hal-ledc.h"

// LEDC PWM Configuration
#define PWM_FREQUENCY 5000 // PWM frequency in Hz
#define PWM_RESOLUTION 8   // 8-bit resolution (0-255 for duty cycle)
#define LEDC_CHANNEL_A 0
#define LEDC_CHANNEL_B 1

// --- Helper function for setting motor state ---
// state: 0=stop, 1=forward, -1=backward
// speed: 0-255
void setMotorStateAndSpeed(int motorDirPin1, int motorDirPin2, int directionState, int ENABLE_PIN, int speed) {
    // Set direction
    digitalWrite(motorDirPin1, directionState > 0 ? HIGH : LOW);
    digitalWrite(motorDirPin2, directionState < 0 ? HIGH : LOW);

    // Set speed using PWM
    if (directionState == 0) { // If stopping, set PWM to 0
        ledcWrite(ENABLE_PIN, 0);
    } else {
        ledcWrite(ENABLE_PIN, constrain(speed, 0, 255)); // constrain speed to 0-255
    }
}


void setupMotors() {
    Serial.println("Setting up motor GPIO pins and PWM...");

    #if defined(MOTOR_A_PIN1) && defined(MOTOR_A_PIN2) && \
        defined(MOTOR_B_PIN1) && defined(MOTOR_B_PIN2) && \
        defined(MOTOR_A_ENABLE_PIN) && defined(MOTOR_B_ENABLE_PIN)

        pinMode(MOTOR_A_PIN1, OUTPUT);
        pinMode(MOTOR_A_PIN2, OUTPUT);
        pinMode(MOTOR_B_PIN1, OUTPUT);
        pinMode(MOTOR_B_PIN2, OUTPUT);

        // Setup PWM channels for ENA and ENB
        // configure LEDC PWM
        ledcAttachChannel(MOTOR_A_ENABLE_PIN, PWM_FREQUENCY, PWM_RESOLUTION, LEDC_CHANNEL_A);

        ledcAttachChannel(MOTOR_B_ENABLE_PIN, PWM_FREQUENCY, PWM_RESOLUTION, LEDC_CHANNEL_B);

        stopMotors(); // Initialize motors stopped, speed 0
        Serial.println("Motor pins and PWM configured.");
    #else
        Serial.println("WARNING: Motor direction or enable pins not fully defined in config.h. Speed control might be disabled.");
        // Fallback for no enable pins (full speed only)
        #if defined(MOTOR_A_PIN1) && defined(MOTOR_A_PIN2) && defined(MOTOR_B_PIN1) && defined(MOTOR_B_PIN2)
            pinMode(MOTOR_A_PIN1, OUTPUT);
            pinMode(MOTOR_A_PIN2, OUTPUT);
            pinMode(MOTOR_B_PIN1, OUTPUT);
            pinMode(MOTOR_B_PIN2, OUTPUT);
            stopMotors();
            Serial.println("Motor direction pins configured (no speed control).");
        #else
             Serial.println("Motor control fully disabled.");
        #endif
    #endif
}


void moveForward(int speed) {
    Serial.printf("COMMAND: Move Forward, Speed: %d\n", speed);
    #if defined(MOTOR_A_PIN1) && defined(MOTOR_A_PIN2) && defined(MOTOR_B_PIN1) && defined(MOTOR_B_PIN2) && defined(MOTOR_A_ENABLE_PIN) && defined(MOTOR_B_ENABLE_PIN)
        // Set both motors to move forward at the specified speed
        // directionState: 1 for forward, -1 for backward, 0 for stop
        setMotorStateAndSpeed(MOTOR_A_PIN1, MOTOR_A_PIN2, 1, MOTOR_A_ENABLE_PIN, speed);
        setMotorStateAndSpeed(MOTOR_B_PIN1, MOTOR_B_PIN2, 1, MOTOR_B_ENABLE_PIN, speed);
    #elif defined(MOTOR_A_PIN1)
        digitalWrite(MOTOR_A_PIN1, HIGH); digitalWrite(MOTOR_A_PIN2, LOW);
        digitalWrite(MOTOR_B_PIN1, HIGH); digitalWrite(MOTOR_B_PIN2, LOW);
    #endif
}


void moveBackward(int speed) {
    Serial.printf("COMMAND: Move Backward, Speed: %d\n", speed);
    #if defined(MOTOR_A_PIN1) && defined(MOTOR_A_PIN2) && defined(MOTOR_B_PIN1) && defined(MOTOR_B_PIN2) && defined(MOTOR_A_ENABLE_PIN) && defined(MOTOR_B_ENABLE_PIN)
        setMotorStateAndSpeed(MOTOR_A_PIN1, MOTOR_A_PIN2, -1, MOTOR_A_ENABLE_PIN, speed);
        setMotorStateAndSpeed(MOTOR_B_PIN1, MOTOR_B_PIN2, -1, MOTOR_B_ENABLE_PIN, speed);
    #elif defined(MOTOR_A_PIN1)
        digitalWrite(MOTOR_A_PIN1, LOW); digitalWrite(MOTOR_A_PIN2, HIGH);
        digitalWrite(MOTOR_B_PIN1, LOW); digitalWrite(MOTOR_B_PIN2, HIGH);
    #endif
}

void turnLeft(int speed) {
    Serial.printf("COMMAND: Turn Left, Speed: %d\n", speed);
    #if defined(MOTOR_A_PIN1) && defined(MOTOR_A_PIN2) && defined(MOTOR_B_PIN1) && defined(MOTOR_B_PIN2) && defined(MOTOR_A_ENABLE_PIN) && defined(MOTOR_B_ENABLE_PIN)
        setMotorStateAndSpeed(MOTOR_A_PIN1, MOTOR_A_PIN2, -1, MOTOR_A_ENABLE_PIN, speed); // Motor A backward
        setMotorStateAndSpeed(MOTOR_B_PIN1, MOTOR_B_PIN2,  1, MOTOR_B_ENABLE_PIN, speed); // Motor B forward
    #elif defined(MOTOR_A_PIN1)
        digitalWrite(MOTOR_A_PIN1, HIGH); digitalWrite(MOTOR_A_PIN2, LOW);  // A backward
        digitalWrite(MOTOR_B_PIN1, LOW);  digitalWrite(MOTOR_B_PIN2, HIGH); // B forward
    #endif
}

void turnRight(int speed) {
    Serial.printf("COMMAND: Turn Right, Speed: %d\n", speed);
    #if defined(MOTOR_A_PIN1) && defined(MOTOR_A_PIN2) && defined(MOTOR_B_PIN1) && defined(MOTOR_B_PIN2) && defined(MOTOR_A_ENABLE_PIN) && defined(MOTOR_B_ENABLE_PIN)
        setMotorStateAndSpeed(MOTOR_A_PIN1, MOTOR_A_PIN2,  1, MOTOR_A_ENABLE_PIN, speed); // Motor A forward
        setMotorStateAndSpeed(MOTOR_B_PIN1, MOTOR_B_PIN2, -1, MOTOR_B_ENABLE_PIN, speed); // Motor B backward
    #elif defined(MOTOR_A_PIN1)
        digitalWrite(MOTOR_A_PIN1, LOW);  digitalWrite(MOTOR_A_PIN2, HIGH); // A forward
        digitalWrite(MOTOR_B_PIN1, HIGH); digitalWrite(MOTOR_B_PIN2, LOW);  // B backward
    #endif
}

void stopMotors() {
    Serial.println("COMMAND: Stop Motors");
    #if defined(MOTOR_A_PIN1) && defined(MOTOR_A_PIN2) && defined(MOTOR_B_PIN1) && defined(MOTOR_B_PIN2) && defined(MOTOR_A_ENABLE_PIN) && defined(MOTOR_B_ENABLE_PIN)
        setMotorStateAndSpeed(MOTOR_A_PIN1, MOTOR_A_PIN2, 0, MOTOR_A_ENABLE_PIN, 0); // Stop motor A
        setMotorStateAndSpeed(MOTOR_B_PIN1, MOTOR_B_PIN2, 0, MOTOR_B_ENABLE_PIN, 0); // Stop motor B
    #elif defined(MOTOR_A_PIN1) // Fallback for no enable pins
        digitalWrite(MOTOR_A_PIN1, LOW); digitalWrite(MOTOR_A_PIN2, LOW);
        digitalWrite(MOTOR_B_PIN1, LOW); digitalWrite(MOTOR_B_PIN2, LOW);
    #endif
}