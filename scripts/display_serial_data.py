import matplotlib.pyplot as plt
from datetime import datetime
import csv
import time
import sys
import json
from instrumental.drivers.vacuum.ngc import NGC2D, Gauge, GaugeSelection
from utils import read_temperature_data, initialize_serial_connection, initialize_pressure_gauge, load_config



if __name__ == "__main__":
    plt.ion()  # Interactive mode

    # Load configuration
    config = load_config()
    temp_sensor_port_cube = config.get('temperature_sensor_port_cube')
    temp_sensor_port_bellow = config.get('temperature_sensor_bellow')


    if not temp_sensor_port_cube :
        print("Error: 'temperature_sensor_port' not found in config.json")
        #sys.exit(1)

    if not temp_sensor_port_bellow :
        print("Error: 'temperature_sensor_bellow' not found in config.json")
        #sys.exit(1)

    
    # Initialize connections
    #ser_cube = initialize_serial_connection(temp_sensor_port_cube)
    #ser_bellow = initialize_serial_connection(temp_sensor_port_bellow)

    pressure_gauge_port = config.get('pressure_gauge_port')
    
    if not pressure_gauge_port:
        print("Error: 'pressure_gauge_port' not found in config.json")
        sys.exit(1)

    ngc2d: NGC2D = initialize_pressure_gauge()
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Temperature plot
    thermistors = ["Sublimation pump", "Chamber sleeve", "Bellow sleeve","Metal interface", "Ion gauge", "Quartz cube"]
    temp_lines = [ax1.plot([], [], label=thermistors[i])[0] for i in range(6)]
    ax1.set_ylim(0, 120)  # Temperature range
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Temperature (°C)')
    ax1.legend()
    
    # Pressure plot
    pressure_line, = ax2.plot([], [], label='Pressure')
    ax2.set_yscale('log')  # Use log scale for pressure
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Pressure (mbar)')
    ax2.legend()

    # Add text annotation for bakeout status
    bakeout_text = ax2.text(0.02, 0.95, '', transform=ax2.transAxes, 
                           bbox=dict(facecolor='white', alpha=0.8))

    # Data storage]
    temps = [[], [], [], [], [], []]
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
                # Read temperature data
                #temp_values = read_temperature_data(ser_cube)+read_temperature_data(ser_bellow)
                temp_values = [0,0,0,0,0,0]
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

                if None not in [temp_values, temp_sensor_port_bellow, temp_sensor_port_cube]:
                    temperature_times.append(current_time)
                    # Update temperature data
                    for i in range(6):
                        temps[i].append(temp_values[i])
                    
                    # Convert times to seconds for plotting
                    time_seconds = [(t - temperature_times[0]).total_seconds() for t in temperature_times]
                    
                    # Update temperature plot
                    for i in range(6):
                        temp_lines[i].set_data(time_seconds, temps[i])
                    ax1.set_xlim(min(time_seconds), max(time_seconds))
                    ax1.set_ylim(min(min(t) for t in temps) - 5, max(max(t) for t in temps) + 5)
                    
                    
                    # Redraw the plot
                    fig.canvas.draw()
                    fig.canvas.flush_events()                  
                # Save to CSV
                writer.writerow([current_time] + temp_values + [pressure])
                f.flush()
                print(f"Data saved: Temperatures {temp_values}, Pressure {pressure:.2e} mbar")
                        
            except KeyboardInterrupt:
                print("\nStopping data collection...")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                time.sleep(1)  # Prevent tight loop on error
                
    ser_cube.close()
    ser_bellow.close()
    ngc2d.close()
    print("Connections closed")