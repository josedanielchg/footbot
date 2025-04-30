#include "WifiManager.h"
#include "config.h" // Include config for SSID/Password
#include <Arduino.h>

bool connectWiFi() {
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    WiFi.setSleep(false); // Keep WiFi active

    Serial.print("WiFi connecting");
    unsigned long startTime = millis();
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        if (millis() - startTime > 20000) { // 20 second timeout
             Serial.println("\nWiFi Connection Failed!");
             return false;
        }
    }
    Serial.println("\nWiFi connected");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    return true;
}