// Motor Driver Pins
const int IN1 = 6;
const int IN2 = 7;
const int IN3 = 8;
const int IN4 = 9;

// Analog Input Pin
const int analogPin = A0;

void setup() {
  Serial.begin(9600);

  // Motor pins output ஆக செட் செய்கிறோம்
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // ஆரம்பத்தில் மோட்டாரை Stop நிலையில் வைக்க
  stopMotors();
}

void loop() {
  int sensorValue = analogRead(analogPin);

  Serial.print("Raw Value: ");
  Serial.println(sensorValue);

  // A0 மதிப்பு 610 முதல் 700 வரை இருந்தால் Forward
  if (sensorValue >= 610 && sensorValue <= 700) {
    moveForward();
  } else {
    // மற்ற அனைத்து மதிப்புகளுக்கும் Stop
    stopMotors();
  }

  delay(50); // சிக்னல் ஸ்டேபிளாக இருக்க சிறிய தாமதம்
}

// Forward இயக்கும் Function (முன்பு Reverse சுழன்ற நிலைகள் மாற்றப்பட்டுள்ளன)
void moveForward() {
  // Motor A - Forward (முன்பு HIGH/LOW இருந்ததை LOW/HIGH என மாற்றப்பட்டுள்ளது)
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  // Motor B - Forward (முன்பு LOW/HIGH இருந்ததை HIGH/LOW என மாற்றப்பட்டுள்ளது)
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

// மோட்டாரை நிறுத்தும் Function
void stopMotors() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}