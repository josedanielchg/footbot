#include "robot_control_handlers.h"
#include "../MotorControl.h"
#include "../vendor/ArduinoJson.h"
#include "esp_http_server.h"
#include <Arduino.h>
#include <stdlib.h>               
#include <string.h>
#include <ctype.h>

bool parseMoveCommandJson(const char* json_string, char* direction_out, int max_direction_len, int* speed_out, bool* speed_was_found_in_json) {
    if (json_string == nullptr || direction_out == nullptr || speed_out == nullptr || speed_was_found_in_json == nullptr) {
        Serial.println(F("Error: Null pointer passed to parseMoveCommandJson."));
        return false;
    }
    JsonDocument doc;
    
    // Deserialize the JSON document
    DeserializationError error = deserializeJson(doc, json_string);

    // Test if parsing succeeded.
    if (error) {
        Serial.print(F("deserializeJson() failed: "));
        Serial.println(error.c_str());
        return false;
    }

    // --- Extract "direction" (mandatory) ---
    if (doc.containsKey("direction") && doc["direction"].is<const char*>()) {
        const char* dir_val = doc["direction"];
        strncpy(direction_out, dir_val, max_direction_len - 1);
        direction_out[max_direction_len - 1] = '\0'; // Ensure null termination
    } else {
        Serial.println(F("JSON parsing error: 'direction' key missing or not a string."));
        return false;
    }

    // --- Extract "speed" (optional, with default) ---
    *speed_out = 255;
    *speed_was_found_in_json = false;

    if (doc.containsKey("speed")) {
        if (doc["speed"].is<int>()) {
            *speed_out = doc["speed"].as<int>();
            if (*speed_out < 0) *speed_out = 0;
            if (*speed_out > 255) *speed_out = 255;
            *speed_was_found_in_json = true;
        } else {
            Serial.println(F("JSON 'speed' key present but value is not an integer. Using default speed."));
        }
    } else {
        Serial.println(F("JSON 'speed' key not found. Using default speed."));
    }

    return true;
}


esp_err_t moveHandler(httpd_req_t *req) {
    char content[150]; // Buffer for the request body
    int ret, remaining = req->content_len;
    int received = 0;

    // 1. Read the request body
    if (remaining == 0) {
        Serial.println(F("Error: POST body is empty for /move."));
        httpd_resp_set_status(req, "400 Bad Request");
        httpd_resp_send(req, "Empty request body", HTTPD_RESP_USE_STRLEN);
        return ESP_FAIL;
    }

    if (remaining >= sizeof(content)) {
        Serial.printf("Error: POST body too large (%d bytes) for buffer (%d bytes).\n", remaining, (int)sizeof(content));
        httpd_resp_set_status(req, "413 Request Entity Too Large");
        httpd_resp_send(req, "Request body too large", HTTPD_RESP_USE_STRLEN);
        return ESP_FAIL;
    }

    while (received < req->content_len) {
        ret = httpd_req_recv(req, content + received, req->content_len - received);
        if (ret <= 0) {
            if (ret == HTTPD_SOCK_ERR_TIMEOUT) {
                Serial.println(F("Timeout receiving POST body chunk."));
                httpd_resp_send_408(req); // 408 Request Timeout
                return ESP_FAIL;
            }
            Serial.println(F("Failed to receive POST body chunk."));
            httpd_resp_send_500(req);
            return ESP_FAIL;
        }
        received += ret;
    }
    content[received] = '\0';
    Serial.printf("Received POST body for /move: [%s]\n", content);

    // 2. Parse JSON using ArduinoJson v7
    char direction[32] = {0};
    int speed = 150; // Default, will be updated by parser
    bool speed_was_present_in_json = false;

    if (!parseMoveCommandJson(content, direction, sizeof(direction), &speed, &speed_was_present_in_json)) {
        // parseMoveCommandJson already prints detailed errors
        httpd_resp_set_status(req, "400 Bad Request");
        httpd_resp_send(req, "Malformed JSON or missing 'direction' key", HTTPD_RESP_USE_STRLEN);
        return ESP_FAIL;
    }

    // 3. Act on parsed values
    Serial.printf("Parsed direction: [%s], Parsed speed: %d (Speed field %s)\n",
                  direction, speed, speed_was_present_in_json ? "found" : "not found/defaulted");

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
}