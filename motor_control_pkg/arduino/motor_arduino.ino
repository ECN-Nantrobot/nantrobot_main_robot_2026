
void setup() {
  Serial.begin(115200); // Match this speed in your Python node
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  if (Serial.available() > 0) {
    // Read the incoming string from ROS2
    String data = Serial.readStringUntil('\n');
    
    // Blink the LED to show data was received
    digitalWrite(LED_BUILTIN, HIGH);
    delay(50);
    digitalWrite(LED_BUILTIN, LOW);

    // Echo back to ROS2 for debugging
    Serial.print("Arduino received: ");
    Serial.println(data);
  }
}