"""
Quick test: controller input and marker
---------------------------------------

Checks that the LightTrack connection, the controller and the LEDs work.

What it does:

    1. Connects to LightTrack (1 m to 20 m, 30 LEDs/m).
    2. Uses the first controller pygame finds.
       If there is none, it opens a small window and uses the keyboard:
       Up/Down arrows act like the joystick, Space acts like A.
    3. Shows a red marker in the middle of the track.
       The joystick (or Up/Down) moves it, the D-pad moves it in small steps.
    4. A (or Space) turns the marker green to confirm the position.
       It turns red again as soon as it moves.

Stop the script with Ctrl+C in the terminal or by closing the pygame window.
The LEDs are switched off when the script stops.
"""

import pygame

from lighttrack import LightTrack

TRACK_START_M = 1   # first LED, in metres from the participant
TRACK_END_M = 20    # last LED, in metres from the participant
SPEED_M_PER_S = 2.0 # marker speed with the joystick pushed all the way
DPAD_STEP_M = 0.1   # how far one D-pad press moves the marker
CHECKS_PER_S = 50   # how often the input is read

track = LightTrack("/dev/cu.usbmodem1101", TRACK_START_M, TRACK_END_M, 30) # 30 LEDs / m

# Use the first controller pygame can find, or the keyboard if there is none.
pygame.init()

if pygame.joystick.get_count() > 0:
    controller = pygame.joystick.Joystick(0)
    print("Controller:", controller.get_name())
else:
    controller = None

    # pygame only receives key presses while one of its own windows is
    # selected, so open a small one.
    window = pygame.display.set_mode((400, 100))
    pygame.display.set_caption("LightTrack: arrow keys to move, Space to confirm")
    window.fill((30, 30, 30))
    pygame.display.flip()
    print("No controller found, using the keyboard.")
    print("Click the pygame window, then use the arrow keys and Space.")

# Start with a red marker in the middle of the track.
position_m = (TRACK_START_M + TRACK_END_M) / 2
track.show(position_m)
print(f"Marker: {track.position_m:.2f} m")

moving = False
clock = pygame.time.Clock()

try:
    while True:
        old_position_m = position_m

        # Single presses arrive as events, so none of them gets lost.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Ctrl+C in the terminal or the window was closed.
                raise SystemExit

            elif event.type == pygame.WINDOWFOCUSLOST:
                print("The pygame window lost focus, click it to use the keyboard again.")

            elif event.type == pygame.WINDOWFOCUSGAINED:
                print("The pygame window has focus, the keyboard works.")

            elif (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or (
                event.type == pygame.JOYBUTTONDOWN and event.button == 0
            ):
                print(f"Confirmed: {track.confirm():.2f} m")

            elif event.type == pygame.JOYHATMOTION:
                # D-pad up is +1, down is -1.
                position_m += event.value[1] * DPAD_STEP_M

        # Held input moves the marker continuously.
        # Like the joystick, the Up arrow is negative.
        if controller is not None:
            stick_y = controller.get_axis(1)
        else:
            keys = pygame.key.get_pressed()
            stick_y = keys[pygame.K_DOWN] - keys[pygame.K_UP]

        # Ignore small joystick movements around the centre.
        if abs(stick_y) > 0.08:
            position_m -= stick_y * SPEED_M_PER_S / CHECKS_PER_S

        # Keep the marker on the track.
        position_m = max(TRACK_START_M, min(TRACK_END_M, position_m))

        if position_m != old_position_m:
            track.show(position_m)
            moving = True
        elif moving:
            # Print where the marker stopped, not every LED it passes.
            print(f"Marker: {track.position_m:.2f} m")
            moving = False

        clock.tick(CHECKS_PER_S)
finally:
    # Switch the LEDs off however the script stops.
    track.clear()
    track.close()
    pygame.quit()
