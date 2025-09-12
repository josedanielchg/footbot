// Main sketch file for ESP32-CAM Robot

// Include headers for different modules
#include "src/config.h"           // For configuration constants
#include "src/WifiManager.h"      // For connecting to WiFi
#include "src/CameraController.h" // For initializing the camera
#include "src/LedControl.h"       // For controlling the LED
#include "src/MotorControl.h"     // For controlling motors
#include "src/WebServerManager.h" // For starting the web server

void measure_fps(int samples = 50) {
  uint64_t min_us = UINT64_MAX, max_us = 0, sum_us = 0;
  uint64_t sum_cycles = 0;

  for (int i = 0; i < samples; i++) {
    uint32_t c0 = ESP.getCycleCount();          // ciclos CPU antes de capturar
    int64_t  t0 = esp_timer_get_time();         // µs antes de capturar

    camera_fb_t* fb = esp_camera_fb_get();      // CAPTURA
    int64_t  t1 = esp_timer_get_time();         // µs después de capturar
    uint32_t c1 = ESP.getCycleCount();          // ciclos CPU después

    if (fb) esp_camera_fb_return(fb);           // ¡no olvides liberar el frame!

    uint64_t dt_us     = (uint64_t)(t1 - t0);
    uint64_t dt_cycles = (uint64_t)(c1 - c0);

    sum_us     += dt_us;
    sum_cycles += dt_cycles;
    if (dt_us < min_us) min_us = dt_us;
    if (dt_us > max_us) max_us = dt_us;

    delay(1); // evita saturar
  }

  double avg_us     = (double)sum_us / samples;
  double fps        = 1e6 / avg_us;
  double avg_cycles = (double)sum_cycles / samples;
  double cpu_mhz    = getCpuFrequencyMhz();     // MHz CPU (p.ej. 240)
  double xclk_cycles_avg = 20.0 * avg_us;       // 20 MHz * tiempo_frame(µs)

  Serial.printf("\n--- Camera capture benchmark (%d muestras) ---\n", samples);
  Serial.printf("dt: avg=%.2f ms  min=%.2f ms  max=%.2f ms\n",
                avg_us/1000.0, min_us/1000.0, max_us/1000.0);
  Serial.printf("FPS ≈ %.2f\n", fps);
  Serial.printf("CPU cycles/frame ≈ %.0f  (CPU ~ %.0f MHz)\n",
                avg_cycles, cpu_mhz);
  Serial.printf("XCLK cycles/frame (20 MHz) ≈ %.0f\n", xclk_cycles_avg);
}

void setup() {
  // Start Serial communication
  Serial.begin(115200);
  Serial.println("\n\n--- ESP32-CAM Robot Booting ---");

  // Initialize components
  setupLed();       // Setup the LED pin
  setupMotors();    // Setup motor control       pins (placeholder)

  // Initialize the camera
  if (!initCamera()) {
    Serial.println("FATAL: Camera Initialization Failed. Halting.");
    while(1) { delay(1000); } // Stop execution
  }

  measure_fps(60);

  // Connect to WiFi
  if (!connectWiFi()) {
     Serial.println("FATAL: WiFi Connection Failed. Halting.");
     while(1) { delay(1000); } // Stop execution
  }

  // Start the Web Server
  if (!startWebServer()) {
      Serial.println("FATAL: Failed to start Web Server. Halting.");
      while(1) { delay(1000); } // Stop execution
  }

  Serial.println("--- Setup Complete ---");
  Serial.print("Camera Stream: http://");
  Serial.print(WiFi.localIP());
  Serial.println(":");
  Serial.print(HTTP_STREAM_PORT); // Use defined port
  Serial.println("/stream");

  Serial.print("Control Interface: http://");
  Serial.print(WiFi.localIP());
  Serial.println(":");
  Serial.print(HTTP_CONTROL_PORT); // Use defined port
  Serial.println("/");
}

void loop() {
  // The web server runs in its own tasks.
  // Motor control logic triggered by handlers could go here if needed, but usually better handled directly within the handler or dedicated motor task.
  delay(10000); // Nothing actively needed in the main loop for this server model (for now)
}