#include "BuzzerSound.h"

BuzzerSound::BuzzerSound(int pin, int channel, int resolution) {
    buzzerPin = pin;
    ledChannel = channel;
    this->resolution = resolution;
    ledcSetup(ledChannel, 2000, resolution); // 初始頻率 2000 Hz
    ledcAttachPin(buzzerPin, ledChannel);
}

void BuzzerSound::stopAll() {
    ledcWriteTone(ledChannel, 0);
    vTaskDelay(10 / portTICK_PERIOD_MS);
}

void BuzzerSound::playStartupSound() {
    ledcWriteTone(ledChannel, 800); // 800 Hz
    vTaskDelay(100 / portTICK_PERIOD_MS); // 持續 100 毫秒
    ledcWriteTone(ledChannel, 1000); // 1000 Hz
    vTaskDelay(100 / portTICK_PERIOD_MS); // 持續 100 毫秒
    ledcWriteTone(ledChannel, 1200); // 1200 Hz
    vTaskDelay(100 / portTICK_PERIOD_MS); // 持續 100 毫秒
    ledcWriteTone(ledChannel, 0); // 停止
    vTaskDelay(10 / portTICK_PERIOD_MS); // 確保蜂鳴器停止
}

void BuzzerSound::playWakeupSound() {
    ledcWriteTone(ledChannel, 1000); // 1500 Hz
    vTaskDelay(100 / portTICK_PERIOD_MS); // 持續 100 毫秒
    ledcWriteTone(ledChannel, 0); // 停止
    vTaskDelay(10 / portTICK_PERIOD_MS); // 確保蜂鳴器停止
    vTaskDelay(50 / portTICK_PERIOD_MS); // 間隔 50 毫秒
    ledcWriteTone(ledChannel, 1500); // 1000 Hz
    vTaskDelay(100 / portTICK_PERIOD_MS); // 持續 100 毫秒
    ledcWriteTone(ledChannel, 0); // 停止
    vTaskDelay(10 / portTICK_PERIOD_MS); // 確保蜂鳴器停止
}

void BuzzerSound::playShutdownSound() {
    ledcWriteTone(ledChannel, 1500); // 1500 Hz
    vTaskDelay(100 / portTICK_PERIOD_MS); // 持續 100 毫秒
    ledcWriteTone(ledChannel, 0); // 停止
    vTaskDelay(10 / portTICK_PERIOD_MS); // 確保蜂鳴器停止
    vTaskDelay(50 / portTICK_PERIOD_MS); // 間隔 50 毫秒
    ledcWriteTone(ledChannel, 1000); // 1000 Hz
    vTaskDelay(100 / portTICK_PERIOD_MS); // 持續 100 毫秒
    ledcWriteTone(ledChannel, 0); // 停止
    vTaskDelay(10 / portTICK_PERIOD_MS); // 確保蜂鳴器停止
}

void BuzzerSound::playConnectionSound() {
    ledcWriteTone(ledChannel, 2000); // 2000 Hz
    vTaskDelay(100 / portTICK_PERIOD_MS); // 持續 100 毫秒
    ledcWriteTone(ledChannel, 2500); // 2500 Hz
    vTaskDelay(100 / portTICK_PERIOD_MS); // 持續 100 毫秒
    ledcWriteTone(ledChannel, 3000); // 3000 Hz
    vTaskDelay(100 / portTICK_PERIOD_MS); // 持續 100 毫秒
    ledcWriteTone(ledChannel, 0); // 停止
    vTaskDelay(10 / portTICK_PERIOD_MS); // 確保蜂鳴器停止
}
