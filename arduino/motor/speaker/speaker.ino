#include <Arduino.h>
#include <driver/i2s.h>

#define I2S_BCK_PIN     (26)
#define I2S_WS_PIN      (25)
#define I2S_DO_PIN      (22)

void setup() {
  Serial.begin(115200);
  Serial.println("Starting setup...");

  // Configure I2S
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = 44100,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S_MSB,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 64,
    .use_apll = false,
    .tx_desc_auto_clear = true,
    .fixed_mclk = 0
  };

  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_BCK_PIN,
    .ws_io_num = I2S_WS_PIN,
    .data_out_num = I2S_DO_PIN,
    .data_in_num = I2S_PIN_NO_CHANGE
  };

  esp_err_t err;

  err = i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  if (err != ESP_OK) {
    Serial.print("Failed to install I2S driver: ");
    Serial.println(err);
  } else {
    Serial.println("I2S driver installed successfully.");
  }

  err = i2s_set_pin(I2S_NUM_0, &pin_config);
  if (err != ESP_OK) {
    Serial.print("Failed to set I2S pins: ");
    Serial.println(err);
  } else {
    Serial.println("I2S pins set successfully.");
  }

  Serial.println("Setup complete.");
}

void loop() {
  size_t i2s_bytes_write = 0;
  const int sample_rate = 44100;
  const int frequency = 1000;  // Tone frequency 1000 Hz
  const int amplitude = 30000;

  int16_t samples[sample_rate];
  for (int i = 0; i < sample_rate; i++) {
    samples[i] = (int16_t)(amplitude * sin((2.0 * M_PI * frequency * i) / sample_rate));
  }

  while (1) {
    esp_err_t err = i2s_write(I2S_NUM_0, samples, sizeof(samples), &i2s_bytes_write, portMAX_DELAY);
    if (err != ESP_OK) {
      Serial.print("Error writing to I2S: ");
      Serial.println(err);
    }
  }
}

