#include <driver/i2s.h>
#include <math.h>

#define I2S_NUM         I2S_NUM_0
#define I2S_BCLK        27
#define I2S_LRC         26
#define I2S_DIN         25

void setup() {
    Serial.begin(115200);
  
    // I2S configuration
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = 44100,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
        .communication_format = (i2s_comm_format_t)(I2S_COMM_FORMAT_I2S | I2S_COMM_FORMAT_I2S_MSB),
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = 64,
        .use_apll = false,
        .tx_desc_auto_clear = true,
        .fixed_mclk = 0
    };

    // I2S pins configuration
    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_BCLK,
        .ws_io_num = I2S_LRC,
        .data_out_num = I2S_DIN,
        .data_in_num = I2S_PIN_NO_CHANGE
    };

    i2s_driver_install(I2S_NUM, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_NUM, &pin_config);
}

void loop() {
    const int sampleRate = 44100; // Sample rate
    const int amplitude = 2000; // Amplitude of the sine wave
    const int frequency = 440; // Frequency of the sine wave (440Hz for A4)
    int16_t samples[44100];

    // Generate a 1-second sine wave at 440Hz
    for (int i = 0; i < sampleRate; i++) {
        samples[i] = amplitude * sinf(2 * M_PI * frequency * i / sampleRate);
    }

    // Play the sine wave continuously
    while (true) {
        size_t bytes_written;
        i2s_write(I2S_NUM_0, samples, sizeof(samples), &bytes_written, portMAX_DELAY);
        delay(10); // Add a small delay to prevent potential issues
    }
}
