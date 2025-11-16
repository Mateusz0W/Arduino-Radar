#pragma once

#include <Arduino.h>
#include <AccelStepper.h>

class StepperMotor{
    private:
        AccelStepper _stepper;
        const float _stepAngle;
        uint16_t _stepsPerSample;

    public:
        StepperMotor(uint8_t IN1, uint8_t IN2, uint8_t IN3, uint8_t IN4, uint16_t stepsPerRev, float stepAngle):_stepper(AccelStepper::HALF4WIRE, IN1, IN3, IN2, IN4), _stepAngle(stepAngle)
        {
            _stepsPerSample = stepsPerRev * (stepAngle / 360.0f);
        }
        void init(const float maxSpeed, const float acceleration);
        void moveStepperToSample(const int index);
        float getStepAngle() const;;

};