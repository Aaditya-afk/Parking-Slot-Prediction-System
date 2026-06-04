/*
 * SmartPark Arduino Firmware - Entry/Exit Detection System
 * 
 * Hardware Setup:
 * - Arduino UNO
 * - IR Sensor 1 (IR_ENTRY) → Pin 2 (detects cars entering)
 * - IR Sensor 2 (IR_EXIT) → Pin 3 (detects cars exiting)
 * - Servo Motor → Pin 9 (gate barrier control)
 * - USB connection to PC for serial communication
 * 
 * Communication Protocol:
 * - Sends JSON events: {"event":"car_entered"} or {"event":"car_exited"}
 * - Receives commands: SERVO_OPEN, SERVO_CLOSE
 * - Baud Rate: 9600
 * 
 * Author: SmartPark System
 * Version: 2.0 - Entry/Exit Detection
 */

#include <Servo.h>
#include <ArduinoJson.h>

// ==================== CONFIGURATION ====================
// Hardware Pins
#define IR_ENTRY_PIN 2        // IR sensor for entry detection
#define IR_EXIT_PIN 3         // IR sensor for exit detection
#define SERVO_PIN 9           // Servo motor for gate

// Servo Configuration
#define SERVO_CLOSED_ANGLE 10   // Gate closed position (slight offset to avoid binding)
#define SERVO_OPEN_ANGLE 110    // Gate open position (increase for full clearance)
#define SERVO_STEP_SIZE 2      // Degrees per step for smooth movement
#define SERVO_STEP_DELAY 20    // Milliseconds between steps

// Timing Configuration
#define DEBOUNCE_DELAY 100     // Debounce time for IR sensors (ms)
#define HOLD_ACTIVE_MS 80      // Minimum time sensor must stay active to confirm event (ms)
#define HEARTBEAT_INTERVAL 30000  // Send heartbeat every 30 seconds
#define GATE_AUTO_CLOSE_DELAY 5000  // Auto-close gate after 5 seconds

// ==================== GLOBAL VARIABLES ====================
Servo gateServo;

// Sensor State Management
struct SensorState {
  bool currentState;
  bool lastState;
  unsigned long lastChangeTime;
  bool eventTriggered;
};

SensorState entryState = {false, false, 0, false};
SensorState exitState = {false, false, 0, false};

// Servo Control
enum ServoState {
  SERVO_IDLE,
  SERVO_OPENING,
  SERVO_CLOSING
};

struct ServoController {
  ServoState state;
  int currentAngle;
  int targetAngle;
  unsigned long lastStepTime;
  unsigned long movementStartTime;
  unsigned long autoCloseTime;
  bool isMoving;
  bool autoCloseEnabled;
} servoCtrl;

// Timing Variables
unsigned long lastHeartbeat = 0;

// Serial Communication
String serialBuffer = "";
DynamicJsonDocument eventDoc(200);
DynamicJsonDocument responseDoc(200);

// ==================== SETUP FUNCTION ====================
void setup() {
  // Initialize Serial Communication
  Serial.begin(9600);
  Serial.setTimeout(100);
  
  // Initialize IR Sensors
  pinMode(IR_ENTRY_PIN, INPUT_PULLUP);
  pinMode(IR_EXIT_PIN, INPUT_PULLUP);
  
  // Initialize sensor states
  entryState.currentState = digitalRead(IR_ENTRY_PIN) == LOW;
  entryState.lastState = entryState.currentState;
  entryState.lastChangeTime = millis();
  entryState.eventTriggered = false;
  
  exitState.currentState = digitalRead(IR_EXIT_PIN) == LOW;
  exitState.lastState = exitState.currentState;
  exitState.lastChangeTime = millis();
  exitState.eventTriggered = false;
  
  // Initialize Servo
  gateServo.attach(SERVO_PIN);
  initializeServo();
  
  // Startup Message
  Serial.println("{\"status\":\"SYSTEM_READY\",\"sensors\":2,\"servo\":\"ATTACHED\",\"mode\":\"ENTRY_EXIT\"}");
  
  delay(1000); // Allow system to stabilize
}

