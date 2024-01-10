#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_SSD1306.h>
#include "demeter.h"

int RELAY_PINS[] = {
  RELAY_STIR_PIN,
  RELAY_ATO_PIN,
  RELAY_BUFF_PIN,
  RELAY_CIRC_PIN, 
  RELAY_PH_PIN,
  RELAY_TDS_PIN,
};

// State-Tracking
unsigned long previousMillis = 0; // lol don't use int here
float last_ph = 0.1;
float last_temp_c = 0.1;
float last_temp_f = 0.1;
float last_tds = 0.1;
bool last_high_water_alarm = false;
bool last_low_water_alarm = false;
String last_report;

OneWire oneWire(TEMP_PIN);
DallasTemperature sensors(&oneWire);
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

/* FUNCS ==================================================================== */

void deenergize(){
  // Turn off all relays.
  for(unsigned int i = 0; i < sizeof(RELAY_PINS); i = i + 1 ){
    digitalWrite(RELAY_PINS[i], HIGH);  
  }
}

void circulate_reservoir(int seconds){
  // Run res pump for N seconds.
  digitalWrite(RELAY_CIRC_PIN, LOW);
  previousMillis = millis();
  while(millis() - previousMillis < seconds*1000){ /* Blocking */ }
  digitalWrite(RELAY_CIRC_PIN, HIGH);
}

void update_display(){
  display.setTextSize(2); 
  display.setTextColor(SSD1306_WHITE);
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println(millis()/1000);
  display.display(); 
}

String report(){
  last_report = ">D:f:"+String(last_temp_f);
  last_report += ",c:"+String(last_temp_c);
  last_report += ",t:"+String(last_tds);
  last_report += ",p:"+String(last_ph);
  last_report += ",l:"+String(last_low_water_alarm);
  last_report += ",h:"+String(last_high_water_alarm);
  last_report += "<";
  return last_report;
}

void update_water_levels(){
  last_high_water_alarm = digitalRead(HIGH_WATER_PIN);
  last_low_water_alarm = !digitalRead(LOW_WATER_PIN);
}

void update_temp(){
  deenergize();
  sensors.requestTemperatures();
  last_temp_c = sensors.getTempCByIndex(0);
  last_temp_f = sensors.getTempFByIndex(0);
}

void update_ph(){
  deenergize();
  
  // Ensure pH probe is energized.
	digitalWrite(RELAY_PH_PIN, LOW);

  // Allow warm-up time for pH sensor.
  previousMillis = millis();
  while(millis() - previousMillis < 2000){
    Serial.println(">D:-<");
  }

  // Take multiple measurements.
	int measurings = 0;
  for (int i = 0; i < SAMPLE_COUNT; i++){
    while(millis() - previousMillis < 200){ /* Blocking */ }
    measurings += analogRead(PH_PIN);
    previousMillis = millis();
  }

  // Kill probe.
	digitalWrite(RELAY_PH_PIN, HIGH);

  // Compute & set pH value.
	float voltage = 5 / 1024.0 * measurings/SAMPLE_COUNT;
	float pHValue = -6.25 * voltage + 22.875;
	last_ph =  pHValue;
}

void update_environment(){
  // circulate_reservoir(30);
  update_water_levels();
  update_temp();
  update_ph();
  // update_tds();
}

/* MAIN ===================================================================== */

void setup() {
  Serial.begin(BAUD_RATE);

  // Init temp probe.
  sensors.begin();

  // Init relay pins.
  for(unsigned int i = 0; i < sizeof(RELAY_PINS); i = i + 1 ){
    pinMode(RELAY_PINS[i], OUTPUT);
  }

  // Ensure relays are off.
  deenergize();

  // Configure float switch pins.
  pinMode(LOW_WATER_PIN, INPUT_PULLUP);
  pinMode(HIGH_WATER_PIN, INPUT_PULLUP);

  // Configure LCD driver.
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)){ // SSD1306_SWITCHCAPVCC = generate display voltage from 3.3V internally
    Serial.println(F("SSD1306 allocation failed"));
    for(;;); // Don't proceed, loop forever
  }
}

void loop(){
  // circulate_reservoir(30000);

  // Handle any msg from serial.
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');

    // FIXME: switch
    if(data == "update_environment"){
      update_environment();
    }
  }

  Serial.println(report());

  update_display();

  // Pause
  previousMillis = millis();
  while(millis() - previousMillis < 500){ /* Blocking */ }
}
