#include "Wire.h"
#include "I2Cdev.h"
#include "MPU6050.h"

// 創建 MPU6050 對象
MPU6050 mpu;

void setup() {
    // 初始化串口
    Serial.begin(115200);
    while (!Serial); // 等待串口連接

    // 初始化 I2C
    Wire.begin(21, 22); // SDA, SCL

    // 初始化 MPU6050
    Serial.println("Initializing MPU6050...");
    mpu.initialize();
    Serial.println(mpu.testConnection() ? "MPU6050 connection successful" : "MPU6050 connection failed");

    // 校準加速度計和陀螺儀（可選）
    // mpu.setXAccelOffset(-563);
    // mpu.setYAccelOffset(1376);
    // mpu.setZAccelOffset(1022);
    // mpu.setXGyroOffset(220);
    // mpu.setYGyroOffset(-76);
    // mpu.setZGyroOffset(-85);

    delay(1000); // 增加延遲讓傳感器穩定
}

void loop() {
    // 讀取加速度計數據
    int16_t ax, ay, az;
    int16_t gx, gy, gz;

    mpu.getAcceleration(&ax, &ay, &az);
    mpu.getRotation(&gx, &gy, &gz);

    // 檢查讀數是否為零
    if (ax == 0 && ay == 0 && az == 0 && gx == 0 && gy == 0 && gz == 0) {
        Serial.println("Invalid reading. Reinitializing MPU6050...");
        mpu.initialize(); // 重新初始化 MPU6050
    } else {
        // 輸出數據
        Serial.print("aX = "); Serial.print(ax);
        Serial.print(" | aY = "); Serial.print(ay);
        Serial.print(" | aZ = "); Serial.print(az);
        Serial.print(" | gX = "); Serial.print(gx);
        Serial.print(" | gY = "); Serial.print(gy);
        Serial.print(" | gZ = "); Serial.println(gz);
    }

    delay(1000);
}
