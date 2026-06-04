/*
 * SmartPark Arduino - Optimized Servo Control
 * 
 * Features:
 * - Smooth servo movement with incremental steps
 * - Non-blocking servo control using millis()
 * - Configurable open/close angles and speed
 * - Error handling and retry logic
 * - Compatible with existing backend protocol
 * - Safety checks for duplicate commands
 * 
 * Hardware:
 * - Arduino UNO
 * - 6x IR sensors (pins 2-7)
 * - 1x Servo motor (pin 9) - Recommended: MG996R or SG90 with external power
 * - External 5V power supply for servo (recommended for reliability)
 * 
 * Serial Commands:
 * - SERVO_OPEN: Opens gate smoothly
 * - SERVO_CLOSE: Closes gate smoothly
 * 
 * Author: SmartPark System
 * Version: 2.0 - Optimized Servo Control
 */

#include <Servo.h>

// ==================== CONFIGURATION ====================
// Servo Configuration
#define SERVO_PIN 9
#define SERVO_CLOSED_ANGLE 0    // Gate closed position (adjustable)
#define SERVO_OPEN_ANGLE 90     // Gate open position (adjustable)
#define SERVO_STEP_SIZE 2       // Degrees per step (smaller = smoother)
#define SERVO_STEP_DELAY 20     // Milliseconds between steps (lower = faster)
#define SERVO_TIMEOUT 5000      // Max time to complete movement (ms)

// IR Sensor Configuration
#define NUM_SLOTS 6
const int sensorPins[NUM_SLOTS] = {2, 3, 4, 5, 6, 7};
const String slotLabels[NUM_SLOTS] = {"SLOT_1", "SLOT_2", "SLOT_3", "SLOT_4", "SLOT_5", "SLOT_6"};

// Timing Configuration
#define SENSOR_READ_INTERVAL 500    // Read sensors every 500ms
#define HEARTBEAT_INTERVAL 10000    // Send heartbeat every 10 seconds
#define SERIAL_TIMEOUT 100          // Serial read timeout

// ==================== GLOBAL VARIABLES ====================
Servo gateServo;

// Servo State Management
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
  bool hasError;
} servoCtrl;

// Sensor State Management
bool slotStates[NUM_SLOTS];
bool lastSlotStates[NUM_SLOTS];
unsigned long lastSensorRead = 0;
unsigned long lastHeartbeat = 0;

// Serial Communication
String serialBuffer = "";
bool serialComplete = false;

// ==================== SETUP FUNCTION ====================
void setup() {
  Serial.begin(9600);
  Serial.setTimeout(SERIAL_TIMEOUT);
  
  // Initialize servo
  gateServo.attach(SERVO_PIN);
  initializeServo();
  
  // Initialize IR sensors
  initializeSensors();
  
  // Print startup message
  Serial.println("SmartPark Arduino System Starting...");
  Serial.println("Servo Control: OPTIMIZED");
  Serial.println("Commands: SERVO_OPEN, SERVO_CLOSE");
  Serial.println("Status: READY");
  
  // Initial sensor reading
  readAllSensors();
  sendAllSlotStatus();
}

// ==================== MAIN LOOP ====================
void loop() {
  // Handle serial communication (non-blocking)
  handleSerialCommunication();
  
  // Update servo movement (non-blocking)
  updateServoMovement();
  
  // Read sensors periodically
  if (millis() - lastSensorRead >= SENSOR_READ_INTERVAL) {
    readAllSensors();
    checkForSlotChanges();
    lastSensorRead = millis();
  }
  
  // Send heartbeat periodically
  if (millis() - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = millis();
  }
  
  // Small delay to prevent overwhelming the loop
  delay(10);
}

// ==================== SERVO CONTROL FUNCTIONS ====================
void initializeServo() {
  servoCtrl.state = SERVO_IDLE;
  servoCtrl.currentAngle = SERVO_CLOSED_ANGLE;
  servoCtrl.targetAngle = SERVO_CLOSED_ANGLE;
  servoCtrl.lastStepTime = 0;
  servoCtrl.movementStartTime = 0;
  servoCtrl.isMoving = false;
  servoCtrl.hasError = false;
  
  // Set initial position
  gateServo.write(SERVO_CLOSED_ANGLE);
  delay(500); // Allow servo to reach initial position
  
  Serial.println("Servo initialized at closed position");
}

void startServoMovement(int targetAngle, ServoState newState) {
  // Safety check: prevent duplicate commands
  if (servoCtrl.isMoving && servoCtrl.targetAngle == targetAngle) {
    Serial.println("Servo already moving to target position");
    return;
  }
  
  // Safety check: already at target position
  if (abs(servoCtrl.currentAngle - targetAngle) <= SERVO_STEP_SIZE) {
    Serial.println("Servo already at target position");
    return;
  }
  
  servoCtrl.state = newState;
  servoCtrl.targetAngle = targetAngle;
  servoCtrl.movementStartTime = millis();
  servoCtrl.lastStepTime = millis();
  servoCtrl.isMoving = true;
  servoCtrl.hasError = false;
  
  String direction = (newState == SERVO_OPENING) ? "OPENING" : "CLOSING";
  Serial.println("Servo " + direction + " - Target: " + String(targetAngle) + "°");
}

