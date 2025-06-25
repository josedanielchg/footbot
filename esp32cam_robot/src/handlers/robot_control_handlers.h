#ifndef ROBOT_CONTROL_HANDLERS_H
#define ROBOT_CONTROL_HANDLERS_H

#include "esp_http_server.h"

// Robot control HTTP request handlers
esp_err_t moveHandler(httpd_req_t *req);

#endif