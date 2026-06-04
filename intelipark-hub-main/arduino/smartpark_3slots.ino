/*
 * SmartPark Arduino Firmware - 3 Slots System
 * 
 * Hardware Setup:
 * - Arduino UNO
 * - 3x IR Sensors (Pins 2, 3, 4) for Slots 1, 2, 3
 * - 1x Servo Motor (Pin 9) for gate control
 * - USB connection to PC for serial communication
 * 
 * Communication Protocol:
 * - Sends JSON slot status every second: {"slot1":0,"slot2":1,"slot3":0}
 * - Receives commands: SERVO_OPEN, SERVO_CLOSE
 * - Responds with: OK, ERROR, or status updates
 * 
 * Author: SmartPark System
 * Version: 1.0 - Production Ready
 */

#include <Servo.h>
#include <ArduinoJson.h>

// ==================== CONFIGURATION ====================
// Hardware Pins
#define IR_SLOT1_PIN 2
#define IR_SLOT2_PIN 3
#define IR_SLOT3_PIN 4
#define SERVO_PIN 9

// Servo Configuration
#define SERVO_CLOSED_ANGLE 0
#define SERVO_OPEN_ANGLE 90
#define SERVO_STEP_SIZE 2
#define SERVO_STEP_DELAY 20
#define SERVO_TIMEOUT 5000

// Timing Configuration
#define SLOT_READ_INTERVAL 1000    // Send slot data every 1 second
#define HEARTBEAT_INTERVAL 30000   // Send heartbeat every 30 seconds
#define DEBOUNCE_DELAY 100         // Sensor debounce time

// ==================== GLOBAL VARIABLES ====================
Servo gateServo;

// Slot Management
struct SlotData {
  int pin;
  bool currentState;
  bool lastState;
  unsigned long lastChangeTime;
  String label;
};

SlotData slots[3] = {
  {IR_SLOT1_PIN, false, false, 0, "slot1"},
  {IR_SLOT2_PIN, false, false, 0, "slot2"},
  {IR_SLOT3_PIN, false, false, 0, "slot3"}
};

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
  bool isMoving;
} servoCtrl;

// Timing Variables
unsigned long lastSlotSend = 0;
unsigned long lastHeartbeat = 0;

// Serial Communication
String serialBuffer = "";
DynamicJsonDocument slotDoc(200);
DynamicJsonDocument responseDoc(200);

// ==================== SETUP FUNCTION ====================
void setup() {
  // Initialize Serial Communication
  Serial.begin(9600);
  Serial.setTimeout(100);
  
  // Initialize IR Sensors
  for (int i = 0; i < 3; i++) {
    pinMode(slots[i].pin, INPUT_PULLUP);
    slots[i].currentState = false;
    slots[i].lastState = false;
    slots[i].lastChangeTime = millis();
  }
  
  // Initialize Servo
  gateServo.attach(SERVO_PIN);
  initializeServo();
  
  // Startup Message
  Serial.println("{\"status\":\"SYSTEM_READY\",\"slots\":3,\"servo\":\"ATTACHED\"}");
  
  // Initial slot reading
  readAllSlots();
  sendSlotData();
}

// ==================== MAIN LOOP ====================
void loop() {
  // Handle incoming serial commands
  handleSerialCommunication();
  
  // Update servo movement (non-blocking)
  updateServoMovement();
  
  // Read and send slot data periodically
  if (millis() - lastSlotSend >= SLOT_READ_INTERVAL) {
    readAllSlots();
    if (hasSlotChanged()) {
      sendSlotData();
    }
    lastSlotSend = millis();
  }
  
  // Send heartbeat periodically
  if (millis() - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = millis();
  }
  
  // Small delay to prevent overwhelming the loop
  delay(10);
}

