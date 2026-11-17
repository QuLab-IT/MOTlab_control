import csv
import json
import math
import sys
import time
from datetime import datetime

import matplotlib.pyplot as plt
from utils import (initialize_serial_connection,
                   load_config, read_temperature_data)

if __name__ == "__main__":
    plt.ion()  # Interactive mode

    # Load configuration
    config = load_config()
    temp_sensor_port_bellow = config.get('temperature_sensor_bellow')

    if not temp_sensor_port_bellow:
        print("Warning: 'temperature_sensor_bellow' not found in config.json; bellow sensor disabled")

    # Initialize serial connections only if ports are provided. Do not exit on failure; handle gracefully.
    ser_bellow = None
    if temp_sensor_port_bellow:
        try:
            ser_bellow = initialize_serial_connection(temp_sensor_port_bellow)
        except SystemExit:
            print(f"Could not open bellow serial port {temp_sensor_port_bellow}; continuing without bellow sensor")
            ser_bellow = None

    temp_sensors_available = ser_bellow is not None



    # Create figure with a temperature subplot only if a sensor is available
    if temp_sensors_available:
        fig, (ax1) = plt.subplots(1, 1, figsize=(10, 8))

        # Temperature plot
        thermistors = ["Sublimation pump", "Chamber sleeve", "Bellow sleeve", "Quartz cube"]
        temp_lines = [ax1.plot([], [], label=thermistors[i])[0] for i in range(4)]
        ax1.set_ylim(0, 120)  # Temperature range
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Temperature (°C)')
        ax1.legend()

    # Data storage
    temps = [[] for _ in range(6)]
    temperature_times = []
    time.sleep(10)
    # CSV file for storage
    with open('temperature_multiple_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time', 'Sublimation pump', 'Chamber sleeve', 'Bellow sleeve','Quartz cube'])
        
        print("Starting data collection...")
        while True:
            try:
                current_time = datetime.now()
                temp_values = [None] * 4
                if temp_sensors_available:
                    # Read temperature data from available sensors. Each serial read typically returns 3 values.
                    bellow_vals = None
                    if ser_bellow:
                        try:
                            bellow_vals = read_temperature_data(ser_bellow)
                        except Exception as e:
                            print(f"Error reading bellow sensor: {e}")
                            bellow_vals = None

                    # Merge results: cube_vals -> last 3 indices (assumption), bellow_vals -> first 3 indices
                    # If only one sensor is present, fill its positions and leave others as None.
                    if bellow_vals:
                        for i, v in enumerate(bellow_vals[:4]):
                            temp_values[i] = v
                    print(temp_values)
                
                # Update temperature data if any sensor provided a reading
                if temp_sensors_available and any(v is not None for v in temp_values):
                    temperature_times.append(current_time)
                    # Append values (None when missing) to each sensor list to preserve alignment
                    for i in range(4):
#                        if(i==0):
#                            temp_values[0]-=50

                        temps[i].append(temp_values[i])

                    # Convert times to seconds for plotting
                    time_seconds = [(t - temperature_times[0]).total_seconds() for t in temperature_times]

                    # Update temperature plot; use NaN for missing values so lines break
                    for i in range(4):
                        ydata = [float(v) if v is not None else float('nan') for v in temps[i]]
                        temp_lines[i].set_data(time_seconds, ydata)

                    ax1.set_xlim(min(time_seconds), max(time_seconds))
                    # compute y-limits from available data
                    all_vals = [v for sensor in temps for v in sensor if v is not None]
                    if all_vals:
                        ax1.set_ylim(min(all_vals) - 5, max(all_vals) + 5)
                    else:
                        ax1.set_ylim(0, 120)

                # Redraw the plot
                fig.canvas.draw()
                fig.canvas.flush_events()
                f.flush()
                if temp_sensors_available:
                    print(f"Data saved: Temperatures {temp_values}")
                        
            except KeyboardInterrupt:
                print("\nStopping data collection...")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                time.sleep(1)  # Prevent tight loop on error
                
    # Close serial connections if they were opened
    try:
        if ser_bellow:
            ser_bellow.close()
    except Exception:
        pass
    print("Connections closed")
