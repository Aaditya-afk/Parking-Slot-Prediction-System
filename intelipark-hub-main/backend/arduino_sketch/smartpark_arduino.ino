/*
  SmartPark Arduino Sketch
  IoT-based Parking Management System
  
  Hardware Setup:
  - Arduino UNO
  - 6x IR sensors (pins 2-7)
  - 1x Servo motor (pin 9)
  - USB connection to PC for serial communication
  
  Functionality:
  - Monitors IR sensors for parking slot occupancy
  - Controls servo motor as barrier gate
  - Sends sensor data to PC via serial
  - Receives servo commands from PC via serial
*/

#include <Servo.h>

// Pin definitions
const int IR_PINS[] = {2, 3, 4, 5, 6, 7};  // IR sensor pins
const int SERVO_PIN = 9;                    // Servo motor pin
const int LED_PIN = 13;                     // Built-in LED for status
const int NUM_SLOTS = 6;                    // Number of parking slots

// Servo motor
Servo gateServo;
const int SERVO_OPEN_ANGLE = 90;   // Gate open position
const int SERVO_CLOSE_ANGLE = 0;   // Gate closed position
bool gateOpen = false;

// Sensor state tracking
bool slotStates[NUM_SLOTS];        // Current slot states (true = occupied)
bool lastSlotStates[NUM_SLOTS];    // Previous slot states
unsigned long lastSensorRead = 0;   // Last sensor reading time
unsigned long lastHeartbeat = 0;    // Last heartbeat time

// Timing constants
const unsigned long SENSOR_INTERVAL = 500;    // Read sensors every 500ms
const unsigned long HEARTBEAT_INTERVAL = 5000; // Heartbeat every 5 seconds
const unsigned long DEBOUNCE_DELAY = 100;     // Debounce delay for sensors

// Serial communication
String inputString = "";
bool stringComplete = false;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  Serial.println("SmartPark Arduino System Starting...");
  
  // Initialize IR sensor pins
  for (int i = 0; i < NUM_SLOTS; i++) {
    pinMode(IR_PINS[i], INPUT);
    slotStates[i] = false;
    lastSlotStates[i] = false;
  }
  
  // Initialize LED pin
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Initialize servo
  gateServo.attach(SERVO_PIN);
  gateServo.write(SERVO_CLOSE_ANGLE);
  gateOpen = false;
  
  // Reserve string space for serial input
  inputString.reserve(50);
  
  Serial.println("System initialized successfully");
  Serial.println("Monitoring parking slots...");
  
  // Initial sensor reading
  readSensors();
  sendInitialStatus();
}

