"""
Auditory distance experiment (Mittweida)
----------------------------------------

LightTrack is used as the response tool.
The sound is auralized and played by liveRAZR, and Unreal Engine manages the experiment flow.
Unreal and this script talk to each other with OSC messages.

Each trial follows the same structure:

    1. Unreal sends /lighttrack/start.
    2. The participant moves the LightTrack marker.
    3. The participant presses A to confirm the response.
    4. The response distance is sent back to Unreal as /lighttrack/response.

The experiment ends when Unreal sends /lighttrack/end, or with Ctrl+C.

The marker stays visible throughout the experiment.
"""

import queue
import threading
import time

import pygame  # used to connect to the Xbox controller
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

from lighttrack import LightTrack


# -----------------------------------------------------------------------------
# Experiment settings
# -----------------------------------------------------------------------------
#
# These are the values a new user is most likely to change.

PORT = "/dev/cu.usbmodem101"

TRACK_START_M = 1.0  # first LED 1 m from the participant
TRACK_END_M = 20.0  # last LED 20 m from the participant
LEDS_PER_M = 30  # 30 LEDs per metre

# Position of the marker when the experiment starts.
INITIAL_POSITION_M = 7.0

# Controller sensitivity.
JOYSTICK_SPEED_M_PER_S = 2.0
DPAD_STEP_M = 0.1

# -----------------------------------------------------------------------------
# OSC settings
# -----------------------------------------------------------------------------
#
# This script listens for messages from Unreal on OSC_LISTEN_PORT
# and sends the responses to Unreal at UNREAL_IP:UNREAL_PORT.
# Both ports must match the OSC settings in Unreal.

OSC_LISTEN_IP = "127.0.0.1"  # accept messages from this computer only
OSC_LISTEN_PORT = 8000

UNREAL_IP = "127.0.0.1"  # Unreal runs on this computer
UNREAL_PORT = 8001

# Unreal -> Python: a sound was played, the participant may respond.
OSC_START_ADDRESS = "/lighttrack/start"

# Unreal -> Python: the experiment is over.
OSC_END_ADDRESS = "/lighttrack/end"

# Python -> Unreal: the confirmed response distance in metres.
OSC_RESPONSE_ADDRESS = "/lighttrack/response"


def start_osc_server(messages):
    """
    Listen for OSC messages from Unreal in the background.

    Each message is put into the `messages` queue, where the main loop
    picks it up.
    """

    def on_start(address, *args):
        messages.put("start")

    def on_end(address, *args):
        messages.put("end")

    dispatcher = Dispatcher()
    dispatcher.map(OSC_START_ADDRESS, on_start)
    dispatcher.map(OSC_END_ADDRESS, on_end)

    server = ThreadingOSCUDPServer((OSC_LISTEN_IP, OSC_LISTEN_PORT), dispatcher)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    return server


def wait_for_unreal(messages):
    """Wait until the next OSC message from Unreal arrives."""

    while True:

        # Keep reading the controller so its state stays up to date.
        pygame.event.pump()

        try:
            return messages.get(timeout=0.01)
        except queue.Empty:
            pass


def get_response(track, controller, position_m):
    """
    Wait until the participant confirms a LightTrack response.

    The current marker position is passed into this function and returned
    again, so the marker can stay at the same position between trials.
    """

    previous_dpad = 0

    # A button that is already held when the trial starts does not count.
    # The participant has to press it again.
    previous_a = controller.get_button(0)

    last_time = time.monotonic()

    while True:

        pygame.event.pump()

        # Time since the previous controller update.
        now = time.monotonic()
        dt = now - last_time
        last_time = now

        # Left joystick: continuous movement.
        y = controller.get_axis(1)

        # Ignore small joystick movements around the centre.
        if abs(y) < 0.08:
            y = 0

        position_m -= y * JOYSTICK_SPEED_M_PER_S * dt

        # D-pad: fixed movement steps.
        dpad_y = controller.get_hat(0)[1]

        if dpad_y != 0 and dpad_y != previous_dpad:
            position_m += dpad_y * DPAD_STEP_M

        previous_dpad = dpad_y

        # Keep the marker inside the response track.
        position_m = max(
            TRACK_START_M,
            min(TRACK_END_M, position_m),
        )

        # Update the visible marker.
        # The marker snaps to the nearest LED, but position_m keeps the exact
        # value, so slow joystick movements add up until the next LED is reached.
        shown_m = track.show(position_m)

        # Xbox A confirms the current response.
        a_pressed = controller.get_button(0)

        if a_pressed and not previous_a:

            track.confirm()
            time.sleep(0.2)

            # Return the marker to red for the next trial.
            track.show(shown_m)

            return shown_m

        previous_a = a_pressed

        time.sleep(0.01)


def main():

    # Start controller support.
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        raise RuntimeError("No controller detected.")

    controller = pygame.joystick.Joystick(0)
    controller.init()

    # Connect to LightTrack.
    track = LightTrack(
        PORT,
        TRACK_START_M,
        TRACK_END_M,
        LEDS_PER_M,
    )

    # Connect to Unreal.
    messages = queue.Queue()
    server = start_osc_server(messages)
    unreal = SimpleUDPClient(UNREAL_IP, UNREAL_PORT)

    # Make sure a marker is visible before the first trial.
    position_m = INITIAL_POSITION_M
    position_m = track.show(position_m)

    try:

        trial = 0

        print(f"Waiting for Unreal on port {OSC_LISTEN_PORT}...")

        while True:

            message = wait_for_unreal(messages)

            if message == "end":
                print("Unreal ended the experiment.")
                break

            trial += 1
            print(f"Trial {trial}")

            # Wait for the participant's LightTrack response.
            position_m = get_response(
                track,
                controller,
                position_m,
            )
            response_m = round(position_m, 3)

            # Tell Unreal the response, so it can save it and play the next sound.
            unreal.send_message(OSC_RESPONSE_ADDRESS, response_m)

            print(f"Response: {response_m:.2f} m")
            print()

    finally:

        # Turn off the track and close connections.
        server.shutdown()
        server.server_close()
        track.clear()
        track.close()
        pygame.quit()


if __name__ == "__main__":
    main()
