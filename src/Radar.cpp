#include "Radar.hpp"

void Radar::init(const float maxSpeed, const float acceleration){
    _motor.init(maxSpeed, acceleration);
    _sensor.init();
}

void Radar::scanSweep(bool forward){
    float stepAngle = _motor.getStepAngle();
    for (int i = 0; i < _sampleCount; ++i) {
        const int idx = forward ? i : (_sampleCount - 1 - i);
        _motor.moveStepperToSample(idx);
        float angle = idx * stepAngle;
        uint16_t dist = _sensor.measureCm();
        emitPoint(angle, dist);
        delay(30);
    }
    Serial.println("END");
}

void Radar::emitPoint(float angle, uint16_t distance) const{
    Serial.print(angle, 1);
    Serial.print(',');
    Serial.println(distance);
}
