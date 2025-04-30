#ifndef WEBREQUESTHANDLERS_H
#define WEBREQUESTHANDLERS_H

#include "esp_http_server.h"

void initializeWebRequestHandlers();

// Handlers for the web server endpoints

// Serves the main HTML page
esp_err_t indexHandler(httpd_req_t *req);

// Handles camera settings control requests (/control)
esp_err_t controlHandler(httpd_req_t *req);

// Provides camera status information (/status)
esp_err_t statusHandler(httpd_req_t *req);

// Handles single JPEG frame capture requests (/capture)
esp_err_t captureHandler(httpd_req_t *req);

// Handles the MJPEG video stream (/stream)
esp_err_t streamHandler(httpd_req_t *req);

// Handles movement commands (/move?direction=forward)
esp_err_t moveHandler(httpd_req_t *req);

// --- Other handlers from original app_httpd.cpp (optional, keep if needed) ---
esp_err_t xclkHandler(httpd_req_t *req);
esp_err_t regHandler(httpd_req_t *req);
esp_err_t gregHandler(httpd_req_t *req);
esp_err_t pllHandler(httpd_req_t *req);
esp_err_t winHandler(httpd_req_t *req); // Resolution handler

#endif // WEBREQUESTHANDLERS_H