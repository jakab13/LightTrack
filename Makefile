# LightTrack firmware helpers (requires arduino-cli).
# Board, core and library versions come from lighttrack/sketch.yaml.
#
#   make compile   build the firmware
#   make upload    build and flash to the connected board
#   make monitor   open the serial monitor (Ctrl-C to quit)
#   make flash     upload, then open the monitor
#   make ports     list connected boards
#
# The port is auto-detected; override with: make upload PORT=/dev/cu.usbmodem101

SKETCH := lighttrack
BAUD   := 115200
PORT   ?= $(shell arduino-cli board list | awk '/arduino:renesas_uno:nanor4/ {print $$1; exit}')

.PHONY: compile upload monitor flash ports check-port

compile:
	arduino-cli compile $(SKETCH)

upload: compile check-port
	arduino-cli upload -p $(PORT) $(SKETCH)

monitor: check-port
	arduino-cli monitor -p $(PORT) --config baudrate=$(BAUD)

flash: upload monitor

ports:
	arduino-cli board list

check-port:
	@test -n "$(PORT)" || { echo "No Nano R4 found. Plug it in or pass PORT=..."; exit 1; }
