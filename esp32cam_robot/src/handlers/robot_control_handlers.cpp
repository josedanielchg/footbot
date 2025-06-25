#include "robot_control_handlers.h"
#include "../MotorControl.h"
#include "esp_http_server.h"
#include <Arduino.h>
#include <stdlib.h>               
#include <string.h>
#include <ctype.h> 

esp_err_t moveHandler(httpd_req_t *req) {
    char content[150]; // Buffer for the request body
    int ret, remaining = req->content_len;
    int received = 0;

    // 1. Read the request body
    if (remaining == 0) {
        Serial.println("Error: POST body is empty for /move.");
        httpd_resp_set_status(req, "400 Bad Request");
        httpd_resp_send(req, "Empty request body", HTTPD_RESP_USE_STRLEN);
        return ESP_FAIL;
    }

    if (remaining >= sizeof(content)) { // Check if content_len is too large for buffer
        Serial.printf("Error: POST body too large (%d bytes) for buffer (%d bytes).\n", remaining, sizeof(content));
        httpd_resp_set_status(req, "413 Request Entity Too Large");
        httpd_resp_send(req, "Request body too large", HTTPD_RESP_USE_STRLEN);
        return ESP_FAIL;
    }

    while (received < req->content_len) {
        ret = httpd_req_recv(req, content + received, req->content_len - received);
        if (ret <= 0) {
            if (ret == HTTPD_SOCK_ERR_TIMEOUT) {
                // If timeout, can retry or fail
                Serial.println("Timeout receiving POST body chunk.");
                // For simplicity, we'll fail on timeout during recv
                httpd_resp_send_500(req); // Or 408 Request Timeout
                return ESP_FAIL;
            }
            Serial.println("Failed to receive POST body chunk.");
            httpd_resp_send_500(req);
            return ESP_FAIL;
        }
        received += ret;
    }
    content[received] = '\0'; // Null-terminate the received content

    Serial.printf("Received POST body for /move: [%s]\n", content); // Print with brackets to see invisible chars

    // 2. Parse JSON-like string for "direction" and "speed"
    char direction[32] = {0};
    int speed = 150; // Default speed if not found or parse error
    bool direction_found = false;
    bool speed_found = false;

    // --- Parse "direction" ---
    char *key_ptr = strstr(content, "\"direction\"");
    if (key_ptr) {
        char *value_ptr = strchr(key_ptr, ':');
        if (value_ptr) {
            value_ptr++; // Move past ':'
            while (*value_ptr == ' ' || *value_ptr == '\t' || *value_ptr == '"') { // Skip whitespace and opening quote
                value_ptr++;
            }
            int i = 0;
            while (*value_ptr != '"' && *value_ptr != '\0' && i < sizeof(direction) - 1) {
                direction[i++] = *value_ptr++;
            }
            direction[i] = '\0'; // Null-terminate
            if (strlen(direction) > 0) {
                direction_found = true;
            }
        }
    }

    // --- Parse "speed" ---
    key_ptr = strstr(content, "\"speed\"");
    if (key_ptr) {
        char *value_ptr = strchr(key_ptr, ':');
        if (value_ptr) {
            value_ptr++; // Move past ':'
            while (*value_ptr == ' ' || *value_ptr == '\t') { // Skip whitespace
                value_ptr++;
            }
            if (isdigit((unsigned char)*value_ptr) || (*value_ptr == '-' && isdigit((unsigned char)*(value_ptr+1))) ) { // Check for digit or negative sign
                speed = atoi(value_ptr); // atoi stops at first non-digit
                // Constrain speed
                if (speed < 0) speed = 0;
                if (speed > 255) speed = 255; // Assuming 0-255 range for PWM
                speed_found = true;
            }
        }
    }

    // 3. Act on parsed values
    if (direction_found) {
        Serial.printf("Parsed direction: [%s], Parsed speed: %d (Speed field %s)\n",
                      direction, speed, speed_found ? "found" : "not found/defaulted");

        if (strcmp(direction, "forward") == 0) {
            moveForward(speed);
        } else if (strcmp(direction, "backward") == 0) {
            moveBackward(speed);
        } else if (strcmp(direction, "left") == 0) {
            turnLeft(speed);
        } else if (strcmp(direction, "right") == 0) {
            turnRight(speed);
        } else if (strcmp(direction, "stop") == 0) {
            stopMotors();
        } else {
            Serial.printf("Unknown move direction in POST: [%s]\n", direction);
            httpd_resp_set_status(req, "400 Bad Request");
            httpd_resp_send(req, "Unknown direction value", HTTPD_RESP_USE_STRLEN);
            return ESP_FAIL;
        }

        httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
        httpd_resp_send(req, "OK", HTTPD_RESP_USE_STRLEN);
        return ESP_OK;

    } else {
        Serial.println("Could not parse 'direction' key/value from POST body.");
        httpd_resp_set_status(req, "400 Bad Request");
        httpd_resp_send(req, "Malformed request: 'direction' key/value missing or invalid", HTTPD_RESP_USE_STRLEN);
        return ESP_FAIL;
    }
}