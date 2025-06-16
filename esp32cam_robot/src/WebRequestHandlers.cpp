#include "WebRequestHandlers.h"
#include "CameraController.h"   // To get sensor object, etc.
#include "LedControl.h"         // To control LED
#include "MotorControl.h"       // To control motors
#include "camera_index.h"       // HTML data
#include "img_converters.h"     // Frame conversion
#include "fb_gfx.h"             // Frame buffer graphics
#include "esp_timer.h"          // Timestamps
#include "sdkconfig.h"
#include <Arduino.h>            // For Serial, String, etc.
#include <stdlib.h>             // For atoi
#include <string.h>             // For strcmp, strlen
#include "esp_http_server.h"
#include <ctype.h> 

typedef struct {
    httpd_req_t *req;
    size_t len;
} jpg_chunking_t;

#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\nX-Timestamp: %d.%06d\r\n\r\n";

typedef struct {
    size_t size;   //number of values used for filtering
    size_t index;  //current value index
    size_t count;  //value count
    int sum;
    int *values;  //array to be filled with values
} ra_filter_t;

static ra_filter_t ra_filter; // Simple moving average filter for frame rate

static ra_filter_t *ra_filter_init(ra_filter_t *filter, size_t sample_size){
    // --- Implementation from app_httpd.cpp ---
    memset(filter, 0, sizeof(ra_filter_t));
    filter->values = (int *)malloc(sample_size * sizeof(int));
    if(!filter->values){
        return NULL;
    }
    memset(filter->values, 0, sample_size * sizeof(int));
    filter->size = sample_size;
    return filter;
}

static int ra_filter_run(ra_filter_t *filter, int value){
    // --- Implementation from app_httpd.cpp ---
     if(!filter->values){
        return value;
    }
    filter->sum -= filter->values[filter->index];
    filter->values[filter->index] = value;
    filter->sum += filter->values[filter->index];
    filter->index++;
    filter->index = filter->index % filter->size;
    if (filter->count < filter->size) {
        filter->count++;
    }
    return filter->sum / filter->count;
}

static size_t jpg_encode_stream(void * arg, size_t index, const void* data, size_t len){
    // --- Implementation from app_httpd.cpp ---
    jpg_chunking_t *j = (jpg_chunking_t *)arg;
    if(!index){
        j->len = 0;
    }
    if(httpd_resp_send_chunk(j->req, (const char *)data, len) != ESP_OK){
        return 0;
    }
    j->len += len;
    return len;
}

static esp_err_t parse_get(httpd_req_t *req, char **obuf) {
    // --- Implementation from app_httpd.cpp ---
    char *buf = NULL;
    size_t buf_len = httpd_req_get_url_query_len(req) + 1;
    if (buf_len > 1) {
        buf = (char *)malloc(buf_len);
        if (!buf) {
            httpd_resp_send_500(req);
            return ESP_FAIL;
        }
        if (httpd_req_get_url_query_str(req, buf, buf_len) == ESP_OK) {
            *obuf = buf;
            return ESP_OK;
        }
        free(buf);
    }
    httpd_resp_send_404(req);
    return ESP_FAIL;
}


// --- Handler Implementations ---

esp_err_t indexHandler(httpd_req_t *req){
    // --- Copy implementation from app_httpd.cpp's index_handler ---
    // Make sure to use the correct camera_index_... variable based on sensor ID
    httpd_resp_set_type(req, "text/html");
    httpd_resp_set_hdr(req, "Content-Encoding", "gzip");
    sensor_t * s = getCameraSensor();
    if (s != NULL) {
        if (s->id.PID == OV3660_PID) {
            return httpd_resp_send(req, (const char *)index_ov3660_html_gz, index_ov3660_html_gz_len);
        } else if (s->id.PID == OV5640_PID) {
            return httpd_resp_send(req, (const char *)index_ov5640_html_gz, index_ov5640_html_gz_len);
        } else { // Default to OV2640
            return httpd_resp_send(req, (const char *)index_ov2640_html_gz, index_ov2640_html_gz_len);
        }
    } else {
        Serial.println("Camera sensor not found for index handler");
        return httpd_resp_send_500(req);
    }
}