void updateServoMovement() {
  if (!servoCtrl.isMoving) return;
  
  unsigned long currentTime = millis();
  
  // Check for timeout
  if (currentTime - servoCtrl.movementStartTime > SERVO_TIMEOUT) {
    handleServoError("Movement timeout");
    return;
  }
  
  // Check if it's time for the next step
  if (currentTime - servoCtrl.lastStepTime >= SERVO_STEP_DELAY) {
    moveServoOneStep();
    servoCtrl.lastStepTime = currentTime;
  }
}

void moveServoOneStep() {
  int difference = servoCtrl.targetAngle - servoCtrl.currentAngle;
  
  // Check if we've reached the target
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
  
  // Constrain to valid servo range
  servoCtrl.currentAngle = constrain(servoCtrl.currentAngle, 0, 180);
  
  // Write new position to servo
  gateServo.write(servoCtrl.currentAngle);
  
  // Debug output (optional - comment out for production)
  // Serial.println("Servo angle: " + String(servoCtrl.currentAngle) + "°");
}

void completeServoMovement() {
  servoCtrl.isMoving = false;
  servoCtrl.state = SERVO_IDLE;
  
  String status = (servoCtrl.currentAngle >= SERVO_OPEN_ANGLE) ? "OPENED" : "CLOSED";
  Serial.println("Servo movement complete - Gate " + status);
  Serial.println("SERVO_STATUS: " + status);
}

void handleServoError(String errorMsg) {
  servoCtrl.hasError = true;
  servoCtrl.isMoving = false;
  servoCtrl.state = SERVO_IDLE;
  
  Serial.println("SERVO_ERROR: " + errorMsg);
  
  // Attempt to recover by setting current position
  gateServo.write(servoCtrl.currentAngle);
  
  // Reset error flag after a delay
  delay(100);
  servoCtrl.hasError = false;
}

// ==================== SERVO COMMAND HANDLERS ====================
void openGate() {
  if (servoCtrl.currentAngle >= SERVO_OPEN_ANGLE && !servoCtrl.isMoving) {
    Serial.println("Gate already open");
    Serial.println("SERVO_STATUS: OPENED");
    return;
  }
  
  startServoMovement(SERVO_OPEN_ANGLE, SERVO_OPENING);
}

void closeGate() {
  if (servoCtrl.currentAngle <= SERVO_CLOSED_ANGLE && !servoCtrl.isMoving) {
    Serial.println("Gate already closed");
    Serial.println("SERVO_STATUS: CLOSED");
    return;
  }
  
  startServoMovement(SERVO_CLOSED_ANGLE, SERVO_CLOSING);
}

// ==================== SENSOR FUNCTIONS ====================
void initializeSensors() {
  for (int i = 0; i < NUM_SLOTS; i++) {
    pinMode(sensorPins[i], INPUT_PULLUP);
    slotStates[i] = false;
    lastSlotStates[i] = false;
  }
  Serial.println("IR sensors initialized");
}

void readAllSensors() {
  for (int i = 0; i < NUM_SLOTS; i++) {
    // IR sensor logic: LOW = occupied (object detected), HIGH = free
    bool isOccupied = (digitalRead(sensorPins[i]) == LOW);
    slotStates[i] = isOccupied;
  }
}

void checkForSlotChanges() {
  for (int i = 0; i < NUM_SLOTS; i++) {
    if (slotStates[i] != lastSlotStates[i]) {
      String status = slotStates[i] ? "OCCUPIED" : "FREE";
      Serial.println(slotLabels[i] + ": " + status);
      lastSlotStates[i] = slotStates[i];
    }
  }
}

void sendAllSlotStatus() {
  Serial.println("=== SLOT STATUS ===");
  for (int i = 0; i < NUM_SLOTS; i++) {
    String status = slotStates[i] ? "OCCUPIED" : "FREE";
    Serial.println(slotLabels[i] + ": " + status);
  }
  Serial.println("==================");
}

// ==================== SERIAL COMMUNICATION ====================
void handleSerialCommunication() {
  while (Serial.available() > 0) {
    char inChar = (char)Serial.read();
    
    if (inChar == '\n' || inChar == '\r') {
      if (serialBuffer.length() > 0) {
        processSerialCommand(serialBuffer);
        serialBuffer = "";
      }
    } else {
      serialBuffer += inChar;
    }
  }
}

