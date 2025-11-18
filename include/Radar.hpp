#pragma once

#include "StepperMotor.hpp"
#include "Sensor.hpp"
#include <ArduinoJson.h>

class Radar{
    private:
        StepperMotor &_motor;
        Sensor &_sensor;
        int _sampleCount;
        String _recivedInfo;
        float _recivedValue;
        int _measureTime;

    public:
        Radar(StepperMotor &motor, Sensor &sensor): _motor(motor), _sensor(sensor), _recivedInfo(""){
            _sampleCount = static_cast<int>(180.0f / motor.getStepAngle()) + 1;
        }
        void init(const float maxSpeed, const float acceleration);
        void scanSweep(bool forward);
        void emitPoint(float angle, uint16_t distance) const;
        bool reciveData();
        void changeParameters();
};