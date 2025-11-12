#include <Arduino.h> 

int Trig = 2; 
int Echo = 3; 
int CM; 
long TIME; 

void setup() 
{ 
  Serial.begin(9600); 
  pinMode(Trig, OUTPUT); 
  pinMode(Echo, INPUT); 

  Serial.println("Test of spacing"); 
} 

void loop() 
{ 
  pomiar_odleglosci(); 
  Serial.print("Distance: "); 
  Serial.print(CM); 
  Serial.println(" cm"); 
  delay(200); 
} 

void pomiar_odleglosci () 
{ 
  digitalWrite(Trig, LOW); 
  delayMicroseconds(2); 
  digitalWrite(Trig, HIGH); 
  delayMicroseconds(10); 
  digitalWrite(Trig, LOW); 
  digitalWrite(Echo, HIGH); 
  TIME = pulseIn(Echo, HIGH); 
  CM = TIME / 58; 
} 