void loop() {
  unsigned long currentTime = millis();
  
  // Read sensors at regular intervals
  if (currentTime - lastSensorRead >= SENSOR_INTERVAL) {
    readSensors();
    checkForChanges();
    lastSensorRead = currentTime;
  }
  
  // Send heartbeat
  if (currentTime - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = currentTime;
  }
  
  // Process serial commands
  if (stringComplete) {
    processSerialCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
  
  // Blink LED to show system is alive
  digitalWrite(LED_PIN, (currentTime / 1000) % 2);
}

void readSensors() {
  // Store previous states
  for (int i = 0; i < NUM_SLOTS; i++) {
    lastSlotStates[i] = slotStates[i];
  }
  
  // Read current sensor states
  for (int i = 0; i < NUM_SLOTS; i++) {
    // IR sensor returns LOW when object detected (occupied)
    // We invert this so true = occupied, false = free
    bool sensorReading = !digitalRead(IR_PINS[i]);
    
    // Simple debouncing - only update if reading is stable
    delay(DEBOUNCE_DELAY);
    bool confirmedReading = !digitalRead(IR_PINS[i]);
    
    if (sensorReading == confirmedReading) {
      slotStates[i] = sensorReading;
    }
  }
}

void checkForChanges() {
  // Check each slot for state changes
  for (int i = 0; i < NUM_SLOTS; i++) {
    if (slotStates[i] != lastSlotStates[i]) {
      // State changed, send update
      sendSlotUpdate(i + 1, slotStates[i]);
    }
  }
}

void sendSlotUpdate(int slotNumber, bool occupied) {
  String status = occupied ? "OCCUPIED" : "FREE";
  Serial.println("SLOT_" + String(slotNumber) + ": " + status);
}

void sendInitialStatus() {
  Serial.println("=== Initial Slot Status ===");
  for (int i = 0; i < NUM_SLOTS; i++) {
    sendSlotUpdate(i + 1, slotStates[i]);
  }
  Serial.println("=== End Initial Status ===");
}

void sendHeartbeat() {
  Serial.println("HEARTBEAT: " + String(millis()));
}

void processSerialCommand(String command) {
  command.trim();
  command.toUpperCase();
  
  if (command == "SERVO_OPEN") {
    openGate();
  }
  else if (command == "SERVO_CLOSE") {
    closeGate();
  }
  else if (command == "STATUS") {
    sendSystemStatus();
  }
  else if (command == "RESET") {
    resetSystem();
  }
  else if (command.startsWith("PING")) {
    Serial.println("PONG");
  }
  else {
    Serial.println("ERROR: Unknown command - " + command);
  }
}

void openGate() {
  if (!gateOpen) {
    Serial.println("SERVO: Opening gate...");
    gateServo.write(SERVO_OPEN_ANGLE);
    gateOpen = true;
    Serial.println("SERVO: Gate opened");
  } else {
    Serial.println("SERVO: Gate already open");
  }
}

void closeGate() {
  if (gateOpen) {
    Serial.println("SERVO: Closing gate...");
    gateServo.write(SERVO_CLOSE_ANGLE);
    gateOpen = false;
    Serial.println("SERVO: Gate closed");
  } else {
    Serial.println("SERVO: Gate already closed");
  }
}

void sendSystemStatus() {
  Serial.println("=== System Status ===");
  Serial.println("Uptime: " + String(millis() / 1000) + " seconds");
  Serial.println("Gate Status: " + String(gateOpen ? "OPEN" : "CLOSED"));
  Serial.println("Slots Status:");
  
  for (int i = 0; i < NUM_SLOTS; i++) {
    String status = slotStates[i] ? "OCCUPIED" : "FREE";
    Serial.println("  SLOT_" + String(i + 1) + ": " + status);
  }
  
  Serial.println("=== End Status ===");
}

void resetSystem() {
  Serial.println("SYSTEM: Resetting...");
  
  // Close gate
  gateServo.write(SERVO_CLOSE_ANGLE);
  gateOpen = false;
  
  // Clear states
  for (int i = 0; i < NUM_SLOTS; i++) {
    slotStates[i] = false;
    lastSlotStates[i] = false;
  }
  
  // Re-read sensors
  delay(500);
  readSensors();
  sendInitialStatus();
  
  Serial.println("SYSTEM: Reset complete");
}

// Serial event handler
void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    
    if (inChar == '\n') {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}

// Utility function to test all components
void runDiagnostics() {
  Serial.println("=== Running Diagnostics ===");
  
  // Test servo
  Serial.println("Testing servo motor...");
  gateServo.write(SERVO_OPEN_ANGLE);
  delay(1000);
  gateServo.write(SERVO_CLOSE_ANGLE);
  delay(1000);
  Serial.println("Servo test complete");
  
  // Test sensors
  Serial.println("Testing IR sensors...");
  for (int i = 0; i < NUM_SLOTS; i++) {
    bool reading = digitalRead(IR_PINS[i]);
    Serial.println("Sensor " + String(i + 1) + " (Pin " + String(IR_PINS[i]) + "): " + 
                   String(reading ? "HIGH" : "LOW"));
  }
  
  // Test LED
  Serial.println("Testing LED...");
  for (int i = 0; i < 5; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
  
  Serial.println("=== Diagnostics Complete ===");
}

/*
  Wiring Instructions:
  
  IR Sensors:
  - SLOT_1 IR Sensor: VCC -> 5V, GND -> GND, OUT -> Pin 2
  - SLOT_2 IR Sensor: VCC -> 5V, GND -> GND, OUT -> Pin 3
  - SLOT_3 IR Sensor: VCC -> 5V, GND -> GND, OUT -> Pin 4
  - SLOT_4 IR Sensor: VCC -> 5V, GND -> GND, OUT -> Pin 5
  - SLOT_5 IR Sensor: VCC -> 5V, GND -> GND, OUT -> Pin 6
  - SLOT_6 IR Sensor: VCC -> 5V, GND -> GND, OUT -> Pin 7
  
  Servo Motor:
  - Red wire (VCC) -> 5V
  - Brown/Black wire (GND) -> GND  
  - Orange/Yellow wire (Signal) -> Pin 9
  
  USB Connection:
  - Connect Arduino to PC via USB cable
  - Note the COM port (e.g., COM3) for backend configuration
  
  Serial Commands from PC:
  - SERVO_OPEN: Opens the barrier gate
  - SERVO_CLOSE: Closes the barrier gate
  - STATUS: Returns system status
  - RESET: Resets the system
  - PING: Returns PONG (connectivity test)
  
  Serial Output to PC:
  - SLOT_X: OCCUPIED/FREE (when slot state changes)
  - HEARTBEAT: timestamp (every 5 seconds)
  - SERVO: status messages
  - ERROR: error messages
*/
