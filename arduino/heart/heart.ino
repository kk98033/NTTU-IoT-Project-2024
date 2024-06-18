const int sensorPin = 34; // KY-039 接到 GPIO 34
const int threshold = 100; // 設置閾值來檢測心跳
unsigned long lastBeatTime = 0; // 上一次心跳的時間
int beatCount = 0; // 計數心跳次數

void setup() {
  Serial.begin(115200); // 設定序列通訊速度
  pinMode(sensorPin, INPUT);
}

void loop() {
  int sensorValue = analogRead(sensorPin); // 讀取 KY-039 的值
  int p
  Serial.println(sensorValue); // 將值輸出到序列監視器
  
  unsigned long currentTime = millis(); // 取得當前時間
  if (sensorValue > threshold) {
    if (currentTime - lastBeatTime > 300) { // 確保至少間隔300毫秒（防止重複計算）
      beatCount++;
      lastBeatTime = currentTime;
      Serial.print("Heart Beat Detected. Count: ");
      Serial.println(beatCount);
    }
  }
  
  delay(10); // 小延遲以避免過度頻繁的讀取
}