esp_err_t controlHandler(httpd_req_t *req){
    // --- Copy implementation from app_httpd.cpp's cmd_handler ---
    // **IMPORTANT CHANGES:**
    // 1. Replace `esp_camera_sensor_get()` with `getCameraSensor()`.
    // 2. Replace LED control logic:
    //    Instead of:
    //       else if (!strcmp(variable, "led_intensity")) {
    //           led_duty = val;
    //           if (isStreaming) {
    //               enable_led(true);
    //           }
    //       }
    //    Use:
    //       else if (!strcmp(variable, "led_intensity")) {
    //           setLedIntensity(val); // Use the function from LedControl
    //           res = 0; // Indicate success
    //       }
    //    Make sure to set `res = 0;` for the LED case so it doesn't fall through to unknown command.
    // ---

    char *buf = NULL;
    char variable[32];
    char value[32];
    esp_err_t ret = parse_get(req, &buf);
    if (ret != ESP_OK) { return ret; }

    if (httpd_query_key_value(buf, "var", variable, sizeof(variable)) != ESP_OK ||
        httpd_query_key_value(buf, "val", value, sizeof(value)) != ESP_OK) {
        free(buf);
        httpd_resp_send_404(req);
        return ESP_FAIL;
    }
    free(buf);

    int val = atoi(value);
    Serial.printf("Control: var=%s, val=%d\n", variable, val);
    sensor_t *s = getCameraSensor();
    int res = -1; // Default to unknown command

    if (!s) {
        return httpd_resp_send_500(req);
    }

    // --- Copy all the strcmp conditions for camera controls from app_httpd.cpp here ---
    if (!strcmp(variable, "framesize")) { if (s->pixformat == PIXFORMAT_JPEG) res = s->set_framesize(s, (framesize_t)val); }
    else if (!strcmp(variable, "quality")) res = s->set_quality(s, val);
    else if (!strcmp(variable, "contrast")) res = s->set_contrast(s, val);
    else if (!strcmp(variable, "brightness")) res = s->set_brightness(s, val);
    else if (!strcmp(variable, "saturation")) res = s->set_saturation(s, val);
    // ... (copy all other camera settings) ...
    else if (!strcmp(variable, "ae_level")) res = s->set_ae_level(s, val);
    // --- **MODIFIED LED Handling** ---
    #if defined(LED_PIN) && LED_PIN >= 0
    else if (!strcmp(variable, "led_intensity")) {
        setLedIntensity(val);
        res = 0; // Command was handled successfully
    }
    #endif
    // --- End of copied settings ---
    else {
        Serial.printf("Unknown control variable: %s\n", variable);
    }

    if (res < 0) {
         Serial.printf("Control command failed or unknown: var=%s, val=%d, res=%d\n", variable, val, res);
         return httpd_resp_send_500(req); // Send 500 if command failed or unknown
    }

    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    return httpd_resp_send(req, NULL, 0);
}


