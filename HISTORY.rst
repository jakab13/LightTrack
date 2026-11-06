=======
History
=======

2.0.0 (2026-11-06)
==================

Fork by Tom Strobl at TU Berlin's Audio Communication Group, developed for an auditory distance experiment at the Faculty of Media Sciences of Mittweida University of Applied Sciences.

Firmware
--------

* Move the firmware into the ``lighttrack/`` sketch folder.
* Add an arduino-cli build setup with pinned board, core and library versions in ``lighttrack/sketch.yaml``.
* Add a ``Makefile`` with ``compile``, ``upload``, ``monitor``, ``flash`` and ``ports`` targets.
* Fix the marker lagging behind the joystick after long inputs.
  All waiting commands are now applied first and the strips are redrawn once with the latest state.

Hardware
--------

* Add the KiCad schematic and PCB of the controller carrier board for the Arduino Nano R4.
* Add the Blender model of the 3D-printed controller enclosure.

Software
--------

* Add ``quicktest.py``, which checks the connection, the controller and the LEDs.
* Add ``experiment_mittweida.py``, an auditory distance experiment that sends the responses via OSC.

Documentation
-------------

* Rework the README with photos of the finished controller, the schematic, wiring, a parts list and troubleshooting.

1.0.0 (2026-09-08)
==================

Original version by Jakab Pilaszanovich and Marc Schönwiesner at Leipzig University's Neurobiology Group (`jakab13/LightTrack <https://github.com/jakab13/LightTrack>`_).

* Arduino firmware ``lighttrack.ino`` driving two floor-mounted LED strips.
* Python interface ``lighttrack.py`` for moving a marker along the strips with an Xbox controller.
* ``experiment_example.py``, a small auditory distance-estimation example.