// ==================== SLOT MANAGEMENT ====================
void readAllSlots() {
  for (int i = 0; i < 3; i++) {
    // Read sensor (LOW = occupied, HIGH = free for most IR sensors)
    bool sensorReading = (digitalRead(slots[i].pin) == LOW);
    
    // Debounce logic
    if (sensorReading != slots[i].currentState) {
      if (millis() - slots[i].lastChangeTime > DEBOUNCE_DELAY) {
        slots[i].lastState = slots[i].currentState;
        slots[i].currentState = sensorReading;
        slots[i].lastChangeTime = millis();
      }
    }
  }
}

bool hasSlotChanged() {
  for (int i = 0; i < 3; i++) {
    if (slots[i].currentState != slots[i].lastState) {
      return true;
    }
  }
  return false;
}

void sendSlotData() {
  // Clear previous data
  slotDoc.clear();
  
  // Add slot states (1 = occupied, 0 = free)
  slotDoc["slot1"] = slots[0].currentState ? 1 : 0;
  slotDoc["slot2"] = slots[1].currentState ? 1 : 0;
  slotDoc["slot3"] = slots[2].currentState ? 1 : 0;
  
  // Add timestamp and metadata
  slotDoc["timestamp"] = millis();
  slotDoc["type"] = "slot_update";
  
  // Send JSON data
  serializeJson(slotDoc, Serial);
  Serial.println(); // Add newline for parsing
  
  // Update last states
  for (int i = 0; i < 3; i++) {
    slots[i].lastState = slots[i].currentState;
  }
}

void sendHeartbeat() {
  responseDoc.clear();
  responseDoc["type"] = "heartbeat";
  responseDoc["uptime"] = millis();
  responseDoc["servo_angle"] = servoCtrl.currentAngle;
  responseDoc["servo_state"] = getServoStateString();
  
  serializeJson(responseDoc, Serial);
  Serial.println();
}

// ==================== SERVO CONTROL ====================
void initializeServo() {
  servoCtrl.state = SERVO_IDLE;
  servoCtrl.currentAngle = SERVO_CLOSED_ANGLE;
  servoCtrl.targetAngle = SERVO_CLOSED_ANGLE;
  servoCtrl.lastStepTime = 0;
  servoCtrl.movementStartTime = 0;
  servoCtrl.isMoving = false;
  
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
  
  // Check for timeout
  if (currentTime - servoCtrl.movementStartTime > SERVO_TIMEOUT) {
    handleServoError("TIMEOUT");
    return;
  }
  
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

void handleServoError(String error) {
  servoCtrl.isMoving = false;
  servoCtrl.state = SERVO_IDLE;
  
  sendServoResponse("ERROR", servoCtrl.currentAngle, error);
  
  // Attempt recovery
  gateServo.write(servoCtrl.currentAngle);
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

String getServoStateString() {
  switch (servoCtrl.state) {
    case SERVO_IDLE: return "IDLE";
    case SERVO_OPENING: return "OPENING";
    case SERVO_CLOSING: return "CLOSING";
    default: return "UNKNOWN";
  }
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
  }
  else if (command == "SERVO_CLOSE") {
    startServoMovement(SERVO_CLOSED_ANGLE, SERVO_CLOSING);
  }
  else if (command == "GET_STATUS") {
    sendSystemStatus();
  }
  else if (command == "GET_SLOTS") {
    sendSlotData();
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
  
  // Add slot states
  JsonObject slotsObj = responseDoc.createNestedObject("slots");
  slotsObj["slot1"] = slots[0].currentState ? 1 : 0;
  slotsObj["slot2"] = slots[1].currentState ? 1 : 0;
  slotsObj["slot3"] = slots[2].currentState ? 1 : 0;
  
  // Add occupancy summary
  int occupiedCount = 0;
  for (int i = 0; i < 3; i++) {
    if (slots[i].currentState) occupiedCount++;
  }
  responseDoc["occupied_slots"] = occupiedCount;
  responseDoc["free_slots"] = 3 - occupiedCount;
  
  serializeJson(responseDoc, Serial);
  Serial.println();
}

void resetServo() {
  // Stop current movement
  servoCtrl.isMoving = false;
  servoCtrl.state = SERVO_IDLE;
  
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