esp_err_t statusHandler(httpd_req_t *req){
    // --- Copy implementation from app_httpd.cpp's status_handler ---
    // **IMPORTANT CHANGES:**
    // 1. Replace `esp_camera_sensor_get()` with `getCameraSensor()`.
    // 2. Replace LED intensity reporting:
    //    Instead of:
    //      #if CONFIG_LED_ILLUMINATOR_ENABLED
    //          p += sprintf(p, ",\"led_intensity\":%u", led_duty);
    //      #else ...
    //    Use:
    //      #if defined(LED_PIN) && LED_PIN >= 0
    //          p += sprintf(p, ",\"led_intensity\":%d", getLedIntensity()); // Use function from LedControl
    //      #else
    //          p += sprintf(p, ",\"led_intensity\":%d", -1); // Indicate LED not available
    //      #endif
    // ---

    static char json_response[1024]; // Make sure this buffer is large enough
    sensor_t * s = getCameraSensor();
    if(!s){ return httpd_resp_send_500(req); }

    char * p = json_response;
    *p++ = '{';
    // --- Copy the sensor status sprintf lines from app_httpd.cpp here ---
    p += sprintf(p, "\"xclk\":%u,", s->xclk_freq_hz / 1000000);
    p += sprintf(p, "\"pixformat\":%u,", s->pixformat);
    // ... (copy all other status sprintf lines) ...
    p += sprintf(p, "\"colorbar\":%u", s->status.colorbar);

    // --- **MODIFIED LED Status** ---
    #if defined(LED_PIN) && LED_PIN >= 0
        p += sprintf(p, ",\"led_intensity\":%d", getLedIntensity());
    #else
        p += sprintf(p, ",\"led_intensity\":%d", -1);
    #endif
    // --- End of LED Status ---

    *p++ = '}';
    *p++ = 0;
    httpd_resp_set_type(req, "application/json");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    return httpd_resp_send(req, json_response, strlen(json_response));
}

esp_err_t captureHandler(httpd_req_t *req){
    camera_fb_t * fb = NULL;
    esp_err_t res = ESP_OK;
    int64_t fr_start = esp_timer_get_time();

    #if defined(LED_PIN) && LED_PIN >= 0
        controlLed(true, getLedIntensity()); // Turn LED on with current intensity
        vTaskDelay(150 / portTICK_PERIOD_MS); // Delay needed for LED to be effective
        fb = esp_camera_fb_get();
        controlLed(false); // Turn LED off
    #else
        fb = esp_camera_fb_get(); // Capture without LED control
    #endif

    if (!fb) {
        Serial.println("Camera capture failed");
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }

    // ... (Set headers, send response, return frame buffer) ...
    httpd_resp_set_type(req, "image/jpeg");
    httpd_resp_set_hdr(req, "Content-Disposition", "inline; filename=capture.jpg");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

     char ts[32];
    snprintf(ts, 32, "%ld.%06ld", fb->timestamp.tv_sec, fb->timestamp.tv_usec);
    httpd_resp_set_hdr(req, "X-Timestamp", (const char *)ts);


    size_t fb_len = 0;
    if(fb->format == PIXFORMAT_JPEG){
        fb_len = fb->len;
        res = httpd_resp_send(req, (const char *)fb->buf, fb->len);
    } else {
        jpg_chunking_t jchunk = {req, 0};
        res = frame2jpg_cb(fb, 80, jpg_encode_stream, &jchunk)?ESP_OK:ESP_FAIL;
        httpd_resp_send_chunk(req, NULL, 0);
        fb_len = jchunk.len;
    }
    esp_camera_fb_return(fb);

    int64_t fr_end = esp_timer_get_time();
    Serial.printf("JPG: %uB %ums\n", (uint32_t)(fb_len), (uint32_t)((fr_end - fr_start)/1000));
    return res;
}