// ==================== MAIN LOOP ====================
void loop() {
  // Handle incoming serial commands
  handleSerialCommunication();
  
  // Update servo movement (non-blocking)
  updateServoMovement();
  
  // Read and process IR sensors
  readSensors();
  processEntryEvents();
  processExitEvents();
  
  // Handle auto-close gate
  handleAutoClose();
  
  // Send heartbeat periodically
  if (millis() - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = millis();
  }
  
  // Small delay to prevent overwhelming the loop
  delay(10);
}

// ==================== SENSOR MANAGEMENT ====================
void readSensors() {
  unsigned long currentTime = millis();
  
  // Read entry sensor (LOW = object detected)
  bool entryReading = (digitalRead(IR_ENTRY_PIN) == LOW);
  if (entryReading != entryState.currentState) {
    if (currentTime - entryState.lastChangeTime > DEBOUNCE_DELAY) {
      entryState.lastState = entryState.currentState;
      entryState.currentState = entryReading;
      entryState.lastChangeTime = currentTime;
      entryState.eventTriggered = false; // Reset event flag
    }
  }
  
  // Read exit sensor (LOW = object detected)
  bool exitReading = (digitalRead(IR_EXIT_PIN) == LOW);
  if (exitReading != exitState.currentState) {
    if (currentTime - exitState.lastChangeTime > DEBOUNCE_DELAY) {
      exitState.lastState = exitState.currentState;
      exitState.currentState = exitReading;
      exitState.lastChangeTime = currentTime;
      exitState.eventTriggered = false; // Reset event flag
    }
  }
}

void processEntryEvents() {
  // Detect car entering (sensor goes from false to true)
  if (!entryState.lastState && entryState.currentState && !entryState.eventTriggered) {
    // Confirm the sensor remained active for a minimum hold duration
    if (millis() - entryState.lastChangeTime >= HOLD_ACTIVE_MS) {
      sendCarEvent("car_entered");
      entryState.eventTriggered = true;
      
      // Auto-open gate for entry
      if (servoCtrl.state == SERVO_IDLE && servoCtrl.currentAngle <= SERVO_CLOSED_ANGLE) {
        startServoMovement(SERVO_OPEN_ANGLE, SERVO_OPENING);
        servoCtrl.autoCloseEnabled = true;
        servoCtrl.autoCloseTime = millis() + GATE_AUTO_CLOSE_DELAY;
      }
    }
  }
}

void processExitEvents() {
  // Detect car exiting (sensor goes from false to true)
  if (!exitState.lastState && exitState.currentState && !exitState.eventTriggered) {
    // Confirm the sensor remained active for a minimum hold duration
    if (millis() - exitState.lastChangeTime >= HOLD_ACTIVE_MS) {
      sendCarEvent("car_exited");
      exitState.eventTriggered = true;
      
      // Auto-open gate for exit
      if (servoCtrl.state == SERVO_IDLE && servoCtrl.currentAngle <= SERVO_CLOSED_ANGLE) {
        startServoMovement(SERVO_OPEN_ANGLE, SERVO_OPENING);
        servoCtrl.autoCloseEnabled = true;
        servoCtrl.autoCloseTime = millis() + GATE_AUTO_CLOSE_DELAY;
      }
    }
  }
}

void sendCarEvent(String eventType) {
  eventDoc.clear();
  eventDoc["event"] = eventType;
  eventDoc["timestamp"] = millis();
  eventDoc["entry_sensor"] = entryState.currentState;
  eventDoc["exit_sensor"] = exitState.currentState;
  
  serializeJson(eventDoc, Serial);
  Serial.println(); // Add newline for parsing
  
  // Debug info
  Serial.print("{\"debug\":\"Event triggered: ");
  Serial.print(eventType);
  Serial.println("\"}");
}

