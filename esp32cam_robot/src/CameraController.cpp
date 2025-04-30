#include "CameraController.h"
#include "config.h"
#include "camera_pins.h" // Include the original pins header
#include <Arduino.h>    // For Serial

bool initCamera() {
    // This structure comes directly from your original .ino setup()
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.frame_size = FRAMESIZE_UXGA; // Set higher resolution initially
    config.pixel_format = PIXFORMAT_JPEG; // Important for streaming
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.jpeg_quality = 12; // Lower quality for higher frame rate streaming initially
    config.fb_count = 1;      // Use 1 buffer initially

    // Adjust config based on PSRAM
    if (config.pixel_format == PIXFORMAT_JPEG) {
        if (psramFound()) {
            config.jpeg_quality = 10; // Can use slightly better quality
            config.fb_count = 2;      // Use 2 buffers for smoother streaming
            config.grab_mode = CAMERA_GRAB_LATEST;
            Serial.println("PSRAM found, optimizing camera config for streaming.");
        } else {
            // Limit frame size if no PSRAM
            config.frame_size = FRAMESIZE_SVGA;
            config.fb_location = CAMERA_FB_IN_DRAM;
            Serial.println("No PSRAM found, limiting frame size to SVGA.");
        }
    } else {
         // Config for non-JPEG formats (like face detection) - Keep original logic if needed
        config.frame_size = FRAMESIZE_240X240;
        #if CONFIG_IDF_TARGET_ESP32S3
          config.fb_count = 2;
        #endif
    }

    // Camera init
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed with error 0x%x\n", err);
        return false;
    }
    Serial.println("Camera initialized successfully.");

    // Get sensor instance
    sensor_t *s = esp_camera_sensor_get();
    if (s == NULL) {
        Serial.println("Failed to get camera sensor.");
        return false;
    }

     // Initial sensor settings (from original code)
    if (s->id.PID == OV3660_PID) { // Adjustments for specific sensors
      s->set_vflip(s, 1);        // flip it back
      s->set_brightness(s, 1);   // up the brightness just a bit
      s->set_saturation(s, -2);  // lower the saturation
    }
     // Set initial frame size for streaming (smaller is faster)
    if (config.pixel_format == PIXFORMAT_JPEG) {
       s->set_framesize(s, FRAMESIZE_QVGA); // Start with QVGA for faster streaming
       Serial.println("Setting initial frame size to QVGA for streaming.");
    }

    #if defined(CAMERA_MODEL_M5STACK_WIDE) || defined(CAMERA_MODEL_M5STACK_ESP32CAM)
        s->set_vflip(s, 1);
        s->set_hmirror(s, 1);
    #endif

    #if defined(CAMERA_MODEL_ESP32S3_EYE)
      s->set_vflip(s, 1);
    #endif

    return true;
}

sensor_t *getCameraSensor() {
    return esp_camera_sensor_get();
}