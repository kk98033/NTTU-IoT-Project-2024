#include <WiFi.h>
#include <WebSocketsClient.h>

const char* ssid = "SEC304";
const char* password = "sec304sec304";
const char* serverAddress = "210.240.160.27";
const uint16_t serverPort = 5000;
const char* path = "/";

WebSocketsClient webSocket;

const int micPin = 34;
const int bufferSize = 1024;
int16_t audioBuffer[bufferSize];
int bufferIndex = 0;

void setup() {
  Serial.begin(115200);

  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Waiting for WiFi connection...");
  }
  Serial.println("Connected to WiFi");

  Serial.println("Connecting to WebSocket server...");
  webSocket.begin(serverAddress, serverPort, path);
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);

  analogSetPinAttenuation(micPin, ADC_11db);
}

void loop() {
  webSocket.loop();
  
  int16_t micValue = analogRead(micPin);
  Serial.print("Mic value: ");
  Serial.println(micValue);

  audioBuffer[bufferIndex++] = micValue;

  if (bufferIndex >= bufferSize) {
    bufferIndex = 0;
    if (webSocket.isConnected()) {
      webSocket.sendBIN((uint8_t*)audioBuffer, sizeof(audioBuffer));
      Serial.println("Audio data sent");
    } else {
      Serial.println("WebSocket not connected, unable to send data");
    }
  }

  delay(1);
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.println("WebSocket Disconnected");
      break;
    case WStype_CONNECTED:
      Serial.println("WebSocket Connected");
      break;
    case WStype_TEXT:
      Serial.printf("Received Text: %s\n", payload);
      break;
    case WStype_BIN:
      Serial.println("Received Binary Data");
      break;
    case WStype_ERROR:
      Serial.println("WebSocket Error");
      break;
    default:
      Serial.printf("WebSocket event: %d\n", type);
      break;
  }
}
