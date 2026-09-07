"""
LightTrack Python interface
---------------------------

This file contains the small Python class used to control the LED track.

The experiment works in metres:
    track.show(5.0)

LightTrack converts that distance to the nearest LED and sends the LED
number and colour to the Arduino.
"""

import time
import serial


class LightTrack:

    # Default colours used by the response marker.
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)

    def __init__(self, port, start_m=1, end_m=13, leds_per_m=30):
        """
        Connect to LightTrack and describe the physical LED track.

        Parameters
        ----------
        port
            Arduino serial port, for example "COM5" or
            "/dev/cu.usbmodem101".

        start_m
            Physical position of the first LED, in metres.

        end_m
            Physical position of the last LED, in metres.

        leds_per_m
            LED density of the strip.
        """

        self.start_m = float(start_m)
        self.end_m = float(end_m)
        self.leds_per_m = float(leds_per_m)

        # Number of LED positions needed to cover the requested range.
        # +1 includes both the first and last position.
        self.num_leds = round(
            (self.end_m - self.start_m) * self.leds_per_m
        ) + 1

        # Keep track of the currently displayed physical position.
        self.position_m = self.start_m

        # Open the USB serial connection to the Arduino.
        self.serial = serial.Serial(port, 115200, timeout=1)

        # Many Arduino boards restart when the serial connection opens.
        # A short pause gives the board time to become ready.
        time.sleep(1.5)

        # Tell the Arduino how many LEDs are used by this setup.
        self._send(f"CONFIG {self.num_leds}")

    def _send(self, message):
        """Send one text command to the Arduino."""
        self.serial.write((message + "\n").encode("ascii"))

    def distance_to_led(self, distance_m):
        """
        Convert a physical distance to the nearest LED number.

        Distances outside the track are limited to the track boundaries.
        """

        distance_m = max(
            self.start_m,
            min(self.end_m, float(distance_m)),
        )

        return round(
            (distance_m - self.start_m) * self.leds_per_m
        )

    def led_to_distance(self, led):
        """Convert an LED number back to its physical position."""
        return self.start_m + led / self.leds_per_m

    def show(self, distance_m, colour=RED):
        """
        Show the marker at a requested distance.

        The returned value is the actual physical LED position after
        rounding to the nearest available LED.
        """

        led = self.distance_to_led(distance_m)
        self.position_m = self.led_to_distance(led)

        r, g, b = colour

        # The Arduino only needs the LED number and RGB colour.
        self._send(f"SET {led} {r} {g} {b}")

        return self.position_m

    def confirm(self):
        """Show the current response position in green."""
        return self.show(self.position_m, self.GREEN)

    def clear(self):
        """Turn all LEDs off."""
        self._send("CLEAR")

    def close(self):
        """Close the serial connection."""
        self.serial.close()
