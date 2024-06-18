#include <TinyGPS++.h>
#include <SoftwareSerial.h>

// 設定 GPS 模組的波特率
#define GPS_BAUDRATE 9600

TinyGPSPlus gps;  // 建立 TinyGPS++ 對象
SoftwareSerial ss(D5, D6); // RX, TX（將 D5 和 D6 更改為你的 ESP8266 引腳）

void setup() {
  Serial.begin(115200);
  ss.begin(GPS_BAUDRATE);
  Serial.println(F("ESP8266 - GPS module"));
}

void loop() {
  while (ss.available() > 0) {
    char c = ss.read();
    Serial.write(c);  // 顯示接收到的原始數據
    gps.encode(c);
  }

  if (gps.location.isValid()) {
    Serial.print(F("- latitude: "));
    Serial.println(gps.location.lat(), 6);

    Serial.print(F("- longitude: "));
    Serial.println(gps.location.lng(), 6);

    Serial.print(F("- altitude: "));
    if (gps.altitude.isValid())
      Serial.println(gps.altitude.meters());
    else
      Serial.println(F("INVALID"));
  } else {
    Serial.println(F("- location: INVALID"));
  }

  Serial.print(F("- speed: "));
  if (gps.speed.isValid()) {
    Serial.print(gps.speed.kmph());
    Serial.println(F(" km/h"));
  } else {
    Serial.println(F("INVALID"));
  }

  Serial.print(F("- GPS date&time: "));
  if (gps.date.isValid() && gps.time.isValid()) {
    Serial.print(gps.date.year());
    Serial.print(F("-"));
    Serial.print(gps.date.month());
    Serial.print(F("-"));
    Serial.print(gps.date.day());
    Serial.print(F(" "));
    Serial.print(gps.time.hour());
    Serial.print(F(":"));
    Serial.print(gps.time.minute());
    Serial.print(F(":"));
    Serial.println(gps.time.second());
  } else {
    Serial.println(F("INVALID"));
  }

  Serial.println();

  if (millis() > 5000 && gps.charsProcessed() < 10)
    Serial.println(F("No GPS data received: check wiring"));
}
