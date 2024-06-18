#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <ArduinoJson.h>
#include <time.h>
#include <WiFiUdp.h>

const char* ssid = "SEC304";
const char* password = "sec304sec304";
const char* mqtt_server = "34.168.176.224";
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 3600 * 8; // 台灣時區 GMT+8
const int daylightOffset_sec = 0;
String temperature = "N/A";
String humidity = "N/A";

// 設置 LCD 地址為 0x27，並設置列數和行數為 16 和 2
LiquidCrystal_I2C lcd(0x27, 16, 2);
WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  int wifi_attempts = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    wifi_attempts++;
    if (wifi_attempts > 20) {  // 10 seconds timeout for WiFi connection
      Serial.println();
      Serial.println("Failed to connect to WiFi");
      return;
    }
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.println("]");

  // 創建一個字符串來保存接收到的訊息
  char message[length + 1];
  strncpy(message, (char*)payload, length);
  message[length] = '\0'; // 確保字符串結束

  // 打印完整的訊息
  Serial.println(message);

  // 創建一個 JSON 解析器
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }

  // 提取溫度和濕度
  const char* temp = doc["Temperature"];
  const char* hum = doc["Humidity"];

  if (temp && hum) {
    temperature = String(temp);
    humidity = String(hum);
    Serial.print("Temperature: ");
    Serial.println(temperature);
    Serial.print("Humidity: ");
    Serial.println(humidity);
  } else {
    Serial.println("Invalid message format");
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // 客戶端 ID 使用唯一值，避免重複
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      client.subscribe("esp8266/DHT11");  // 訂閱指定主題
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void printLocalTime() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    Serial.println("Failed to obtain time");
    return;
  }

  char timeStr[16];
  strftime(timeStr, sizeof(timeStr), "%Y-%m-%d", &timeinfo);
  lcd.setCursor(2, 0);
  lcd.print(timeStr);

  strftime(timeStr, sizeof(timeStr), "%H:%M:%S", &timeinfo);
  lcd.setCursor(2, 1);
  lcd.print(timeStr);
}

void setup() {
  // 初始化 LCD
  lcd.init();
  // 打開背光
  lcd.backlight();
  Serial.begin(115200);
  setup_wifi();
  if (WiFi.status() == WL_CONNECTED) {
    client.setServer(mqtt_server, 1883);
    client.setCallback(callback);
    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  } else {
    Serial.println("Skipping MQTT setup due to WiFi connection failure");
  }
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    if (!client.connected()) {
      reconnect();
    }
    client.loop();
    lcd.clear();
    printLocalTime();
    delay(3000);
    lcd.clear();
    lcd.setCursor(2, 0);
    lcd.print("Temp:" + temperature);
    lcd.setCursor(1, 1);
    lcd.print("Humidity:" + humidity);
  } else {
    lcd.setCursor(0, 0);
    lcd.print("WiFi not connected");
  }

  delay(3000);
  lcd.clear();
}
