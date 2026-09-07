# LightTrack

**LightTrack** is a simple, Arduino-controlled LED response track for behavioural and psychophysics experiments.

![LightTrack system overview](https://github.com/jakab13/LightTrack/blob/master/system_overview.png)

The original prototype was developed for auditory distance-estimation experiments at Leipzig University's [Neurobiology Group](https://www.lw.uni-leipzig.de/en/institut-fuer-biologie/abteilungen/general-zoology-and-neurobiology/research). Participants moved a red marker along two floor-mounted LED strips with an Xbox controller and pressed A to confirm their response.

---

## Files

The implementation is intentionally small:

Python keeps track of the participant's current response, converts that distance to the nearest LED position, and sends the corresponding command to an Arduino. The Arduino only controls the LED strips.

```text
README.md
lighttrack.py
lighttrack.ino
experiment_example.py
requirements.txt
LICENSE

system_overview.png
wiring.svg
experiment_example.png
```

- `lighttrack.py` — Python interface to the response track
- `lighttrack.ino` — Arduino firmware
- `experiment_example.py` — small auditory distance-estimation example
- `requirements.txt` — Python dependencies

---

## Hardware

A basic LightTrack setup needs only a few components.

| Part | What it does | Example / helper |
|---|---|---|
| **Arduino** | Receives serial commands from Python and controls the LEDs | [Arduino Nano R4](https://docs.arduino.cc/hardware/nano-r4/) |
| **WS2812B-compatible LED strip** | Displays the response position | [Example 30 LEDs/m strip](https://www.adafruit.com/product/2537) |
| **5 V power supply** | Powers the LED strips | Use a regulated supply appropriate for the installation |
| **330–470 Ω resistors** | Placed in the LED data lines | One resistor per strip |
| **500–1000 µF capacitor** | Helps stabilise the LED power line | Recommended near the strip power input |
| **USB cable** | Connects the Arduino to the experiment computer | Match the Arduino connector |
| **Game controller** | Participant input in the example | [Xbox Wireless Controller](https://www.xbox.com/accessories/controllers/xbox-wireless-controller) |
| **Wires / connectors** | Connects the components | Jumper wires, screw terminals, etc. |

### Recommended Arduino

For a new build, a **compact 5 V Arduino** is the easiest option.

The [Arduino Nano R4](https://docs.arduino.cc/hardware/nano-r4/) is a good default because it combines a small Nano-format board with **5 V GPIO** and USB-C. This makes it convenient for a small portable interface and avoids the extra logic-level conversion normally needed when a 3.3 V controller drives a 5 V LED strip.

The original LightTrack prototype used an **Arduino Nano 33 IoT**. Its small size was useful for the same portability reasons, but it uses 3.3 V GPIO. If a 3.3 V board is used, a suitable logic-level shifter is recommended.

### LED strips

LightTrack is written for individually addressable WS2812B-style RGB strips.

The original system used **30 LEDs/m**, giving a physical response resolution of about:

```text
1 / 30 m = 3.3 cm
```

The Adafruit strip linked above is only an example. Equivalent 5 V WS2812B-compatible strips from other suppliers should work as well.

For general wiring and power guidance, the [Adafruit NeoPixel Überguide](https://learn.adafruit.com/adafruit-neopixel-uberguide) and its [best-practices page](https://learn.adafruit.com/adafruit-neopixel-uberguide/best-practices) are useful references.

---

## Wiring

The default Arduino pins in `lighttrack.ino` are:

```cpp
LEFT_PIN = 6
RIGHT_PIN = 7
```

The two strips should be installed in the **same direction**, with LED 0 at the start of the response track.

Basic wiring:

```text
Arduino D6  ---- 330–470 Ω resistor ---- DIN left strip
Arduino D7  ---- 330–470 Ω resistor ---- DIN right strip

Arduino GND ---------------------------- power supply GND
LED strip GND -------------------------- power supply GND
LED strip +5 V ------------------------- power supply +5 V
```

The Arduino and the LED power supply must share a **common ground**.

Do not power a long LED strip from the Arduino itself. Use an external regulated 5 V power supply. For long physical installations, power may need to be supplied at more than one point along the strip.

---

## Arduino setup

1. Install the [Arduino IDE](https://www.arduino.cc/en/software).
2. Install the [Adafruit NeoPixel library](https://github.com/adafruit/Adafruit_NeoPixel).
3. Open `lighttrack.ino`.
4. Check that `LEFT_PIN` and `RIGHT_PIN` match your wiring.
5. Upload the sketch to the Arduino.

The Arduino does not need to know the physical distance range. Python sends the required number of LED positions when it connects.

---

## Python setup

Install the required packages:

```bash
pip install -r requirements.txt
```

The main LightTrack settings are defined in metres:

```python
from lighttrack import LightTrack

track = LightTrack(
    port="COM5",
    start_m=1,
    end_m=13,
    leds_per_m=30,
)
```

On macOS or Linux, the serial port may look more like:

```python
port="/dev/cu.usbmodem101"
```

### Basic use

```python
track.show(7.0)       # red marker at approximately 7 m
track.confirm()       # current marker turns green

track.clear()
track.close()
```

The experimenter never needs to work directly with LED numbers.

For example, with:

```python
start_m = 1
end_m = 13
leds_per_m = 30
```

LightTrack automatically maps:

```text
1 m   -> beginning of the track
7 m   -> middle of the track
13 m  -> end of the track
```

If a requested position falls between two LEDs, the nearest physical LED is used.

---

## Example experiment

*Illustrative example only — the physical length and arrangement of the track can be changed freely.*

`experiment_example.py` demonstrates LightTrack as a response device in a small auditory distance-estimation task.

The participant:

1. hears a sound;
2. moves the LightTrack marker to the perceived distance;
3. presses **A** to confirm the response.

The marker remains visible throughout the experiment. The current marker position is carried from trial to trial and only changes when the participant moves it.

### Example trial

Conceptually, one trial is:

```python
target_m = 8

stimulus = make_stimulus(target_m)
stimulus.play()

response_m = get_response(
    track,
    controller,
    position_m,
)
```

---

## Mock auditory distance stimulus

The example uses [`slab`](https://github.com/DrMarc/slab), a Python package for psychoacoustic experiments.

A simple virtual room is created using `slab.Room`:

```python
room = slab.Room(
    size=[30, 30, 4],
    listener=[15, 15, 1.5],
    source=[0, 0, 2],
    absorption=[0.15],
)
```

On each trial, the source is moved to a new distance:

```python
room.set_source([0, 0, distance_m])
```

A room impulse response is generated and applied to a short noise stimulus:

```python
hrir = room.hrir(trim=0.25)

sound = slab.Sound.pinknoise(
    duration=0.3,
    samplerate=hrir.samplerate,
)

stimulus = hrir.apply(sound)
```

This sound simulation is only a convenient example of how LightTrack can be integrated into an experiment. It is **not** intended to reproduce a particular auditory-distance paradigm.

Useful links:

- [slab GitHub repository](https://github.com/DrMarc/slab)
- [slab documentation](https://slab.readthedocs.io/)

---

## Quick test

Before running an experiment, the track can be checked with a few lines:

```python
from time import sleep
from lighttrack import LightTrack

track = LightTrack("COM5", 1, 13, 30)

for distance in [1, 4, 7, 10, 13]:
    track.show(distance)
    sleep(1)

track.confirm()
sleep(1)

track.clear()
track.close()
```

Check that:

- both strips show a single marker;
- both markers indicate the same physical position;
- the marker moves in the expected direction;
- confirmation changes the marker to green.

---

## Troubleshooting

### No LEDs turn on

Check:

- the external 5 V supply;
- common ground between Arduino and LED supply;
- LED strip `DIN` rather than `DOUT`;
- Arduino serial port;
- whether `lighttrack.ino` was uploaded successfully.

### Arduino connects, but LEDs do not respond

Check:

- D6 and D7 wiring;
- the resistor in each data line;
- that the strip is WS2812B-compatible;
- that the Arduino and Python code both use 115200 baud.

### Only one strip works

Check the second strip's:

- data wire;
- 5 V connection;
- ground connection.

### Position does not match the physical track

Check:

```python
start_m
end_m
leds_per_m
```

Also verify where the first physical LED sits relative to the start of the distance scale.

### LEDs behave unreliably

Check the power wiring first. A resistor in the data line and a capacitor across the LED supply are recommended, and long strips may require additional power injection.

---

## How LightTrack fits into other experiments

LightTrack itself does not depend on auditory experiments.

The same interface can be used wherever a participant needs to indicate a position along a physical scale:

```text
controller / keyboard / other input
                ↓
          experiment code
                ↓
       response in physical units
                ↓
            LightTrack
                ↓
             Arduino
                ↓
            LED marker
```

Python remains the central hub, so the input device and stimulus software can be replaced without changing the Arduino side.

---

## Original prototype

LightTrack grew out of an auditory distance-perception setup at Leipzig University.

The original prototype used:

- two floor-mounted addressable RGB LED strips;
- 30 LEDs/m;
- approximately 1–13 m of response space;
- one active red marker on both strips;
- green confirmation feedback;
- an Xbox One-compatible controller;
- an Arduino Nano 33 IoT;
- Python as the central experiment and response interface.

The strips extended beyond the loudspeaker range, which helped avoid making the response endpoints identical to the nearest and furthest possible sound-source positions. This response arrangement is described in the original experiment documentation.

---

## Useful links

- [Arduino Nano R4 documentation](https://docs.arduino.cc/hardware/nano-r4/)
- [Arduino Nano R4 official store](https://store.arduino.cc/products/nano-r4)
- [Arduino IDE](https://www.arduino.cc/en/software)
- [Adafruit NeoPixel 30 LEDs/m example strip](https://www.adafruit.com/product/2537)
- [Adafruit NeoPixel Überguide](https://learn.adafruit.com/adafruit-neopixel-uberguide)
- [NeoPixel best practices](https://learn.adafruit.com/adafruit-neopixel-uberguide/best-practices)
- [Adafruit NeoPixel Arduino library](https://github.com/adafruit/Adafruit_NeoPixel)
- [Xbox Wireless Controller](https://www.xbox.com/accessories/controllers/xbox-wireless-controller)
- [slab](https://github.com/DrMarc/slab)
- [slab documentation](https://slab.readthedocs.io/)
- [Original distance_anchoring experiment](https://github.com/SebSchroe/distance_anchoring)

---

## License

See `LICENSE`.
