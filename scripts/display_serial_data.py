import csv
import json
import math
import sys
import time
from datetime import datetime

import matplotlib.pyplot as plt
from instrumental.drivers.vacuum.ngc import NGC2D, Gauge, GaugeSelection
from utils import (initialize_pressure_gauge, initialize_serial_connection,
                   load_config, read_temperature_data)

if __name__ == "__main__":
    plt.ion()  # Interactive mode

    # Load configuration
    config = load_config()
    temp_sensor_port_cube = config.get('temperature_sensor_port_cube')
    temp_sensor_port_bellow = config.get('temperature_sensor_bellow')

    if not temp_sensor_port_cube:
        print("Warning: 'temperature_sensor_port_cube' not found in config.json; cube sensor disabled")

    if not temp_sensor_port_bellow:
        print("Warning: 'temperature_sensor_bellow' not found in config.json; bellow sensor disabled")

    # Initialize serial connections only if ports are provided. Do not exit on failure; handle gracefully.
    ser_cube = None
    ser_bellow = None
    if temp_sensor_port_cube:
        try:
            ser_cube = initialize_serial_connection(temp_sensor_port_cube)
        except SystemExit:
            # initialize_serial_connection currently calls sys.exit on error; catch to continue running
            print(f"Could not open cube serial port {temp_sensor_port_cube}; continuing without cube sensor")
            ser_cube = None
    if temp_sensor_port_bellow:
        try:
            ser_bellow = initialize_serial_connection(temp_sensor_port_bellow)
        except SystemExit:
            print(f"Could not open bellow serial port {temp_sensor_port_bellow}; continuing without bellow sensor")
            ser_bellow = None

    temp_sensors_available = ser_cube is not None or ser_bellow is not None

    pressure_gauge_port = config.get('pressure_gauge_port')
    
    if not pressure_gauge_port:
        print("Error: 'pressure_gauge_port' not found in config.json")
        sys.exit(1)

    ngc2d: NGC2D = initialize_pressure_gauge()
    
    # Create figure with a temperature subplot only if a sensor is available
    if temp_sensors_available:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        # Temperature plot
        thermistors = ["Sublimation pump", "Chamber sleeve", "Bellow sleeve","Metal interface", "Ion gauge", "Quartz cube"]
        temp_lines = [ax1.plot([], [], label=thermistors[i])[0] for i in range(6)]
        ax1.set_ylim(0, 120)  # Temperature range
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Temperature (°C)')
        ax1.legend()
    else:
        fig, ax2 = plt.subplots(1, 1, figsize=(10, 8))

    # Pressure plot
    pressure_line, = ax2.plot([], [], label='Pressure')
    ax2.set_yscale('log')  # Use log scale for pressure
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Pressure (mbar)')
    ax2.legend()

    # Add text annotation for bakeout status
    bakeout_text = ax2.text(0.02, 0.95, '', transform=ax2.transAxes, 
                           bbox=dict(facecolor='white', alpha=0.8))

    # Data storage
    temps = [[] for _ in range(6)]
    temperature_times = []
    pressures = []
    pressure_times = []
    time.sleep(10)
    # CSV file for storage
    with open('temperature_pressure_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time', 'Sublimation pump', 'Chamber sleeve', 'Bellow sleeve','Metal interface', 'Ion gauge', 'Quartz cube', 'Pressure (mbar)'])
        
        print("Starting data collection...")
        while True:
            try:
                current_time = datetime.now()
                temp_values = [None] * 6
                if temp_sensors_available:
                    # Read temperature data from available sensors. Each serial read typically returns 3 values.
                    cube_vals = None
                    bellow_vals = None
                    if ser_cube:
                        try:
                            cube_vals = read_temperature_data(ser_cube)
                        except Exception as e:
                            print(f"Error reading cube sensor: {e}")
                            cube_vals = None
                    if ser_bellow:
                        try:
                            bellow_vals = read_temperature_data(ser_bellow)
                        except Exception as e:
                            print(f"Error reading bellow sensor: {e}")
                            bellow_vals = None

                    # Merge results: cube_vals -> last 3 indices (assumption), bellow_vals -> first 3 indices
                    # If only one sensor is present, fill its positions and leave others as None.
                    if bellow_vals:
                        for i, v in enumerate(bellow_vals[:3]):
                            temp_values[i] = v
                    if cube_vals:
                        for i, v in enumerate(cube_vals[:3]):
                            temp_values[3 + i] = v
                    print(temp_values)
                # Read pressure data
                # Read pressure data from NGC2D
                
                ngc2_d_status = ngc2d.get_status()
                gauge: Gauge = next((g for g in ngc2_d_status.gauges if g.number == GaugeSelection.ION_GAUGE_1), None)
                
                pressure = gauge.pressure  # Get pressure in mbar
                # unit = gauge.unit  # Get pressure in mbar
                controlling_bakeout = gauge.status.controlling_bakeout
                if controlling_bakeout is not None:
                    # Update bakeout status text
                    bakeout_status = "Bakeout: ON" if controlling_bakeout else "Bakeout: OFF"
                    bakeout_text.set_text(bakeout_status)
                
                if None not in [pressure, pressure_gauge_port]:
                    pressure_times.append(current_time)

                    # Convert times to seconds for plotting
                    time_seconds = [(t - pressure_times[0]).total_seconds() for t in pressure_times]

                    # Update pressure data
                    pressures.append(pressure)
                    pressure_line.set_data(time_seconds, pressures)
                    # Update pressure plot
                    ax2.set_xlim(min(time_seconds), max(time_seconds))
                    ax2.set_ylim(min(pressures) * 0.1, max(pressures) * 10)

                # Update temperature data if any sensor provided a reading
                if temp_sensors_available and any(v is not None for v in temp_values):
                    temperature_times.append(current_time)
                    # Append values (None when missing) to each sensor list to preserve alignment
                    for i in range(6):
                        temps[i].append(temp_values[i])

                    # Convert times to seconds for plotting
                    time_seconds = [(t - temperature_times[0]).total_seconds() for t in temperature_times]

                    # Update temperature plot; use NaN for missing values so lines break
                    for i in range(6):
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
                # Save to CSV
                writer.writerow([current_time] + temp_values + [pressure])
                f.flush()
                if temp_sensors_available:
                    print(f"Data saved: Temperatures {temp_values}, Pressure {pressure:.2e} mbar")
                else:
                    print(f"Data saved: Pressure {pressure:.2e} mbar")
                        
            except KeyboardInterrupt:
                print("\nStopping data collection...")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                time.sleep(1)  # Prevent tight loop on error
                
    # Close serial connections if they were opened
    try:
        if ser_cube:
            ser_cube.close()
    except Exception:
        pass
    try:
        if ser_bellow:
            ser_bellow.close()
    except Exception:
        pass
    ngc2d.close()
    print("Connections closed")