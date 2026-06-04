# 🔌 SmartPark Hardware Wiring Diagrams

Complete wiring guide for reliable servo control and sensor integration.

## 🎯 **Recommended Setup (External Power)**

### **Components List**
```
Required:
✅ Arduino UNO
✅ MG996R Servo (or SG90 with external power)
✅ 6x IR Obstacle Sensors (FC-51 or similar)
✅ 5V 2A Power Supply
✅ Breadboard or Terminal Blocks
✅ Jumper Wires (Male-Male, Male-Female)

Optional:
🔧 1000µF Capacitor (power smoothing)
🔧 LED indicators for status
🔧 Push button for manual control
```

---

## 📐 **Wiring Diagram 1: External Power (Recommended)**

```
                    ┌─────────────────┐
                    │   Arduino UNO   │
                    │                 │
                    │  Digital Pins   │
    IR Sensors ──── │  2,3,4,5,6,7   │
                    │                 │
    Servo Signal ── │  Pin 9         │
                    │                 │
    Common Ground ─ │  GND           │ ─┬─ External PSU (-)
                    │                 │  │
                    │  5V (unused)    │  │
                    └─────────────────┘  │
                                         │
    ┌─────────────────────────────────────┴──────────────┐
    │                                                    │
    │  ┌──────────────────┐    ┌─────────────────────┐   │
    │  │  5V 2A Power     │    │     MG996R Servo    │   │
    │  │  Supply          │    │                     │   │
    │  │                  │    │  Red   (VCC) ───────┼───┤
    │  │  (+) ────────────┼────┤  Brown (GND) ───────┼───┤
    │  │  (-) ────────────┼────┤  Orange(Signal) ────┼───┘
    │  └──────────────────┘    └─────────────────────┘
    └───────────────────────────────────────────────────┘
                              │
                              └── To Arduino Pin 9
```

### **Connection Table**
| Component | Wire Color | Arduino Pin | External PSU | Notes |
|-----------|------------|-------------|--------------|--------|
| Servo VCC | Red | - | (+) 5V | High current from external supply |
| Servo GND | Brown | GND | (-) GND | **Common ground critical!** |
| Servo Signal | Orange | Pin 9 | - | Control signal only |
| IR Sensor 1 | - | Pin 2 | - | SLOT_1 detection |
| IR Sensor 2 | - | Pin 3 | - | SLOT_2 detection |
| IR Sensor 3 | - | Pin 4 | - | SLOT_3 detection |
| IR Sensor 4 | - | Pin 5 | - | SLOT_4 detection |
| IR Sensor 5 | - | Pin 6 | - | SLOT_5 detection |
| IR Sensor 6 | - | Pin 7 | - | SLOT_6 detection |

---

## 📐 **Wiring Diagram 2: Arduino Power Only (Basic)**

```
                    ┌─────────────────┐
                    │   Arduino UNO   │
                    │                 │
    IR Sensors ──── │  2,3,4,5,6,7   │
                    │                 │
    Servo Signal ── │  Pin 9         │
    Servo VCC ───── │  5V            │ ⚠️ Limited current
    Servo GND ───── │  GND           │
                    │                 │
                    │  USB Power      │ ── To PC
                    └─────────────────┘
```

**⚠️ Warning:** This setup may cause:
- Voltage drops under load
- Jerky servo movement  
- Arduino resets
- Reduced servo torque

---

## 🔧 **IR Sensor Wiring Details**

### **Typical IR Sensor (FC-51) Pinout**
```
IR Sensor Module:
┌─────────────┐
│  [LED] [RX] │
│             │
│ VCC GND OUT │
└─┬───┬───┬───┘
  │   │   │
  │   │   └── To Arduino Digital Pin (2-7)
  │   └────── To Arduino GND
  └────────── To Arduino 5V
```

### **IR Sensor Connection Table**
| Sensor | Slot | Arduino Pin | VCC | GND | Signal |
|--------|------|-------------|-----|-----|--------|
| IR-1 | SLOT_1 | Pin 2 | 5V | GND | Digital |
| IR-2 | SLOT_2 | Pin 3 | 5V | GND | Digital |
| IR-3 | SLOT_3 | Pin 4 | 5V | GND | Digital |
| IR-4 | SLOT_4 | Pin 5 | 5V | GND | Digital |
| IR-5 | SLOT_5 | Pin 6 | 5V | GND | Digital |
| IR-6 | SLOT_6 | Pin 7 | 5V | GND | Digital |

**Detection Logic:**
- `HIGH` (5V) = No obstacle detected = Slot FREE
- `LOW` (0V) = Obstacle detected = Slot OCCUPIED

---

## ⚡ **Power Supply Specifications**

### **Recommended External Power Supply**
```
Specifications:
- Voltage: 5V DC (±0.25V tolerance)
- Current: 2A minimum (3A recommended for safety margin)
- Connector: 2.1mm barrel jack or terminal blocks
- Regulation: <1% ripple
- Protection: Over-current, over-voltage

Recommended Models:
- Mean Well RS-15-5 (15W, 3A)
- ALITOVE 5V 6A Power Supply
- Generic 5V 2A Wall Adapter
```

