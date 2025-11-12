#include <Arduino.h>
#include <AccelStepper.h>

constexpr uint8_t trigPin = 2;
constexpr uint8_t echoPin = 3;
constexpr uint8_t IN1 = 8;
constexpr uint8_t IN2 = 9;
constexpr uint8_t IN3 = 10;
constexpr uint8_t IN4 = 11;

constexpr float stepAngle = 2.0f;                 // degrees per sample
constexpr uint16_t stepsPerRev = 2048;            // 28BYJ-48 default with gearbox
constexpr uint16_t stepsPerSample = stepsPerRev * (stepAngle / 360.0f);
constexpr uint16_t maxDistanceCm = 400;           // ~4 m range of HC-SR04

AccelStepper stepper(AccelStepper::HALF4WIRE, IN1, IN3, IN2, IN4);

struct Sample {
  float angle;
  uint16_t distance;
};

constexpr int sampleCount = static_cast<int>(180.0f / stepAngle) + 1;
Sample scanBuffer[sampleCount];

uint16_t measureCm() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  long duration = pulseIn(echoPin, HIGH, maxDistanceCm * 58UL * 2);  // timeout for ~max distance
  return duration > 0 ? static_cast<uint16_t>(duration / 58UL) : 0;
}

void moveStepperToSample(int index) {
  stepper.moveTo(index * stepsPerSample);
  while (stepper.distanceToGo() != 0) {
    stepper.run();
  }
}

void scanSweep(bool forward) {
  for (int i = 0; i < sampleCount; ++i) {
    const int idx = forward ? i : (sampleCount - 1 - i);
    moveStepperToSample(idx);
    scanBuffer[i] = {idx * stepAngle, measureCm()};
    delay(30);  // allow sensor to settle before next measurement
  }
}

void emitScan() {
  for (int i = 0; i < sampleCount; ++i) {
    Serial.print(scanBuffer[i].angle, 1);
    Serial.print(',');
    Serial.println(scanBuffer[i].distance);
  }
  Serial.println("END");
}

void setup() {
  Serial.begin(115200);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  stepper.setMaxSpeed(600);
  stepper.setAcceleration(300);
}

void loop() {
  scanSweep(true);
  scanSweep(false);
  emitScan();
}
