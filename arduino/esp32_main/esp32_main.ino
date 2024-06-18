#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <driver/adc.h>

#include "BuzzerSound.h"



#define AUDIO_BUFFER_MAX 512

uint8_t audioBuffer[AUDIO_BUFFER_MAX];
uint8_t transmitBuffer[AUDIO_BUFFER_MAX];
uint32_t bufferPointer = 0;

const char* ssid = "Trixie is my wifu la";
const char* password = "ilovefsya";
const char* host = "210.240.160.27";
const char* mqtt_server = "34.168.176.224";
const char* mqtt_topic = "beep";

bool transmitNow = false;

WiFiClient espClient;
PubSubClient mqttClient(espClient);
WiFiClient client;

hw_timer_t * timer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;

const int redPin = 16;
const int greenPin = 17;
const int bluePin = 18;
BuzzerSound buzzer(5, 0, 8); // 設置蜂鳴器引腳為 GPIO 5，使用 LEDC 頻道 0，解析度為 8 位元

TaskHandle_t Task1;
TaskHandle_t Task2;

void setupLED() {
  // 使用不同的頻道來設置 LED
  ledcSetup(1, 5000, 8); // 頻道 1，頻率 5000 Hz，解析度 8 位
  ledcSetup(2, 5000, 8); // 頻道 2，頻率 5000 Hz，解析度 8 位
  ledcSetup(3, 5000, 8); // 頻道 3，頻率 5000 Hz，解析度 8 位

  // 將頻道附加到引腳
  ledcAttachPin(redPin, 1);
  ledcAttachPin(greenPin, 2);
  ledcAttachPin(bluePin, 3);
}

void setColor(uint8_t red, uint8_t green, uint8_t blue) {
  ledcWrite(1, red);
  ledcWrite(2, green);
  ledcWrite(3, blue);
}

void turnOffLED() {
  setColor(0, 0, 0);
}

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

void setup_wifi() {
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
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (unsigned int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();

  // 如果接收到 "beep" 主題的訊息，觸發蜂鳴器
  if (String(topic) == "mic_on") {
    setColor(0, 0, 255); // 設置為橘色
    // setColor(0, 255, 0); // 設置為綠色
    mic_on();
  }
  if (String(topic) == "mic_off") {
    setColor(0, 255, 0); // 設置為綠色
    // turnOffLED();
    mic_off();
  }
}

void mic_on() {
    Serial.println("Mic On");
    buzzer.playWakeupSound();
    vTaskDelay(10 / portTICK_PERIOD_MS);
    buzzer.stopAll();
}

void mic_off() {
    Serial.println("Mic Off");
    buzzer.playShutdownSound();
    vTaskDelay(10 / portTICK_PERIOD_MS);
    buzzer.stopAll();
}

void reconnect() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    // 注意：確保連接ID的唯一性，例如 ESP32Client + 隨機數
    String clientId = "ESP32Client-" + String(random(0xffff), HEX);
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("connected");

      mqttClient.subscribe(mqtt_topic);
      mqttClient.subscribe("mic_on");
      mqttClient.subscribe("mic_off");

      Serial.print("Subscribed to topic: ");
      Serial.println(mqtt_topic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}


void Task1code(void *pvParameters) {
  Serial.print("Task1 running on core ");
  Serial.println(xPortGetCoreID());

  const int port = 8888;

  while (true) {
    if (!client.connected()) {
      Serial.println("Connection to server lost, trying to reconnect...");
      setColor(255, 0, 0); // 設置為紅色
      buzzer.stopAll();
      while (!client.connect(host, port)) {
        Serial.println("Reconnection failed, retrying in 5 seconds...");
        delay(5000);
      }
      Serial.println("Reconnected to server");
      buzzer.playConnectionSound();
      setColor(0, 255, 0); // 設置為綠色

      // Reinitialize timer
      if (timer) {
        timerEnd(timer);
      }
      timer = timerBegin(0, 80, true);
      timerAttachInterrupt(timer, &onTimer, true);
      timerAlarmWrite(timer, 125, true);
      timerAlarmEnable(timer);
    }

    if (transmitNow) {
      transmitNow = false;
      client.write((const uint8_t *)transmitBuffer, sizeof(transmitBuffer));
      mqttClient.publish("audio/data", (const char *)transmitBuffer, sizeof(transmitBuffer));
    }

    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
}


void Task2code( void * pvParameters ) {
  Serial.print("Task2 running on core ");
  Serial.println(xPortGetCoreID());

  for(;;) {
    if (!mqttClient.connected()) {
      reconnect();
    }
    mqttClient.loop();
    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
}

void setup() {
  Serial.begin(115200);
  setupLED(); // 初始化LED
  setColor(255, 0, 0); // 設置為紅色

  setup_wifi();

  buzzer.playStartupSound();

  mqttClient.setServer(mqtt_server, 1883);
  mqttClient.setCallback(callback);

  reconnect(); // 確保在setup中進行一次MQTT連接嘗試

  adc1_config_width(ADC_WIDTH_12Bit);
  adc1_config_channel_atten(ADC1_CHANNEL_0, ADC_ATTEN_11db);

  xTaskCreatePinnedToCore(
    Task1code,   /* Task function. */
    "Task1",     /* name of task. */
    10000,       /* Stack size of task */
    NULL,        /* parameter of the task */
    1,           /* priority of the task */
    &Task1,      /* Task handle to keep track of created task */
    0);          /* pin task to core 0 */

  xTaskCreatePinnedToCore(
    Task2code,   /* Task function. */
    "Task2",     /* name of task. */
    10000,       /* Stack size of task */
    NULL,        /* parameter of the task */
    1,           /* priority of the task */
    &Task2,      /* Task handle to keep track of created task */
    1);          /* pin task to core 1 */
}


void loop() {
  // 空的loop函數，所有工作由任務來完成
}
