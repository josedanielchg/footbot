#ifndef WEBSERVERMANAGER_H
#define WEBSERVERMANAGER_H

#include "esp_http_server.h"

// Starts both the control/capture server and the streaming server
bool startWebServer();

// Stops the web servers
void stopWebServer();

#endif // WEBSERVERMANAGER_H