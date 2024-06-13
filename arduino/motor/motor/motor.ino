#include <ESP8266WiFi.h>
#include <Servo.h>

Servo myservo;  // 創建伺服對象來控制伺服馬達

int servoPin = D4;  // 伺服控制腳位

void setup() {
  myservo.attach(servoPin);  // 將伺服物件附加到伺服控制腳位
  myservo.write(0);          // 初始化伺服位置為0度
}

void loop() {
  // 從 0 度轉到 180 度
  for (int pos = 0; pos <= 180; pos++) {
    myservo.write(pos);   // 設定伺服馬達位置
    delay(15);            // 等待伺服移動完成
  }

  delay(1000);  // 等待 1 秒

  // 從 180 度轉到 0 度
  for (int pos = 180; pos >= 0; pos--) {
    myservo.write(pos);   // 設定伺服馬達位置
    delay(15);            // 等待伺服移動完成
  }

  delay(1000);  // 等待 1 秒
}