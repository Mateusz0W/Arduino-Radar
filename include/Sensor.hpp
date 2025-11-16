#pragma once

#include <Arduino.h>

class Sensor{
    public:
        virtual void init() = 0;
        virtual uint16_t measureCm() = 0;
};