#include "Radar.hpp"

void Radar::init(const float maxSpeed, const float acceleration){
    _motor.init(maxSpeed, acceleration);
    _sensor.init();
}

void Radar::scanSweep(bool forward){
    float stepAngle = _motor.getStepAngle();
    for (int i = 0; i < _sampleCount; ++i) {
        const int idx = forward ? i : (_sampleCount - 1 - i);
        float angle = (float(idx) / (_sampleCount - 1)) * _maxAngle;
        _motor.moveToAngle(angle);
        delay(50);
        uint16_t dist = _sensor.measureCm();
        emitPoint(angle, dist);
        delay(30);
    }
    Serial.println("END");
}

void Radar::emitPoint(float angle, uint16_t distance) const{
    JsonDocument doc;
    doc["angle"] = angle;
    doc["distance"] = distance;

    serializeJson(doc, Serial);
    Serial.println();
}

bool Radar::receiveData(){
    if (!Serial.available())
        return false;

    String receivedString = Serial.readStringUntil('\n');
    
    if (receivedString.length() == 0)
        return false;

    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, receivedString);

    if (!error){
        _receivedAngle = doc["Angle"].as<float>();
        _receivedResolution = doc["Resolution"].as<int>(); 
    }

    return true;
}

void Radar::changeParameters(){
    if(receiveData()){
        setResolution(_receivedResolution);
        setMaxAngle(_receivedAngle);
    }
}

void Radar::setMaxAngle(float angle) {
    _maxAngle = angle;
    _sampleCount = static_cast<int>(_maxAngle / _motor.getStepAngle()) + 1;
}

void Radar::setResolution(int resolution) {
    _resolution = resolution;
    _sampleCount = resolution + 1;
}