esp_err_t streamHandler(httpd_req_t *req){
    // --- Copy implementation from app_httpd.cpp's stream_handler ---
    // **IMPORTANT CHANGES:**
    // 1. Replace `isStreaming = true; enable_led(true);` with `setLedStreamingState(true);`
    // 2. Replace `isStreaming = false; enable_led(false);` with `setLedStreamingState(false);`
    // 3. Initialize ra_filter here or ensure it's initialized once elsewhere (e.g., in WebServerManager start).
    // ---
    camera_fb_t * fb = NULL;
    struct timeval _timestamp;
    esp_err_t res = ESP_OK;
    size_t _jpg_buf_len;
    uint8_t * _jpg_buf;
    char * part_buf[128]; // was 64, increased size

    static int64_t last_frame = 0;
    if(!last_frame) {
        last_frame = esp_timer_get_time();
    }

    res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
    if(res != ESP_OK){ return res; }

    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    httpd_resp_set_hdr(req, "X-Framerate", "60"); // Set desired framerate header

    #if defined(LED_PIN) && LED_PIN >= 0
        setLedStreamingState(true); // Indicate streaming started, turn on LED if intensity > 0
    #endif

    while(true){
        fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("Camera capture failed");
            res = ESP_FAIL;
        } else {
             _timestamp.tv_sec = fb->timestamp.tv_sec;
             _timestamp.tv_usec = fb->timestamp.tv_usec;
            if(fb->format != PIXFORMAT_JPEG){
                // ... (frame conversion logic from app_httpd.cpp) ...
                 bool jpeg_converted = frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
                 esp_camera_fb_return(fb);
                 fb = NULL;
                 if(!jpeg_converted){
                    Serial.println("JPEG compression failed");
                    res = ESP_FAIL;
                 }
            } else {
                _jpg_buf_len = fb->len;
                _jpg_buf = fb->buf;
            }
        } // end if (!fb)

        if(res == ESP_OK){
             // Send boundary and part header
             res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
             if (res == ESP_OK) {
                size_t hlen = snprintf((char *)part_buf, 128, _STREAM_PART, _jpg_buf_len, _timestamp.tv_sec, _timestamp.tv_usec);
                res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
             }
             // Send JPEG data
             if (res == ESP_OK) {
                 res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
             }
        }

        // Return frame buffer if it was acquired directly
        if(fb){
            esp_camera_fb_return(fb);
            fb = NULL;
            _jpg_buf = NULL;
        } else if (_jpg_buf){ // Free buffer if it was allocated by frame2jpg
            free(_jpg_buf);
            _jpg_buf = NULL;
        }

        if(res != ESP_OK){
             Serial.printf("Send frame failed: 0x%x\n", res);
             break; // Exit loop on error
        }

        // Frame rate calculation (from app_httpd.cpp)
        int64_t fr_end = esp_timer_get_time();
        int64_t frame_time = fr_end - last_frame;
        last_frame = fr_end;
        frame_time /= 1000;
        uint32_t avg_frame_time = ra_filter_run(&ra_filter, frame_time);
        // Serial.printf("MJPG: %uB %ums (%.1ffps), AVG: %ums (%.1ffps)\n",
        //     (uint32_t)(_jpg_buf_len),
        //     (uint32_t)frame_time, 1000.0 / (uint32_t)frame_time,
        //     avg_frame_time, 1000.0 / avg_frame_time);

    } // end while(true)

    #if defined(LED_PIN) && LED_PIN >= 0
        setLedStreamingState(false); // Indicate streaming stopped, turn off LED
    #endif

    Serial.println("Stream handler ending.");
    return res;
}

