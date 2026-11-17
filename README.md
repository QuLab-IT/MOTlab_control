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

//If arduino-cli shows FQBN Unknown on your arduino, please list and install your arduino FQBN, like so:

```sh
arduino-cli core search uno  //The uno in the end is just a string. Replace it by your board name, but arduino-cli will return every arduino FQBN connected, even if not installed

arduino-cli core install arduino:megaavr        //Arduino used in this setuup, it may change! The package is returned with the command above!
```

//Also, you need to verify and change the USB port denomination in the config.json that corresponds to your arduino

//To check which port is your arduino at please run the following command:
usb-1a86 -> Arduino
usb-Prolific\_Technology\_Inc -> Pressure sensor

//The configuration file is located at:
scripts/config.json


# Uploading Arduino sketches (`tools/arduino_upload.py`)
`tools/arduino_upload.py` compiles a sketch and uploads it to an Arduino Mega 2560 using [arduino-cli](https://arduino.github.io/arduino-cli/). It is meant to be run on the MOT's Raspberry Pi, so sketches can be updated remotely without the Arduino IDE.

Sketches live in `tools/`, one folder per sketch, with the `.ino` file named like its folder (the arduino-cli convention):

```
tools/
├── arduino_upload.py
└── read_temperatures/
    └── read_temperatures.ino   # replies with the thermistor temperature when it receives 'R' over serial (9600 baud)
```

## Usage to upload the script to arduino
Run the script **from inside `tools/`**, since the sketch path is resolved relative to the current directory:

```bash
python3 arduino_upload.py --sketch_name read_temperatures --port /dev/ttyACM0
```

- `--sketch_name`: folder name of the sketch, without `.ino` (the script looks for `<sketch_name>/<sketch_name>.ino`).
- `--port`: serial port the Arduino is connected to. On the Pi this is usually `/dev/ttyACM0`; run `arduino-cli board list` to check.

## Usage to connect the raspberry and arduino, and read the arduino messages

```sh
cd ~/CODE/Motlab_control/scripts
python3 display_multiple_temperatures.py
```


