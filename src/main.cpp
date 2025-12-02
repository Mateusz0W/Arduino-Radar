#include "Radar.hpp"
#include "UltrasonicSensor.hpp"

UltrasonicSensor sensor(2, 3, 400);
StepperMotor motor(8, 9, 10, 11, 2048, 2);
Radar radar(motor, sensor);

void setup(){
    Serial.begin(115200);
    radar.init(600, 300);
}

void loop(){
    radar.scanSweep(true);
    radar.changeParameters();
}
