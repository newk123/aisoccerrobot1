# aisoccerrobot1
soccerbot
Autonomous Soccer Ball Detection RobotAn edge AI robotics project combining a Raspberry Pi (running an optimized YOLO NCNN object detection model via Picamera2) with an Arduino Uno microcontroller to track and react to soccer balls in real time.Architecture Overview[ Raspberry Pi Camera v2/3 ]
              │
              ▼
[ Raspberry Pi 4/5 (Edge AI) ]
  - YOLO Object Detection (NCNN Format)
  - 3-Second High Output Pulse Logic
  - GPIO 17 / 27 / 22 Trigger
              │
              ▼ (3.3V Logic Signal + Common GND)
[ Pull-Down Resistor (10kΩ to GND) ]
              │
              ▼
[ Arduino Uno (A0 Pin) ]
  - Software Noise Filtering (ADC Range: 610–700)
  - Output to Motor Driver (Pins 6, 7, 8, 9)
              │
              ▼
[ Dual DC Motors (Differential Drive Chassis) ]
Hardware RequirementsSBC: Raspberry Pi 4 / 5 (Raspberry Pi OS 64-bit)Camera: Raspberry Pi Camera Module (CSI interface)Microcontroller: Arduino Uno / NanoActuation: L298N or L293D Dual H-Bridge Motor Driver + 2x DC Gear MotorsNoise Mitigation: 1kΩ to 10kΩ Resistor (Pull-Down between Arduino A0 and GND)Power: External battery pack for motors (Separate logic & motor supplies recommended)Hardware Pinout & Wiring1. Raspberry Pi to Arduino InterfaceRaspberry Pi PinArduino PinDescriptionGPIO 17 (or 27, 22)A03.3V trigger pulse when ball detectedGNDGNDCrucial: Common ground reference—A0 to GND1kΩ - 10kΩ Resistor (Hardware Pull-Down)2. Arduino to Motor Driver (L298N / L293D)Arduino PinMotor Driver PinFunctionD6IN1Motor A Direction 1D7IN2Motor A Direction 2D8IN3Motor B Direction 1D9IN4Motor B Direction 2GNDGNDCommon Ground with Battery & LogicSoftware & Environment Setup1. Raspberry Pi SetupA. Virtual Environment SetupBashcd ~/Soccer
source ai_env/bin/activate
pip install ultralytics opencv-python picamera2
B. Hardware Pull-Down at Boot (Fix Floating Pins)To prevent GPIO floating voltages (~1.5V) before Python loads:Bashsudo nano /boot/firmware/config.txt
# (or /boot/config.txt on older OS releases)
Add to the end of the file:Plaintextgpio=17,27,22=pd
C. Autoboot Setup via SystemdCreate a systemd unit file:Bashsudo nano /etc/systemd/system/ball_detect.service
Paste the following:Ini, TOML[Unit]
Description=Soccer Ball Detection Autoboot Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Soccer/ncn
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
ExecStart=/home/pi/Soccer/ai_env/bin/python /home/pi/Soccer/ncn/Final_ball_detection.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
Enable and start the service:Bashsudo systemctl daemon-reload
sudo systemctl enable ball_detect.service
sudo systemctl start ball_detect.service
Arduino Firmware (robot_controller.ino)Upload the following sketch via the Arduino IDE:C++// Motor Driver Pins
const int IN1 = 6;
const int IN2 = 7;
const int IN3 = 8;
const int IN4 = 9;

// Analog Input Pin connected to Raspberry Pi GPIO
const int analogPin = A0;

void setup() {
  Serial.begin(9600);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  stopMotors();
}

void loop() {
  int sensorValue = analogRead(analogPin);

  // 3.3V GPIO pulse translates to ~660-680 on a 5V 10-bit ADC
  if (sensorValue >= 610 && sensorValue <= 700) {
    moveForward();
  } else {
    stopMotors();
  }

  delay(30);
}

void moveForward() {
  // Configured for forward rotation
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void stopMotors() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}
Operational CommandsCheck Service Status:Bashsudo systemctl status ball_detect.service
View Real-Time Detection Logs:Bashjournalctl -u ball_detect.service -f
Stop / Restart Service:Bashsudo systemctl stop ball_detect.service
sudo systemctl restart ball_detect.service
Troubleshooting GuideMotors Jitter / False Trigger on Boot:Ensure the 10kΩ pull-down resistor is placed between Arduino A0 and GND, and verify gpio=17,27,22=pd exists in /boot/firmware/config.txt.No Motor Response When Ball Detected:Check serial monitor values. If reading is below 610, verify common GND between Pi and Arduino, or widen the detection threshold in the Arduino code.Camera Stalls:Ensure Picamera2 is not being accessed by another process or legacy camera stack (raspicam).
