// 0 RX
// 1 TX
// 2 Circulation Pump Relay[4] (Power)
// 3 Buffer Pump Relay[3] (Power)
// 4 ATO Pump Relay[2] (Power)
// 5 -empty-
// 6 Stir Relay[1] (Power)
// 7 Temp Probe (Data)
// 8 -empty-
// 9 Min Water (Green) 
// 10 Max Water (Blue)
// 11 TDS Relay[6] (Power)
// 12 PH Relay[5] (Power)
// 13 -empty-

#define BAUD_RATE 9600

// Sampling
#define SAMPLE_COUNT 30

// LCD
#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels
#define OLED_RESET     -1 // Reset pin # (or -1 if sharing Arduino reset pin)
#define SCREEN_ADDRESS 0x3C ///< See datasheet for Address; 0x3D for 128x64, 0x3C for 128x32

// Relays
#define RELAY_CIRC_PIN 2 
#define RELAY_BUFF_PIN 3
#define RELAY_ATO_PIN 4
#define RELAY_STIR_PIN 6
#define RELAY_TDS_PIN 11
#define RELAY_PH_PIN 12

// Sensors
#define TEMP_PIN 7
#define LOW_WATER_PIN 9
#define HIGH_WATER_PIN 10
#define TDS_PIN A1
#define PH_PIN A0

// #define MS_TO_ML 545
// #define MIN_PH 10 // 5.5