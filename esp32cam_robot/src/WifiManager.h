#ifndef WIFIMANAGER_H
#define WIFIMANAGER_H

#include <WiFi.h>

// Connects to WiFi using credentials from config.h
// Returns true on success, false on failure (after timeout)
bool connectWiFi();

#endif // WIFIMANAGER_H