// ==================== SERVO CONTROL ====================
void initializeServo() {
  servoCtrl.state = SERVO_IDLE;
  servoCtrl.currentAngle = SERVO_CLOSED_ANGLE;
  servoCtrl.targetAngle = SERVO_CLOSED_ANGLE;
  servoCtrl.lastStepTime = 0;
  servoCtrl.movementStartTime = 0;
  servoCtrl.autoCloseTime = 0;
  servoCtrl.isMoving = false;
  servoCtrl.autoCloseEnabled = false;
  
  // Set initial position
  gateServo.write(SERVO_CLOSED_ANGLE);
  delay(500); // Allow servo to reach position
}

void startServoMovement(int targetAngle, ServoState newState) {
  // Safety check: already at target
  if (abs(servoCtrl.currentAngle - targetAngle) <= SERVO_STEP_SIZE) {
    sendServoResponse("ALREADY_AT_TARGET", targetAngle);
    return;
  }
  
  // Safety check: already moving to target
  if (servoCtrl.isMoving && servoCtrl.targetAngle == targetAngle) {
    sendServoResponse("ALREADY_MOVING", targetAngle);
    return;
  }
  
  servoCtrl.state = newState;
  servoCtrl.targetAngle = targetAngle;
  servoCtrl.movementStartTime = millis();
  servoCtrl.lastStepTime = millis();
  servoCtrl.isMoving = true;
  
  String action = (newState == SERVO_OPENING) ? "OPENING" : "CLOSING";
  sendServoResponse("MOVEMENT_STARTED", targetAngle, action);
}

void updateServoMovement() {
  if (!servoCtrl.isMoving) return;
  
  unsigned long currentTime = millis();
  
  // Check if it's time for next step
  if (currentTime - servoCtrl.lastStepTime >= SERVO_STEP_DELAY) {
    moveServoOneStep();
    servoCtrl.lastStepTime = currentTime;
  }
}

void moveServoOneStep() {
  int difference = servoCtrl.targetAngle - servoCtrl.currentAngle;
  
  // Check if reached target
  if (abs(difference) <= SERVO_STEP_SIZE) {
    servoCtrl.currentAngle = servoCtrl.targetAngle;
    gateServo.write(servoCtrl.currentAngle);
    completeServoMovement();
    return;
  }
  
  // Move one step toward target
  if (difference > 0) {
    servoCtrl.currentAngle += SERVO_STEP_SIZE;
  } else {
    servoCtrl.currentAngle -= SERVO_STEP_SIZE;
  }
  
  // Constrain to valid range
  servoCtrl.currentAngle = constrain(servoCtrl.currentAngle, 0, 180);
  
  // Write to servo
  gateServo.write(servoCtrl.currentAngle);
}

void completeServoMovement() {
  servoCtrl.isMoving = false;
  servoCtrl.state = SERVO_IDLE;
  
  String position = (servoCtrl.currentAngle >= SERVO_OPEN_ANGLE) ? "OPEN" : "CLOSED";
  sendServoResponse("MOVEMENT_COMPLETE", servoCtrl.currentAngle, position);
}

void handleAutoClose() {
  if (servoCtrl.autoCloseEnabled && 
      servoCtrl.state == SERVO_IDLE && 
      servoCtrl.currentAngle >= SERVO_OPEN_ANGLE &&
      millis() >= servoCtrl.autoCloseTime) {
    
    // Auto-close the gate
    startServoMovement(SERVO_CLOSED_ANGLE, SERVO_CLOSING);
    servoCtrl.autoCloseEnabled = false;
    
    Serial.println("{\"info\":\"Auto-closing gate\"}");
  }
}

void sendServoResponse(String status, int angle, String extra = "") {
  responseDoc.clear();
  responseDoc["type"] = "servo_response";
  responseDoc["status"] = status;
  responseDoc["angle"] = angle;
  responseDoc["timestamp"] = millis();
  
  if (extra != "") {
    responseDoc["detail"] = extra;
  }
  
  serializeJson(responseDoc, Serial);
  Serial.println();
}

// ==================== SERIAL COMMUNICATION ====================
void handleSerialCommunication() {
  while (Serial.available() > 0) {
    char inChar = (char)Serial.read();
    
    if (inChar == '\n' || inChar == '\r') {
      if (serialBuffer.length() > 0) {
        processCommand(serialBuffer);
        serialBuffer = "";
      }
    } else {
      serialBuffer += inChar;
    }
  }
}

