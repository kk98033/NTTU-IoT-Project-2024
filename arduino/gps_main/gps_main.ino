#include <WiFi.h>
#include <PubSubClient.h>
#include <TinyGPS++.h>
#include <HardwareSerial.h>
#include <Wire.h>
#include <MPU6050.h>

// WiFi 設定
const char* ssid = "Trixie is my wifu la";
const char* password = "ilovefsya";

// MQTT 設定
const char* mqtt_server = "34.168.176.224";
const char* mqtt_topic = "gps";
const char* debug_topic = "debug";
const char* mpu_topic = "XYZ";

// 創建 TinyGPS++ 對象
TinyGPSPlus gps;

// 定義接線引腳
static const int RXPin = 16, TXPin = 17;
static const uint32_t GPSBaud = 9600;

// 創建 HardwareSerial 對象
HardwareSerial ss(1);

// MPU-6050 對象
MPU6050 mpu;

// WiFi 和 MQTT 客戶端
WiFiClient espClient;
PubSubClient client(espClient);

// 宣告變數來儲存MPU-6050數據
int16_t ax, ay, az;
int16_t gx, gy, gz;

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32Client")) {
      Serial.println("connected");
      // 傳送 debug 訊息
      client.publish(debug_topic, "ESP32 connected to MQTT broker");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  // 初始化序列監視器
  Serial.begin(115200);
  ss.begin(GPSBaud, SERIAL_8N1, RXPin, TXPin);

  setup_wifi();
  client.setServer(mqtt_server, 1883);

  // 初始化 MPU-6050
  Wire.begin();
  mpu.initialize();
  if (mpu.testConnection()) {
    Serial.println(F("MPU6050 connection successful"));
  } else {
    Serial.println(F("MPU6050 connection failed"));
  }

  Serial.println(F("GPS 初始化完成"));
}

// 定義計時器的間隔時間（例如，每 10 秒發送一次訊息）
const unsigned long debugInterval = 5000;
unsigned long previousMillis = 0;
// 定義 GPS 資料傳送的間隔時間（例如，每 30 秒發送一次訊息）
const unsigned long gpsSendInterval = 30000;
unsigned long previousGPSSendMillis = 0;
// 定義 MPU-6050 資料傳送的間隔時間（例如，每 10 秒發送一次訊息）
const unsigned long mpuSendInterval = 1000;
unsigned long previousMPUSendMillis = 0;

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long currentMillis = millis();

  // 讀取 GPS 數據
  bool gpsDataAvailable = false;
  while (ss.available() > 0) {
    gps.encode(ss.read());
    if (gps.location.isUpdated()) {
      gpsDataAvailable = true;
    }
  }

  // 如果有 GPS 數據且達到 GPS 資料傳送的間隔時間，發送 GPS 訊息
  if (gpsDataAvailable && currentMillis - previousGPSSendMillis >= gpsSendInterval) {
    previousGPSSendMillis = currentMillis;

    // 打印經緯度
    Serial.print(F("Latitude: "));
    Serial.println(gps.location.lat(), 6);
    Serial.print(F("Longitude: "));
    Serial.println(gps.location.lng(), 6);

    // 構建要傳送的消息
    String payload = "{\"lat\":" + String(gps.location.lat(), 6) + 
                     ",\"lng\":" + String(gps.location.lng(), 6) + 
                     "}";
    Serial.print("Publishing to topic ");
    Serial.print(mqtt_topic);
    Serial.print(": ");
    Serial.println(payload);

    // 發送消息到 MQTT 伺服器
    if (client.publish(mqtt_topic, payload.c_str())) {
      Serial.println("Publish success");
    } else {
      Serial.println("Publish failed");
    }
  }

  // 讀取 MPU-6050 數據且達到 MPU-6050 資料傳送的間隔時間
  if (currentMillis - previousMPUSendMillis >= mpuSendInterval) {
    previousMPUSendMillis = currentMillis;

    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    // 構建要傳送的消息
    String mpuPayload = "{\"ax\":" + String(ax) + 
                        ",\"ay\":" + String(ay) + 
                        ",\"az\":" + String(az) + 
                        ",\"gx\":" + String(gx) + 
                        ",\"gy\":" + String(gy) + 
                        ",\"gz\":" + String(gz) + 
                        "}";
    Serial.print("Publishing to topic ");
    Serial.print(mpu_topic);
    Serial.print(": ");
    Serial.println(mpuPayload);

    // 發送消息到 MQTT 伺服器
    if (client.publish(mpu_topic, mpuPayload.c_str())) {
      Serial.println("MPU6050 publish success");
    } else {
      Serial.println("MPU6050 publish failed");
    }
  }

  // 如果沒有 GPS 數據，且達到 debug 訊息的間隔時間，發送 debug 訊息
  if (!gpsDataAvailable && currentMillis - previousMillis >= debugInterval) {
    previousMillis = currentMillis;
    String debugPayload = "{\"debug\":\"No GPS data available\"}";
    Serial.print("Publishing debug to topic ");
    Serial.print(debug_topic);
    Serial.print(": ");
    Serial.println(debugPayload);

    // 發送 debug 訊息到 MQTT 伺服器
    if (client.publish(debug_topic, debugPayload.c_str())) {
      Serial.println("Debug publish success");
    } else {
      Serial.println("Debug publish failed");
    }
  }
}
