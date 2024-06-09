#include <Arduino.h>
#include <WiFi.h>
#include <driver/adc.h>

#define AUDIO_BUFFER_MAX 512

uint8_t audioBuffer[AUDIO_BUFFER_MAX];
uint8_t transmitBuffer[AUDIO_BUFFER_MAX];
uint32_t bufferPointer = 0;

const char* ssid = "SEC304";
const char* password = "sec304sec304";
const char* host = "210.240.160.27";

bool transmitNow = false;

WiFiClient client;

hw_timer_t * timer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;

void IRAM_ATTR onTimer() {
  portENTER_CRITICAL_ISR(&timerMux);
  int adcVal = adc1_get_voltage(ADC1_CHANNEL_0);
  if (adcVal > 3800) {
    adcVal = 4095;
  }
  uint8_t value = map(adcVal, 0 , 4095, 0, 255);
  audioBuffer[bufferPointer] = value;
  bufferPointer++;

  if (bufferPointer == AUDIO_BUFFER_MAX) {
    bufferPointer = 0;
    memcpy(transmitBuffer, audioBuffer, AUDIO_BUFFER_MAX);
    transmitNow = true;
  }
  portEXIT_CRITICAL_ISR(&timerMux);
}

void setup() {
  Serial.begin(115200);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("MY IP address: ");
  Serial.println(WiFi.localIP());

  adc1_config_width(ADC_WIDTH_12Bit);
  adc1_config_channel_atten(ADC1_CHANNEL_0, ADC_ATTEN_11db);

  const int port = 8888;
  while (!client.connect(host, port)) {
    Serial.println("connection failed");
    delay(1000);
  }

  Serial.println("connected to server");

  timer = timerBegin(0, 80, true);
  timerAttachInterrupt(timer, &onTimer, true);
  timerAlarmWrite(timer, 125, true);
  timerAlarmEnable(timer);
}

void loop() {
  if (transmitNow) {
    transmitNow = false;
    client.write((const uint8_t *)audioBuffer, sizeof(audioBuffer));
  }
}
