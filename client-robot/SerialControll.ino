#include <Servo.h>

Servo servo1;
Servo servo2;

String inputBuffer = "";

const int defaultAngle = 70;

void setup() {
  Serial.begin(9600);
  servo1.attach(9);
  servo2.attach(3);
  servo1.write(defaultAngle);
  servo2.write(180 - defaultAngle);
  Serial.println("Arduino Ready");
}

void loop() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      processCommand(inputBuffer);
      inputBuffer = ""; // Clear buffer
    } else {
      inputBuffer += inChar;
    }
  }
}

void processCommand(String input) {
  input.trim();

  if (input.startsWith("S:")) {
    input = input.substring(2); // Remove 'S:'
    int commaIndex = input.indexOf(',');

    if (commaIndex != -1) {
      String angle1Str = input.substring(0, commaIndex);
      String angle2Str = input.substring(commaIndex + 1);

      int angle1 = constrain(angle1Str.toInt(), 0, 180);
      int angle2 = constrain(angle2Str.toInt(), 0, 180);

      servo1.write(angle1);
      servo2.write(180 - angle2); // invert if needed

      Serial.println("Servos set to: " + String(angle1) + " / " + String(angle2));
    } else {
      Serial.println("Invalid format. Use: S:angle1,angle2");
    }
  } else {
    Serial.println("Unknown command: " + input);
  }
}
