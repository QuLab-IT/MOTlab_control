# MOTlab_control
Python codes to communicate with Keysight AWG and Basler cameras. Used to run experiments on magneto-optical traps.

This repository keeps the Python codes (written in Python 3.6) used to manage the dataflow from and to Keysight arbitrary waveform generators (AWG), Techtronix oscilloscopes and Basler cameras. These equipments are used to run experiments on magneto-optical traps.  


To access the MOT's raspberry pi please access https://connect.raspberrypi.com/
The credential can be obtained from José Senart

# Requirements
Some of the scripts in this repository employ th Instrumental python lib, forked by our organization. To use it you must install a local version of the repo by going to https://github.com/QuLab-IT/Instrumental and following the local install steps.

//Create the virtual environment
python3 -m venv .venv

//Enable the virtual environment
source .venv/bin/activate

//Install the python environment 
python3 -m pip install -r requirements.txt

# Uploading Arduino sketches (`tools/arduino_upload.py`)
`tools/arduino_upload.py` compiles a sketch and uploads it to an Arduino Mega 2560 using [arduino-cli](https://arduino.github.io/arduino-cli/). It is meant to be run on the MOT's Raspberry Pi, so sketches can be updated remotely without the Arduino IDE.

Sketches live in `tools/`, one folder per sketch, with the `.ino` file named like its folder (the arduino-cli convention):

```
tools/
├── arduino_upload.py
└── read_temperatures/
    └── read_temperatures.ino   # replies with the thermistor temperature when it receives 'R' over serial (9600 baud)
```

## Usage
Run the script **from inside `tools/`**, since the sketch path is resolved relative to the current directory:

```bash
cd tools
python arduino_upload.py --sketch_name read_temperatures --port /dev/ttyACM0
```

- `--sketch_name`: folder name of the sketch, without `.ino` (the script looks for `<sketch_name>/<sketch_name>.ino`).
- `--port`: serial port the Arduino is connected to. On the Pi this is usually `/dev/ttyACM0`; run `arduino-cli board list` to check.

## What it does
1. Checks that `<sketch_name>/<sketch_name>.ino` exists.
2. Checks that `arduino-cli` is installed. On Linux it installs it automatically to `~/.local/bin`; on other systems you have to install it yourself.
3. Reads the `#include` lines in the sketch and installs the matching libraries with `arduino-cli lib install`. `thermistor.h` maps to `ThermistorLibrary@1.0.6`. Any other include is installed under its own name, which works only if that name is a real library in the Arduino Library Manager. For a new library, add an entry to `library_map` in `get_required_libraries()`.
4. Updates the core index and installs the `arduino:avr` core.
5. Compiles and uploads the sketch for the board `arduino:avr:mega:cpu=atmega2560`. To use a different board, change the FQBN in `upload_sketch()`.

The script exits with a non-zero status if any step fails.
