#include "StepperMotor.hpp"

void StepperMotor::init(const float maxSpeed,const float acceleration){
    _stepper.setMaxSpeed(maxSpeed);
    _stepper.setAcceleration(acceleration);
    _stepper.setCurrentPosition(0);
}

void StepperMotor::moveStepperToSample(const int index){
    _stepper.moveTo(index * _stepsPerSample);
    while (_stepper.distanceToGo() != 0) 
        _stepper.run();
  
}

float StepperMotor::getStepAngle() const{
    return _stepAngle;
}

void StepperMotor::changeResolution(uint16_t resolution){
    _stepsPerSample = resolution * (_stepAngle / 360.0f);
}