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
        unsigned long startTime = millis();
        unsigned long elapsed = startTime;
        while (elapsed - startTime > _measureTime)
        {
            uint16_t dist = _sensor.measureCm();
            emitPoint(angle, dist);
            elapsed = millis();
        }
        delay(30);
    }
    Serial.println("END");
}

void Radar::emitPoint(float angle, uint16_t distance) const{
    Serial.print(angle, 1);
    Serial.print(',');
    Serial.println(distance);
}

bool Radar::reciveData(){
    if (!Serial.available())
        return false;

    String recivedString = Serial.readStringUntil('\n');
    
    if (recivedString.length() == 0)
        return false;

    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, recivedString);

    if (!error){
        _recivedInfo = doc["Command"].as<String>();
        _recivedValue = doc["Value"].as<int>(); 
    }

    return true;
}

void Radar::changeParameters(){
    if(reciveData()){
        if(_recivedInfo == "Resolution")      
            _motor.changeResolution(_recivedValue);
        else if (_recivedInfo == "Time")
            _measureTime = _recivedValue;
    }
}