void processCommand(String command) {
  command.trim();
  command.toUpperCase();
  
  if (command == "SERVO_OPEN") {
    startServoMovement(SERVO_OPEN_ANGLE, SERVO_OPENING);
    servoCtrl.autoCloseEnabled = true;
    servoCtrl.autoCloseTime = millis() + GATE_AUTO_CLOSE_DELAY;
  }
  else if (command == "SERVO_CLOSE") {
    startServoMovement(SERVO_CLOSED_ANGLE, SERVO_CLOSING);
    servoCtrl.autoCloseEnabled = false;
  }
  else if (command == "GET_STATUS") {
    sendSystemStatus();
  }
  else if (command == "GET_SENSORS") {
    sendSensorStatus();
  }
  else if (command == "RESET_SERVO") {
    resetServo();
  }
  else if (command == "PING") {
    Serial.println("{\"type\":\"pong\",\"timestamp\":" + String(millis()) + "}");
  }
  else {
    responseDoc.clear();
    responseDoc["type"] = "error";
    responseDoc["message"] = "UNKNOWN_COMMAND";
    responseDoc["received"] = command;
    serializeJson(responseDoc, Serial);
    Serial.println();
  }
}

void sendSystemStatus() {
  responseDoc.clear();
  responseDoc["type"] = "system_status";
  responseDoc["uptime"] = millis();
  responseDoc["servo_angle"] = servoCtrl.currentAngle;
  responseDoc["servo_state"] = getServoStateString();
  responseDoc["servo_moving"] = servoCtrl.isMoving;
  responseDoc["auto_close_enabled"] = servoCtrl.autoCloseEnabled;
  
  // Add sensor states
  JsonObject sensorsObj = responseDoc.createNestedObject("sensors");
  sensorsObj["entry_detected"] = entryState.currentState;
  sensorsObj["exit_detected"] = exitState.currentState;
  sensorsObj["entry_last_change"] = entryState.lastChangeTime;
  sensorsObj["exit_last_change"] = exitState.lastChangeTime;
  
  serializeJson(responseDoc, Serial);
  Serial.println();
}

void sendSensorStatus() {
  responseDoc.clear();
  responseDoc["type"] = "sensor_status";
  responseDoc["entry_sensor"] = entryState.currentState;
  responseDoc["exit_sensor"] = exitState.currentState;
  responseDoc["entry_last_change"] = entryState.lastChangeTime;
  responseDoc["exit_last_change"] = exitState.lastChangeTime;
  responseDoc["timestamp"] = millis();
  
  serializeJson(responseDoc, Serial);
  Serial.println();
}

void sendHeartbeat() {
  responseDoc.clear();
  responseDoc["type"] = "heartbeat";
  responseDoc["uptime"] = millis();
  responseDoc["servo_angle"] = servoCtrl.currentAngle;
  responseDoc["servo_state"] = getServoStateString();
  responseDoc["entry_sensor"] = entryState.currentState;
  responseDoc["exit_sensor"] = exitState.currentState;
  
  serializeJson(responseDoc, Serial);
  Serial.println();
}

String getServoStateString() {
  switch (servoCtrl.state) {
    case SERVO_IDLE: return "IDLE";
    case SERVO_OPENING: return "OPENING";
    case SERVO_CLOSING: return "CLOSING";
    default: return "UNKNOWN";
  }
}

void resetServo() {
  // Stop current movement
  servoCtrl.isMoving = false;
  servoCtrl.state = SERVO_IDLE;
  servoCtrl.autoCloseEnabled = false;
  
  // Detach and reattach
  gateServo.detach();
  delay(100);
  gateServo.attach(SERVO_PIN);
  
  // Reset to closed position
  servoCtrl.currentAngle = SERVO_CLOSED_ANGLE;
  servoCtrl.targetAngle = SERVO_CLOSED_ANGLE;
  gateServo.write(SERVO_CLOSED_ANGLE);
  
  sendServoResponse("RESET_COMPLETE", SERVO_CLOSED_ANGLE);
}
