const int buttonPin = 14;  // KY-004 連接到 GPIO14 (D5)
int buttonState = 0;       // 變數來儲存按鈕狀態

void setup() {
  // 初始化序列通訊，設定波特率為 57600
  Serial.begin(57600);
  
  // 初始化按鈕引腳為輸入模式
  pinMode(buttonPin, INPUT);
}

void loop() {
  // 讀取按鈕狀態
  buttonState = digitalRead(buttonPin);

  // 檢查按鈕是否被按下
  if (buttonState == LOW) {
    // 如果按下按鈕，輸出訊息到序列監視器
    Serial.println("Button pressed");
  } else {
    // 如果按鈕未按下，輸出訊息到序列監視器
    Serial.println("Button released");
  }

  // 等待一段時間，以避免太頻繁的讀取
  delay(200);
}
