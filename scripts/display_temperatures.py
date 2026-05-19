import csv
import json
import sys
import time
from datetime import datetime

import matplotlib.pyplot as plt
from utils import (initialize_serial_connection, load_config,
                   read_temperature_data)

if __name__ == "__main__":
    plt.ion()  # Interactive mode

    # Load configuration
    config = load_config()
    temp_sensor_port = config.get('temperature_sensor_port')

    if not temp_sensor_port:
        print("Error: 'temperature_sensor_port' not found in config.json")
        sys.exit(1)

    # Initialize connection
    ser = initialize_serial_connection(temp_sensor_port)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Temperature plot
    temp_line, = ax.plot([], [], label='Temperature')
    ax.set_ylim(0, 120)  # Temperature range
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Temperature (°C)')
    ax.legend()

    # Data storage
    temps = []
    temperature_times = []
    time.sleep(10)
    # CSV file for storage
    with open('temperature_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time', 'Temperature'])
        
        print("Starting data collection...")
        while True:
            try:
                current_time = datetime.now()
                # Read temperature data
                temp_value = read_temperature_data(ser)[0]
                print(temp_value)
                
                temperature_times.append(current_time)
                temps.append(temp_value)
                
                # Convert times to seconds for plotting
                time_seconds = [(t - temperature_times[0]).total_seconds() for t in temperature_times]
                
                # Update temperature plot
                temp_line.set_data(time_seconds, temps)
                ax.set_xlim(min(time_seconds), max(time_seconds))
                ax.set_ylim(min(temps) - 5, max(temps) + 5)
                
                # Redraw the plot
                fig.canvas.draw()
                fig.canvas.flush_events()
                
                # Save to CSV
                writer.writerow([current_time, temp_value])
                f.flush()
                print(f"Data saved: {current_time} - Temperature {temp_value}")
                        
            except KeyboardInterrupt:
                print("\nStopping data collection...")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                time.sleep(1)  # Prevent tight loop on error
                
    ser.close()
    print("Connection closed")