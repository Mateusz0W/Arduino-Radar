#include "UltrasonicSensor.hpp"

void UltrasonicSensor::init(){
    pinMode(_trigPin, OUTPUT);
    pinMode(_echoPin, INPUT);
}

uint16_t UltrasonicSensor::measureCm(){
    digitalWrite(_trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(_trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(_trigPin, LOW);
    long duration = pulseIn(_echoPin, HIGH, _maxDistanceCm * 58UL * 2);  // timeout for ~max distance
    return duration > 0 ? static_cast<uint16_t>(duration / 58UL) : 0;
}