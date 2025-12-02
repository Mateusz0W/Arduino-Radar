#pragma once

#include "StepperMotor.hpp"
#include "Sensor.hpp"
#include <ArduinoJson.h>

class Radar{
    private:
        StepperMotor &_motor;
        Sensor &_sensor;
        int _sampleCount;
        int _recivedResolution;
        float _recivedAngle;
        int _measureTime;
        float _maxAngle;
        int _resolution;

    public:
        Radar(StepperMotor &motor, Sensor &sensor, float maxAngle = 180.0f, int resolution = 0): _motor(motor), _sensor(sensor), _maxAngle(maxAngle), _resolution(resolution){
        if (resolution > 0)
            _sampleCount = resolution + 1;
        else
            _sampleCount = static_cast<int>(180.0f / motor.getStepAngle()) + 1;
        }
        void init(const float maxSpeed, const float acceleration);
        void scanSweep(bool forward);
        void emitPoint(float angle, uint16_t distance) const;
        bool reciveData();
        void changeParameters();
        void setMaxAngle(float angel);
        void setResolution(int resolution);
};