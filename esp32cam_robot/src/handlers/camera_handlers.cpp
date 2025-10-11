// src/handlers/camera_handlers.cpp
#include "camera_handlers.h"
#include "../CameraController.h"
#include "../LedControl.h"
#include "../camera_index.h"
#include "img_converters.h"
#include "fb_gfx.h"
#include "esp_timer.h"
#include <Arduino.h>
#include <stdlib.h>
#include <string.h>
#include "esp_http_server.h"
#include "sdkconfig.h"
#include <ctype.h>

typedef struct {
    httpd_req_t *req;
    size_t len;
} jpg_chunking_t_local;

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

static ra_filter_t ra_filter_stream;

static esp_err_t parse_get(httpd_req_t *req, char **obuf) {
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

// And the ra_filter functions for streamHandler
static ra_filter_t *ra_filter_init_local(ra_filter_t *filter, size_t sample_size){
    memset(filter, 0, sizeof(ra_filter_t));
    filter->values = (int *)malloc(sample_size * sizeof(int));
    if(!filter->values){
        return NULL;
    }
    memset(filter->values, 0, sample_size * sizeof(int));
    filter->size = sample_size;
    return filter;
}

static int ra_filter_run_local(ra_filter_t *filter, int value){
    if(!filter->values){ return value; }
    filter->sum -= filter->values[filter->index];
    filter->values[filter->index] = value;
    filter->sum += filter->values[filter->index];
    filter->index++;
    filter->index = filter->index % filter->size;
    if (filter->count < filter->size) { filter->count++; }
    return filter->sum / filter->count;
}

// For streamHandler's jpg_encode_stream
static size_t jpg_encode_stream_local(void * arg, size_t index, const void* data, size_t len){
    jpg_chunking_t_local *j = (jpg_chunking_t_local *)arg;
    if(!index){ 
        j->len = 0;
    }
    if(httpd_resp_send_chunk(j->req, (const char *)data, len) != ESP_OK){
        return 0;
    }
    j->len += len;
    return len;
}

// --- Handler Implementations ---

esp_err_t indexHandler(httpd_req_t *req) {
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

esp_err_t statusHandler(httpd_req_t *req){
    static char json_response[1024];
    sensor_t * s = getCameraSensor();
    if(!s){ return httpd_resp_send_500(req); }

    char * p = json_response;
    *p++ = '{';
    p += sprintf(p, "\"xclk\":%u,", s->xclk_freq_hz / 1000000);
    p += sprintf(p, "\"pixformat\":%u,", s->pixformat);
    p += sprintf(p, "\"framesize\":%u,", s->status.framesize);
    p += sprintf(p, "\"quality\":%u,", s->status.quality);
    p += sprintf(p, "\"brightness\":%d,", s->status.brightness);
    p += sprintf(p, "\"contrast\":%d,", s->status.contrast);
    p += sprintf(p, "\"saturation\":%d,", s->status.saturation);
    p += sprintf(p, "\"sharpness\":%d,", s->status.sharpness);
    p += sprintf(p, "\"special_effect\":%u,", s->status.special_effect);
    p += sprintf(p, "\"wb_mode\":%u,", s->status.wb_mode);
    p += sprintf(p, "\"awb\":%u,", s->status.awb);
    p += sprintf(p, "\"awb_gain\":%u,", s->status.awb_gain);
    p += sprintf(p, "\"aec\":%u,", s->status.aec);
    p += sprintf(p, "\"aec2\":%u,", s->status.aec2);
    p += sprintf(p, "\"ae_level\":%d,", s->status.ae_level);
    p += sprintf(p, "\"aec_value\":%u,", s->status.aec_value);
    p += sprintf(p, "\"agc\":%u,", s->status.agc);
    p += sprintf(p, "\"agc_gain\":%u,", s->status.agc_gain);
    p += sprintf(p, "\"gainceiling\":%u,", s->status.gainceiling);
    p += sprintf(p, "\"bpc\":%u,", s->status.bpc);
    p += sprintf(p, "\"wpc\":%u,", s->status.wpc);
    p += sprintf(p, "\"raw_gma\":%u,", s->status.raw_gma);
    p += sprintf(p, "\"lenc\":%u,", s->status.lenc);
    p += sprintf(p, "\"hmirror\":%u,", s->status.hmirror);
    p += sprintf(p, "\"dcw\":%u,", s->status.dcw);
    p += sprintf(p, "\"colorbar\":%u", s->status.colorbar);

    #if defined(LED_PIN) && LED_PIN >= 0
        p += sprintf(p, ",\"led_intensity\":%d", getLedIntensity());
    #else
        p += sprintf(p, ",\"led_intensity\":%d", -1);
    #endif

    *p++ = '}';
    *p++ = 0;
    httpd_resp_set_type(req, "application/json");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    return httpd_resp_send(req, json_response, strlen(json_response));
}

esp_err_t controlHandler(httpd_req_t *req) {
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

    if (!strcmp(variable, "framesize")) {
        if (s->pixformat == PIXFORMAT_JPEG) { res = s->set_framesize(s, (framesize_t)val); }
    } 
    else if (!strcmp(variable, "quality")) { res = s->set_quality(s, val); }
    else if (!strcmp(variable, "contrast")) { res = s->set_contrast(s, val); }
    else if (!strcmp(variable, "brightness")) { res = s->set_brightness(s, val); }
    else if (!strcmp(variable, "saturation")) { res = s->set_saturation(s, val); }
    else if (!strcmp(variable, "gainceiling")) { res = s->set_gainceiling(s, (gainceiling_t)val); }
    else if (!strcmp(variable, "colorbar")) { res = s->set_colorbar(s, val); }
    else if (!strcmp(variable, "awb")) { res = s->set_whitebal(s, val); }
    else if (!strcmp(variable, "agc")) { res = s->set_gain_ctrl(s, val); }
    else if (!strcmp(variable, "aec")) { res = s->set_exposure_ctrl(s, val); }
    else if (!strcmp(variable, "hmirror")) { res = s->set_hmirror(s, val); }
    else if (!strcmp(variable, "vflip")) { res = s->set_vflip(s, val); }
    else if (!strcmp(variable, "awb_gain")) { res = s->set_awb_gain(s, val); }
    else if (!strcmp(variable, "agc_gain")) { res = s->set_agc_gain(s, val); }
    else if (!strcmp(variable, "aec_value")) { res = s->set_aec_value(s, val); }
    else if (!strcmp(variable, "aec2")) { res = s->set_aec2(s, val); }
    else if (!strcmp(variable, "dcw")) { res = s->set_dcw(s, val); }
    else if (!strcmp(variable, "bpc")) { res = s->set_bpc(s, val); }
    else if (!strcmp(variable, "wpc")) { res = s->set_wpc(s, val); }
    else if (!strcmp(variable, "raw_gma")) { res = s->set_raw_gma(s, val); }
    else if (!strcmp(variable, "lenc")) { res = s->set_lenc(s, val); }
    else if (!strcmp(variable, "special_effect")) { res = s->set_special_effect(s, val); }
    else if (!strcmp(variable, "wb_mode")) { res = s->set_wb_mode(s, val); }
    else if (!strcmp(variable, "ae_level")) { res = s->set_ae_level(s, val); }
    else if (!strcmp(variable, "ae_level")) res = s->set_ae_level(s, val);

    #if defined(LED_PIN) && LED_PIN >= 0
        else if (!strcmp(variable, "led_intensity")) {
            setLedIntensity(val);
            res = 0; // Command was handled successfully
        }
    #endif
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

esp_err_t captureHandler(httpd_req_t *req) {
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
        jpg_chunking_t_local jchunk = {req, 0};
        res = frame2jpg_cb(fb, 80, jpg_encode_stream_local, &jchunk)?ESP_OK:ESP_FAIL;
        httpd_resp_send_chunk(req, NULL, 0);
        fb_len = jchunk.len;
    }
    esp_camera_fb_return(fb);

    int64_t fr_end = esp_timer_get_time();
    Serial.printf("JPG: %uB %ums\n", (uint32_t)(fb_len), (uint32_t)((fr_end - fr_start)/1000));
    return res;
}

esp_err_t streamHandler(httpd_req_t *req) {
    camera_fb_t * fb = NULL;
    struct timeval _timestamp;
    esp_err_t res = ESP_OK;
    size_t _jpg_buf_len;
    uint8_t * _jpg_buf;
    char * part_buf[128];

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
        }

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
        } else if (_jpg_buf){
            free(_jpg_buf);
            _jpg_buf = NULL;
        }

        if(res != ESP_OK){
            Serial.printf("Send frame failed: 0x%x\n", res);
            break;
        }

        // Frame rate calculation (from app_httpd.cpp)
        int64_t fr_end = esp_timer_get_time();
        int64_t frame_time = fr_end - last_frame;
        last_frame = fr_end;
        frame_time /= 1000;
        uint32_t avg_frame_time = ra_filter_run_local(&ra_filter_stream, frame_time);
    }

    #if defined(LED_PIN) && LED_PIN >= 0
        setLedStreamingState(false);
    #endif

    Serial.println("Stream handler ending.");
    return res;
}