esp_err_t moveHandler(httpd_req_t *req) {
    char content[150]; // Buffer for the request body
    int ret, remaining = req->content_len;
    int received = 0;

    // 1. Read the request body
    if (remaining == 0) {
        Serial.println("Error: POST body is empty for /move.");
        httpd_resp_set_status(req, "400 Bad Request");
        httpd_resp_send(req, "Empty request body", HTTPD_RESP_USE_STRLEN);
        return ESP_FAIL;
    }

    if (remaining >= sizeof(content)) { // Check if content_len is too large for buffer
        Serial.printf("Error: POST body too large (%d bytes) for buffer (%d bytes).\n", remaining, sizeof(content));
        httpd_resp_set_status(req, "413 Request Entity Too Large");
        httpd_resp_send(req, "Request body too large", HTTPD_RESP_USE_STRLEN);
        return ESP_FAIL;
    }

    while (received < req->content_len) {
        ret = httpd_req_recv(req, content + received, req->content_len - received);
        if (ret <= 0) {
            if (ret == HTTPD_SOCK_ERR_TIMEOUT) {
                // If timeout, can retry or fail
                Serial.println("Timeout receiving POST body chunk.");
                // For simplicity, we'll fail on timeout during recv
                httpd_resp_send_500(req); // Or 408 Request Timeout
                return ESP_FAIL;
            }
            Serial.println("Failed to receive POST body chunk.");
            httpd_resp_send_500(req);
            return ESP_FAIL;
        }
        received += ret;
    }
    content[received] = '\0'; // Null-terminate the received content

    Serial.printf("Received POST body for /move: [%s]\n", content); // Print with brackets to see invisible chars

    // 2. Parse JSON-like string for "direction" and "speed"
    char direction[32] = {0};
    int speed = 150; // Default speed if not found or parse error
    bool direction_found = false;
    bool speed_found = false;

    // --- Parse "direction" ---
    char *key_ptr = strstr(content, "\"direction\"");
    if (key_ptr) {
        char *value_ptr = strchr(key_ptr, ':');
        if (value_ptr) {
            value_ptr++; // Move past ':'
            while (*value_ptr == ' ' || *value_ptr == '\t' || *value_ptr == '"') { // Skip whitespace and opening quote
                value_ptr++;
            }
            int i = 0;
            while (*value_ptr != '"' && *value_ptr != '\0' && i < sizeof(direction) - 1) {
                direction[i++] = *value_ptr++;
            }
            direction[i] = '\0'; // Null-terminate
            if (strlen(direction) > 0) {
                direction_found = true;
            }
        }
    }

    // --- Parse "speed" ---
    key_ptr = strstr(content, "\"speed\"");
    if (key_ptr) {
        char *value_ptr = strchr(key_ptr, ':');
        if (value_ptr) {
            value_ptr++; // Move past ':'
            while (*value_ptr == ' ' || *value_ptr == '\t') { // Skip whitespace
                value_ptr++;
            }
            if (isdigit((unsigned char)*value_ptr) || (*value_ptr == '-' && isdigit((unsigned char)*(value_ptr+1))) ) { // Check for digit or negative sign
                speed = atoi(value_ptr); // atoi stops at first non-digit
                // Constrain speed
                if (speed < 0) speed = 0;
                if (speed > 255) speed = 255; // Assuming 0-255 range for PWM
                speed_found = true;
            }
        }
    }

    // 3. Act on parsed values
    if (direction_found) {
        Serial.printf("Parsed direction: [%s], Parsed speed: %d (Speed field %s)\n",
                      direction, speed, speed_found ? "found" : "not found/defaulted");

        if (strcmp(direction, "forward") == 0) {
            moveForward(speed);
        } else if (strcmp(direction, "backward") == 0) {
            moveBackward(speed);
        } else if (strcmp(direction, "left") == 0) {
            turnLeft(speed);
        } else if (strcmp(direction, "right") == 0) {
            turnRight(speed);
        } else if (strcmp(direction, "stop") == 0) {
            stopMotors();
        } else {
            Serial.printf("Unknown move direction in POST: [%s]\n", direction);
            httpd_resp_set_status(req, "400 Bad Request");
            httpd_resp_send(req, "Unknown direction value", HTTPD_RESP_USE_STRLEN);
            return ESP_FAIL;
        }

        httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
        httpd_resp_send(req, "OK", HTTPD_RESP_USE_STRLEN);
        return ESP_OK;

    } else {
        Serial.println("Could not parse 'direction' key/value from POST body.");
        httpd_resp_set_status(req, "400 Bad Request");
        httpd_resp_send(req, "Malformed request: 'direction' key/value missing or invalid", HTTPD_RESP_USE_STRLEN);
        return ESP_FAIL;
    }
}

// Call this once to initialize the filter
void initializeWebRequestHandlers() {
     ra_filter_init(&ra_filter, 20); // Initialize rolling average filter for FPS display
}