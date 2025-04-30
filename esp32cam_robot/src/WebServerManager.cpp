#include "WebServerManager.h"
#include "WebRequestHandlers.h" // Include the handlers
#include "config.h"             // For ports
#include <Arduino.h>            // For Serial

// Server handles
static httpd_handle_t camera_httpd = NULL;
static httpd_handle_t stream_httpd = NULL;

bool startWebServer() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = HTTP_CONTROL_PORT; // Port 80 for control/capture
    config.ctrl_port = 32768;               // Default control port
    config.max_uri_handlers = 16;           // Increased handler limit
    config.stack_size = 8192;               // Increase stack size slightly

    // Initialize handlers (like the FPS filter)
    initializeWebRequestHandlers();

    // --- Define URI handlers ---
    httpd_uri_t index_uri = { "/", HTTP_GET, indexHandler, NULL };
    httpd_uri_t status_uri = { "/status", HTTP_GET, statusHandler, NULL };
    httpd_uri_t control_uri = { "/control", HTTP_GET, controlHandler, NULL };
    httpd_uri_t capture_uri = { "/capture", HTTP_GET, captureHandler, NULL };
    httpd_uri_t move_uri = { "/move", HTTP_GET, moveHandler, NULL }; // New move handler


    Serial.printf("Starting web server on port: '%d'\n", config.server_port);
    if (httpd_start(&camera_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(camera_httpd, &index_uri);
        httpd_register_uri_handler(camera_httpd, &status_uri);
        httpd_register_uri_handler(camera_httpd, &control_uri);
        httpd_register_uri_handler(camera_httpd, &capture_uri);
        httpd_register_uri_handler(camera_httpd, &move_uri); // Register move handler
        Serial.println("Control server started successfully.");
    } else {
        Serial.println("Error starting control server!");
        return false;
    }

    // --- Start Streaming Server on Port 81 ---
    config.server_port = HTTP_STREAM_PORT;
    config.ctrl_port = 32769; // Increment control port

    httpd_uri_t stream_uri = { "/stream", HTTP_GET, streamHandler, NULL };

    Serial.printf("Starting stream server on port: '%d'\n", config.server_port);
    if (httpd_start(&stream_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(stream_httpd, &stream_uri);
        Serial.println("Stream server started successfully.");
    } else {
        Serial.println("Error starting stream server!");
        httpd_stop(camera_httpd);
        camera_httpd = NULL;
        return false;
    }

    return true; // Both servers started
}

void stopWebServer() {
    if (camera_httpd) {
        httpd_stop(camera_httpd);
        camera_httpd = NULL;
        Serial.println("Control server stopped.");
    }
     if (stream_httpd) {
        httpd_stop(stream_httpd);
        stream_httpd = NULL;
        Serial.println("Stream server stopped.");
    }
}