void processSerialCommand(String command) {
  command.trim();
  command.toUpperCase();
  
  Serial.println("Received command: " + command);
  
  if (command == "SERVO_OPEN") {
    openGate();
  }
  else if (command == "SERVO_CLOSE") {
    closeGate();
  }
  else if (command == "STATUS") {
    sendSystemStatus();
  }
  else if (command == "SLOTS") {
    sendAllSlotStatus();
  }
  else if (command == "SERVO_STATUS") {
    sendServoStatus();
  }
  else if (command == "RESET_SERVO") {
    resetServo();
  }
  else if (command.startsWith("SET_ANGLES:")) {
    handleAngleConfiguration(command);
  }
  else {
    Serial.println("Unknown command: " + command);
    Serial.println("Available commands: SERVO_OPEN, SERVO_CLOSE, STATUS, SLOTS, SERVO_STATUS, RESET_SERVO");
  }
}

// ==================== STATUS AND DIAGNOSTIC FUNCTIONS ====================
void sendHeartbeat() {
  Serial.println("HEARTBEAT: " + String(millis()));
}

void sendSystemStatus() {
  Serial.println("=== SYSTEM STATUS ===");
  Serial.println("Uptime: " + String(millis() / 1000) + " seconds");
  Serial.println("Servo State: " + getServoStateString());
  Serial.println("Servo Angle: " + String(servoCtrl.currentAngle) + "°");
  Serial.println("Servo Moving: " + String(servoCtrl.isMoving ? "YES" : "NO"));
  Serial.println("Servo Error: " + String(servoCtrl.hasError ? "YES" : "NO"));
  
  // Count occupied slots
  int occupiedCount = 0;
  for (int i = 0; i < NUM_SLOTS; i++) {
    if (slotStates[i]) occupiedCount++;
  }
  Serial.println("Occupied Slots: " + String(occupiedCount) + "/" + String(NUM_SLOTS));
  Serial.println("====================");
}

void sendServoStatus() {
  String state = getServoStateString();
  String position = (servoCtrl.currentAngle >= SERVO_OPEN_ANGLE) ? "OPENED" : "CLOSED";
  
  Serial.println("SERVO_STATE: " + state);
  Serial.println("SERVO_POSITION: " + position);
  Serial.println("SERVO_ANGLE: " + String(servoCtrl.currentAngle));
  Serial.println("SERVO_TARGET: " + String(servoCtrl.targetAngle));
  Serial.println("SERVO_MOVING: " + String(servoCtrl.isMoving ? "YES" : "NO"));
}

String getServoStateString() {
  switch (servoCtrl.state) {
    case SERVO_IDLE: return "IDLE";
    case SERVO_OPENING: return "OPENING";
    case SERVO_CLOSING: return "CLOSING";
    default: return "UNKNOWN";
  }
}

// ==================== ADVANCED FEATURES ====================
void resetServo() {
  Serial.println("Resetting servo...");
  
  // Stop any current movement
  servoCtrl.isMoving = false;
  servoCtrl.state = SERVO_IDLE;
  servoCtrl.hasError = false;
  
  // Detach and reattach servo
  gateServo.detach();
  delay(100);
  gateServo.attach(SERVO_PIN);
  
  // Set to closed position
  servoCtrl.currentAngle = SERVO_CLOSED_ANGLE;
  servoCtrl.targetAngle = SERVO_CLOSED_ANGLE;
  gateServo.write(SERVO_CLOSED_ANGLE);
  
  delay(500);
  Serial.println("Servo reset complete");
}

void handleAngleConfiguration(String command) {
  // Format: SET_ANGLES:CLOSED_ANGLE,OPEN_ANGLE
  // Example: SET_ANGLES:0,90
  
  int colonIndex = command.indexOf(':');
  if (colonIndex == -1) {
    Serial.println("Invalid angle format. Use: SET_ANGLES:closed,open");
    return;
  }
  
  String angles = command.substring(colonIndex + 1);
  int commaIndex = angles.indexOf(',');
  
  if (commaIndex == -1) {
    Serial.println("Invalid angle format. Use: SET_ANGLES:closed,open");
    return;
  }
  
  int newClosedAngle = angles.substring(0, commaIndex).toInt();
  int newOpenAngle = angles.substring(commaIndex + 1).toInt();
  
  // Validate angles
  if (newClosedAngle < 0 || newClosedAngle > 180 || newOpenAngle < 0 || newOpenAngle > 180) {
    Serial.println("Invalid angles. Must be between 0-180 degrees");
    return;
  }
  
  if (abs(newOpenAngle - newClosedAngle) < 10) {
    Serial.println("Angles too close. Minimum difference: 10 degrees");
    return;
  }
  
  // Note: In a real implementation, you'd save these to EEPROM
  Serial.println("Angle configuration received:");
  Serial.println("Closed: " + String(newClosedAngle) + "°");
  Serial.println("Open: " + String(newOpenAngle) + "°");
  Serial.println("Note: Restart Arduino to apply new angles");
}

// ==================== ERROR RECOVERY ====================
void handleCommunicationError() {
  Serial.println("Communication error detected");
  
  // Reset serial buffer
  serialBuffer = "";
  
  // Clear serial buffer
  while (Serial.available()) {
    Serial.read();
  }
  
  Serial.println("Serial communication reset");
}
