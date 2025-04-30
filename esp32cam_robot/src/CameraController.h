#ifndef CAMERACONTROLLER_H
#define CAMERACONTROLLER_H

#include "esp_camera.h"

// Initializes the camera sensor based on the selected model
// Returns true on success, false on failure
bool initCamera();

// Gets the current camera sensor pointer
sensor_t *getCameraSensor();

#endif // CAMERACONTROLLER_H