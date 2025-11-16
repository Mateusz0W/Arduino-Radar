#pragma once
#include "Sensor.hpp"

class UltrasonicSensor: public Sensor{
    private:
        const uint8_t _trigPin, _echoPin;
        const uint32_t _maxDistanceCm;
    public:
        UltrasonicSensor(uint8_t trigPin, uint8_t echoPin, uint16_t maxDistanceCm): _trigPin(trigPin), _echoPin(echoPin), _maxDistanceCm(maxDistanceCm){}
        uint16_t measureCm() override;
        void init() override;
};

