"""
Example auditory distance experiment
------------------------------------

This is a small example showing how LightTrack can be used as a response tool.

Each trial follows the same structure:

    1. Generate a sound at a simulated distance.
    2. Play the sound.
    3. Let the participant move the LightTrack marker.
    4. Press A to confirm the response.
    5. Save stimulus distance and response distance.

The marker stays visible throughout the experiment.

The sound simulation is only an example and is not intended to reproduce
a specific auditory-distance experiment.
"""

import csv
import random
import time

import pygame
import slab

from lighttrack import LightTrack


# -----------------------------------------------------------------------------
# Experiment settings
# -----------------------------------------------------------------------------
#
# These are the values a new user is most likely to change.

PORT = "COM5"

TRACK_START_M = 1.0
TRACK_END_M = 13.0
LEDS_PER_M = 30

# Position of the marker when the experiment starts.
INITIAL_POSITION_M = 7.0

# Distances used for the mock sound stimuli.
STIMULUS_DISTANCES_M = [2, 4, 6, 8, 10, 12]
N_TRIALS = 6

# Controller sensitivity.
JOYSTICK_SPEED_M_PER_S = 2.0
DPAD_STEP_M = 0.1


# -----------------------------------------------------------------------------
# Virtual room
# -----------------------------------------------------------------------------
#
# slab.Room creates a simple binaural room simulation.
# The source distance will be changed on each trial.

room = slab.Room(
    size=[30, 30, 4],
    listener=[15, 15, 1.5],
    source=[0, 0, 2],
    absorption=[0.15],
)


def make_stimulus(distance_m):
    """
    Create a short sound at a simulated distance.

    The room response changes with source distance, adding reflections
    and reverberation. Overall level is then equalised so that distance
    is not represented only by loudness.
    """

    # Source format: [azimuth, elevation, distance]
    room.set_source([0, 0, distance_m])

    # Generate the binaural room impulse response.
    hrir = room.hrir(trim=0.25)

    # Create a short broadband sound.
    sound = slab.Sound.pinknoise(
        duration=0.3,
        samplerate=hrir.samplerate,
    )
    sound = sound.ramp(duration=0.01)

    # Apply the room acoustics.
    stimulus = hrir.apply(sound)

    # Keep overall level constant across distances.
    stimulus.level = 70

    return stimulus


def get_response(track, controller, position_m):
    """
    Wait until the participant confirms a LightTrack response.

    The current marker position is passed into this function and returned
    again, so the marker can stay at the same position between trials.
    """

    previous_dpad = 0
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
        position_m = track.show(position_m)

        # Xbox A confirms the current response.
        if controller.get_button(0):

            track.confirm()
            time.sleep(0.2)

            # Wait until the button is released.
            while controller.get_button(0):
                pygame.event.pump()
                time.sleep(0.01)

            # Return the marker to red for the next trial.
            track.show(position_m)

            return position_m

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

    # Make sure a marker is visible before the first trial.
    position_m = INITIAL_POSITION_M
    position_m = track.show(position_m)

    results = []

    try:

        for trial in range(1, N_TRIALS + 1):

            # Choose a mock stimulus distance.
            target_m = random.choice(STIMULUS_DISTANCES_M)

            print(f"Trial {trial}/{N_TRIALS}")

            # Create and play the sound.
            stimulus = make_stimulus(target_m)
            stimulus.play()

            # Wait for the participant's LightTrack response.
            position_m = get_response(
                track,
                controller,
                position_m,
            )

            # Save the stimulus and response.
            results.append({
                "trial": trial,
                "stimulus_distance_m": target_m,
                "response_distance_m": round(position_m, 3),
            })

            print(f"Response: {position_m:.2f} m")
            print()

            time.sleep(0.5)

    finally:

        # Turn off the track and close connections.
        track.clear()
        track.close()
        pygame.quit()

    # Save all trials to a simple CSV file.
    with open("results.csv", "w", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "trial",
                "stimulus_distance_m",
                "response_distance_m",
            ],
        )

        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    main()
