// src/handlers/camera_handlers.h
#ifndef CAMERA_HANDLERS_H
#define CAMERA_HANDLERS_H

#include "esp_http_server.h"

esp_err_t indexHandler(httpd_req_t *req);
esp_err_t statusHandler(httpd_req_t *req);
esp_err_t controlHandler(httpd_req_t *req); // Camera settings
esp_err_t captureHandler(httpd_req_t *req);
esp_err_t streamHandler(httpd_req_t *req);

#endif