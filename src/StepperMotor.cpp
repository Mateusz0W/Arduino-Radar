#include "StepperMotor.hpp"

void StepperMotor::init(const float maxSpeed,const float acceleration){
    _stepper.setMaxSpeed(maxSpeed);
    _stepper.setAcceleration(acceleration);
    _stepper.setCurrentPosition(0);
}

float StepperMotor::getStepAngle() const{
    return _stepAngle;
}

void StepperMotor::changeResolution(uint16_t resolution){
    _stepsPerSample = resolution * (_stepAngle / 360.0f);
}

void StepperMotor::moveToAngle(float angle){
    long target = (angle / 360.0f) * _stepsPerRev;
    // _stepper.moveTo(target);
    // while (_stepper.distanceToGo() != 0)
    //     _stepper.run();s
    _stepper.runToNewPosition(target);
}