### **Power Consumption Calculation**
```
Component Power Usage:
- Arduino UNO: ~200mA
- 6x IR Sensors: ~60mA (10mA each)
- MG996R Servo (idle): ~100mA
- MG996R Servo (moving): ~800-1200mA
- Total Peak: ~1400mA

Safety Margin: 2A supply recommended
```

---

## 🛡️ **Power Protection Circuit (Optional)**

### **Basic Protection**
```
5V PSU (+) ──┬── 1000µF Capacitor ──┬── To Servo VCC
             │                      │
             └── 100Ω Resistor ─────┘
             
5V PSU (-) ────────────────────────── To Servo GND + Arduino GND
```

### **Advanced Protection**
```
5V PSU (+) ──┬── Fuse (2A) ──┬── 1000µF Cap ──┬── To Servo VCC
             │               │                │
             └── LED + 330Ω ─┘                │
                                              │
5V PSU (-) ──┬─────────────────────────────────┘
             │
             └── To Arduino GND
```

**Components:**
- **1000µF Capacitor**: Smooths power during servo movement
- **2A Fuse**: Protects against short circuits
- **LED Indicator**: Shows power status
- **330Ω Resistor**: Current limiting for LED

---

## 🔌 **Breadboard Layout**

### **Compact Breadboard Setup**
```
     A  B  C  D  E     F  G  H  I  J
   ┌─────────────────────────────────┐
 1 │ +  +  +  +  +     +  +  +  +  + │ ← 5V Rail
 2 │ -  -  -  -  -     -  -  -  -  - │ ← GND Rail
   │                                 │
 3 │       IR1 IR2 IR3 IR4 IR5 IR6   │ ← IR Sensors
 4 │        │   │   │   │   │   │    │
 5 │        2   3   4   5   6   7    │ ← Arduino Pins
   │                                 │
10│              Servo               │
11│            Red Brown Orange      │
12│             │    │     │         │
13│            PSU  GND    9         │ ← Connections
   └─────────────────────────────────┘
```

---

## 🔧 **Servo Mounting Considerations**

### **Mechanical Setup**
```
Gate Mechanism Options:

1. Direct Drive (Simple):
   Servo Horn → Gate Arm (90° rotation)
   
2. Lever System (More Torque):
   Servo → Short Lever → Long Gate Arm
   
3. Gear Reduction (Heavy Gates):
   Servo → Gear Train → Gate Mechanism
```

### **Mounting Tips**
- **Secure Mounting**: Use servo mounting brackets
- **Alignment**: Ensure servo shaft is perpendicular to gate
- **Clearance**: Allow full 0°-180° rotation
- **Protection**: Shield from weather if outdoor use

---

## 🧪 **Testing Procedures**

### **Step 1: Power Test**
```bash
1. Connect external power supply
2. Measure voltage at servo VCC pin
3. Should read 4.8-5.2V under no load
4. Should not drop below 4.5V during movement
```

### **Step 2: Servo Test**
```bash
1. Upload optimized sketch
2. Send "SERVO_OPEN" command
3. Measure current draw (should be <1.5A)
4. Verify smooth 0°→90° movement in ~1 second
```

### **Step 3: Sensor Test**
```bash
1. Send "SLOTS" command
2. Block each IR sensor with hand
3. Verify status changes from FREE to OCCUPIED
4. Check all 6 sensors respond correctly
```

### **Step 4: Integration Test**
```bash
1. Start backend: python run.py
2. Connect to frontend: http://localhost:5173
3. Verify real-time slot updates
4. Test servo commands from web interface
```

---

## 🚨 **Troubleshooting Common Issues**

### **Servo Doesn't Move**
```
Check:
✅ Power supply voltage (4.8-5.2V)
✅ Common ground connection
✅ Signal wire to correct pin (Pin 9)
✅ Servo not mechanically blocked
✅ Serial commands received correctly
```

### **Jerky Movement**
```
Solutions:
✅ Add external power supply
✅ Add 1000µF capacitor
✅ Check all ground connections
✅ Use shorter, thicker power wires
✅ Reduce SERVO_STEP_SIZE in code
```

### **Arduino Resets**
```
Causes & Fixes:
✅ Voltage drop → External power supply
✅ Ground loops → Single common ground
✅ EMI from servo → Add capacitor
✅ Overcurrent → Check wiring
```

### **IR Sensors Not Working**
```
Check:
✅ 5V power to sensors
✅ Ground connections
✅ Digital pins 2-7 connected
✅ Sensor orientation (LED facing target)
✅ Detection range (2-30cm typical)
```

---

## 📋 **Final Checklist**

### **Before First Power-On**
- [ ] All connections double-checked
- [ ] Common ground established
- [ ] No short circuits
- [ ] Servo mechanically free to move
- [ ] External power supply rated correctly

### **Before Integration**
- [ ] Arduino sketch uploaded successfully
- [ ] Serial communication working (9600 baud)
- [ ] All sensors responding correctly
- [ ] Servo moves smoothly on command
- [ ] Backend can communicate with Arduino

### **Production Ready**
- [ ] All connections secured (no loose wires)
- [ ] Power supply stable under load
- [ ] Error handling tested
- [ ] System runs reliably for 24+ hours
- [ ] Documentation updated with any changes

**🎯 With this wiring setup, your servo gate will operate smoothly and reliably!**
