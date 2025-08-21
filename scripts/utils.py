import serial
import sys
import json
import time
from instrumental.drivers.vacuum.ngc import NGC2D
from PyP100 import PyP100



def load_config(config_path='config.json'):
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print(f"Loaded configuration from {config_path}")
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Configuration file '{config_path}' contains invalid JSON.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while reading the config file: {e}")
        sys.exit(1)
    

def initialize_serial_connection(port):
    try:
        ser = serial.Serial(
            port=port,
            baudrate=9600,
            timeout=1,
        )
        ser.reset_input_buffer()
        time.sleep(0.1)
        print(f"Successfully connected to serial port: {port}")
        return ser
    except serial.SerialException as e:
        print(f"Error opening serial port {port}: {e}")
        print("Please check if the device is connected and the port is correct in config.json")
        sys.exit(1)


def initialize_pressure_gauge() -> NGC2D:
    try:
        # Initialize the gauge
        gauge = NGC2D()
        print("Successfully connected to pressure gauge")
        return gauge
    except Exception as e:
        print(f"Error initializing pressure gauge: {e}")
        sys.exit(1)


def read_temperature_data(ser):
    """
    Request and read temperature data from serial port.
    Sends 'R' command, then reads and parses the response.
    Returns a list of 3 temperature values if successful, None otherwise.
    """
    try:
        ser.reset_input_buffer() # Clear any stale input
        ser.write(b'R')          # Send the read command as bytes
        line = ser.readline().decode('utf-8').strip()
        if not line:
            print(f"No data received from device on port {ser.port} after sending 'R'")
            return None

        try:
            # Split the line and convert to floats
            values = [float(x.strip()) for x in line.split(',')]
            
            if len(values) == 3:
                return values
            else:
                print(f"Warning: Expected 3 values from port {ser.port}, got {len(values)}")
                return None
                
        except ValueError as e:
            print(f"Error converting values to float from port {ser.port}: {e}")
            print(f"Problematic line from port {ser.port}: {line}")
            return None
            
    except Exception as e:
        print(f"Error communicating with serial port {ser.port}: {e}")
        return None
    

def initialize_relay(ip, email, password) -> PyP100.P100:
    relay =PyP100.P100(
        ip,
        email,
        password,
    )
    relay.handshake() #Creates the cookies required for further methods
    relay.login() #Sends credentials to the plug and creates AES Key and IV for further methods
    return relay