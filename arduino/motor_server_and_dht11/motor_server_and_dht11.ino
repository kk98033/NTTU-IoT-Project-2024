#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Servo.h>
#include "DHT.h"
#include <Wire.h>
// #include <LiquidCrystal_I2C.h>

#define DHTPIN D2      // 定義DHT傳感器數據引腳連接到ESP8266的D2
#define DHTTYPE DHT11  // 如果你使用的是DHT22，將DHT11替換為DHT22
// 設定 LCD 地址 (通常是 0x27 或 0x3F)
// LiquidCrystal_I2C lcd(0x27, 16, 2);

DHT dht(DHTPIN, DHTTYPE);
const char* ssid = "SEC304";
const char* password = "sec304sec304";
const char* mqtt_server = "34.168.176.224";

WiFiClient espClient;
PubSubClient client(espClient);
Servo myservo;  // 創建伺服對象來控制伺服馬達

int servoPin = D4;  // 伺服控制腳位
int onPosition = 180; // ON 位置
int offPosition = -180; // OFF 位置

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
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(message);

  if (message == "ON") {
    Serial.println("Turning servo to ON position");
    myservo.write(onPosition); // 轉動伺服馬達到 ON 位置
  } else if (message == "OFF") {
    Serial.println("Turning servo to OFF position");
    myservo.write(offPosition); // 轉動伺服馬達到 OFF 位置
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    Serial.print("Server: ");
    Serial.print(mqtt_server);
    Serial.print(", Port: 1883");

    if (client.connect("ESP8266Client")) {
      Serial.println("connected");
      client.subscribe("esp8266/control");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH); // Turn the LED off initially

  myservo.attach(servoPin);  // 將伺服物件附加到伺服控制腳位
  myservo.write(offPosition); // 初始化伺服位置為 OFF

  Serial.begin(115200);
  setup_wifi();
  dht.begin();
  if (WiFi.status() == WL_CONNECTED) {
    client.setServer(mqtt_server, 1883);
    client.setCallback(callback);
  } else {
    Serial.println("Skipping MQTT setup due to WiFi connection failure");
  }

  // lcd.begin(16,2);
  // lcd.backlight();
  
  // // 顯示訊息
  // lcd.setCursor(0, 0);
  // lcd.print("Hello, World!");
  // lcd.setCursor(0, 1);
  // lcd.print("ESP8266 LCD");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    if (!client.connected()) {
      reconnect();
    }
    client.loop();
    
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    if (isnan(h) || isnan(t)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }

    String payload = "Temperature: " + String(t) + "C, Humidity: " + String(h) + "%";
    Serial.print("Publishing message: ");
    Serial.println(payload);
    client.publish("esp8266/DHT11", payload.c_str());
  } else {
    Serial.println("WiFi not connected");
  }
  
  delay(2000); // 延遲2秒
}
