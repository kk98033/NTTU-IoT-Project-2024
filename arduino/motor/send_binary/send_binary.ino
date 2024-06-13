#include "WiFi.h"
#include "ESPAsyncWebServer.h"
 
const char* ssid = "SEC304";
const char* password =  "sec304sec304";
 
AsyncWebServer server(80);
AsyncWebSocket ws("/test");
 
void onWsEvent(AsyncWebSocket * server, AsyncWebSocketClient * client, AwsEventType type, void * arg, uint8_t *data, size_t len){
 
  if(type == WS_EVT_CONNECT){
    Serial.println("Websocket client connection received");
 
    uint8_t content[3] = {10,22,43};
 
    client->binary(content, 3);
 
  } else if(type == WS_EVT_DISCONNECT){
    Serial.println("Client disconnected");
  }
}
 
void setup(){
  Serial.begin(115200);
 
  WiFi.begin(ssid, password);
 
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi..");
  }
 
  Serial.println(WiFi.localIP());
 
  ws.onEvent(onWsEvent);
  server.addHandler(&ws);
 
  server.begin();
}
 
void loop(){}