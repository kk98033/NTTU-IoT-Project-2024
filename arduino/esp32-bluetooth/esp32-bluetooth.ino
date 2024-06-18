#include "BluetoothA2DPSource.h"

BluetoothA2DPSource a2dp_source;

// 生成音頻數據的回調函數
int32_t get_sound_data(Frame *data, int32_t frameCount) {
    for (int i = 0; i < frameCount; i++) {
        data[i].channel1 = (int16_t)(sin(2.0 * M_PI * (double)i / 100.0) * 32000.0);
        data[i].channel2 = data[i].channel1;
    }
    return frameCount;
}

void setup() {
    Serial.begin(115200);
    Serial.println("Starting Bluetooth A2DP Source");
    // 開始藍牙A2DP源
    a2dp_source.start("MyMusic", get_sound_data); // "MyMusic" 是設備名稱
    Serial.println("Bluetooth A2DP Source started successfully");
}

void loop() {
    // 空的循環函數
}
