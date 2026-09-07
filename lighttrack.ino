/*
  LightTrack Arduino firmware
  ---------------------------

  This program receives simple commands from Python and updates one or two
  WS2812B LED strips.

  Python sends commands such as:

    CONFIG 361
    SET 180 255 0 0
    CLEAR

  The Arduino does not work in metres. It only needs to know which LED
  should be active and what colour it should have.
*/

#include <Adafruit_NeoPixel.h>


// -----------------------------------------------------------------------------
// Hardware settings
// -----------------------------------------------------------------------------
//
// Change these pins only if the LED strips are connected somewhere else.

const int LEFT_PIN = 6;
const int RIGHT_PIN = 7;

// Brightness range: 0-255.
// A moderate value is usually sufficient for a response marker.
const int BRIGHTNESS = 64;


// -----------------------------------------------------------------------------
// LED strips
// -----------------------------------------------------------------------------
//
// The strips start with a temporary length of one LED.
// Python sends the real track length after connecting.

int numLeds = 1;
int previousLed = -1;

Adafruit_NeoPixel leftStrip(1, LEFT_PIN, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel rightStrip(1, RIGHT_PIN, NEO_GRB + NEO_KHZ800);


// Turn all LEDs off.
void clearTrack() {

  leftStrip.clear();
  rightStrip.clear();

  leftStrip.show();
  rightStrip.show();

  previousLed = -1;
}


// Set the number of LEDs used by the current physical setup.
void configureTrack(int n) {

  numLeds = n;

  leftStrip.updateLength(numLeds);
  rightStrip.updateLength(numLeds);

  leftStrip.setBrightness(BRIGHTNESS);
  rightStrip.setBrightness(BRIGHTNESS);

  clearTrack();
}


// Show one marker on both strips.
void showLed(int index, int r, int g, int b) {

  // Keep the requested LED inside the available range.
  index = constrain(index, 0, numLeds - 1);

  // Switch off the previous marker.
  if (previousLed >= 0) {
    leftStrip.setPixelColor(previousLed, 0);
    rightStrip.setPixelColor(previousLed, 0);
  }

  // Light the same position on both strips.
  leftStrip.setPixelColor(index, leftStrip.Color(r, g, b));
  rightStrip.setPixelColor(index, rightStrip.Color(r, g, b));

  leftStrip.show();
  rightStrip.show();

  previousLed = index;
}


void setup() {

  // Must match the baud rate used in lighttrack.py.
  Serial.begin(115200);
  Serial.setTimeout(20);

  leftStrip.begin();
  rightStrip.begin();

  clearTrack();
}


void loop() {

  // Do nothing until Python sends a command.
  if (!Serial.available()) {
    return;
  }

  // Each command is one line of text.
  String command = Serial.readStringUntil('\n');
  command.trim();


  // Example:
  // CONFIG 361
  //
  // Python sends this once when LightTrack connects.
  if (command.startsWith("CONFIG ")) {

    int n;

    if (sscanf(command.c_str(), "CONFIG %d", &n) == 1) {
      configureTrack(n);
    }
  }


  // Example:
  // SET 180 255 0 0
  //
  // This means:
  // LED 180, red=255, green=0, blue=0.
  else if (command.startsWith("SET ")) {

    int index, r, g, b;

    if (sscanf(
      command.c_str(),
      "SET %d %d %d %d",
      &index, &r, &g, &b
    ) == 4) {
      showLed(index, r, g, b);
    }
  }


  // Turn the track off.
  else if (command == "CLEAR") {
    clearTrack();
  }
}
