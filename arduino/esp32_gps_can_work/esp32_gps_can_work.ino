#include <WiFi.h>
#include <PubSubClient.h>
#include <TinyGPS++.h>
#include <HardwareSerial.h>

// WiFi 設定
const char* ssid = "SEC304";
const char* password = "sec304sec304";

// MQTT 設定
const char* mqtt_server = "34.168.176.224";
const char* mqtt_topic = "gps";
const char* debug_topic = "debug";

// 創建 TinyGPS++ 對象
TinyGPSPlus gps;

// 定義接線引腳
static const int RXPin = 16, TXPin = 17;
static const uint32_t GPSBaud = 9600;

// 創建 HardwareSerial 對象
HardwareSerial ss(1);

// WiFi 和 MQTT 客戶端
WiFiClient espClient;
PubSubClient client(espClient);

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

  Serial.println(F("GPS 初始化完成"));
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // 讀取 GPS 數據
  while (ss.available() > 0) {
    gps.encode(ss.read());
    if (gps.location.isUpdated()) {
      // 打印經緯度
      Serial.print(F("Latitude: "));
      Serial.println(gps.location.lat(), 6);
      Serial.print(F("Longitude: "));
      Serial.println(gps.location.lng(), 6);

      // 構建要傳送的消息
      String payload = String("{\"lat\":") + String(gps.location.lat(), 6) + 
                       String(",\"lng\":") + String(gps.location.lng(), 6) + 
                       String("}");

      // 發送消息到 MQTT 伺服器
      client.publish(mqtt_topic, payload.c_str());
    }
  }
}
