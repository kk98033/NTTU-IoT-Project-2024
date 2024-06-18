#ifndef BUZZER_SOUND_H
#define BUZZER_SOUND_H

#include <Arduino.h>

class BuzzerSound {
public:
    BuzzerSound(int pin, int channel, int resolution);
    void playStartupSound();
    void playWakeupSound();
    void playShutdownSound();
    void playConnectionSound();
    void stopAll();

private:
    int buzzerPin;
    int ledChannel;
    int resolution;
};

#endif
