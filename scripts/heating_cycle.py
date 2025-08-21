import csv
import matplotlib.pyplot as plt
import time
import sys

from datetime import datetime
from instrumental.drivers.vacuum.ngc import NGC2D, Gauge, GaugeSelection
from utils import initialize_pressure_gauge, initialize_relay, initialize_serial_connection, load_config, read_temperature_data

def initialize_plot():
    plt.ion()  # Interactive mode
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # Temperature plot
    thermistors = [
        "Sublimation pump",
        "Chamber sleeve",
        "Bellow sleeve",
        "Metal interface",
        "Ion pump",
        "Quartz cube",
    ]

    temp_lines = [ax1.plot([], [], label=thermistors[i])[0] for i in range(6)]
    ax1.set_ylim(0, 100)  # Temperature range
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Temperature (°C)')
    ax1.legend()
    
    # Pressure plot
    pressure_line, = ax2.plot([], [], label='Pressure')
    ax2.set_yscale('log')  # Use log scale for pressure
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Pressure (mbar)')
    ax2.legend()

    return fig, (ax1, ax2), (pressure_line, temp_lines)

def progress_plot(pressure, temp_values, time_seconds, pressures, pressure_line, temps, temp_lines, ax1, ax2, fig):
    if pressure:
        # Update pressure data
        pressures.append(pressure)
        pressure_line.set_data(time_seconds, pressures)
        # Update pressure plot
        ax2.set_xlim(min(time_seconds), max(time_seconds))
        ax2.set_ylim(min(pressures) * 0.1, max(pressures) * 10)

    if temp_values:
        # Update temperature data
        for i in range(6):
            temps[i].append(temp_values[i])
        
        # Update temperature plot
        for i in range(6):
            temp_lines[i].set_data(time_seconds, temps[i])
        ax1.set_xlim(min(time_seconds), max(time_seconds))
        ax1.set_ylim(min(min(t) for t in temps) - 5, max(max(t) for t in temps) + 5)
        
        # Redraw the plot
        fig.canvas.draw()
        fig.canvas.flush_events()


def progress_relay_control(current_pressure, current_temperatures, goal_temperature, max_pressure, current_setpoint, chamber_relay, bellow_relay, heater_chamber_on, heater_bellow_on):
    
    cube_temperature = current_temperatures[5]
    interface_metal_temperature = current_temperatures[3] - 8 #make a bit higher
    ion_pump_temperature = current_temperatures[4] - 2
    sublimaton_pump_temperature = current_temperatures[0] - 5 #too agressive 
    Delta_hysteresis_bellow = - 45 #since the bellow heats up so fast
    bellow_sleeve_temperature = current_temperatures[2] - Delta_hysteresis_bellow
    Delta_hysteresis= 5 # Hysteresis for the sleeve temperature
    chamber_sleeve_temperature = current_temperatures[1] - Delta_hysteresis

    chamber_temperatures = [
        cube_temperature, 
        interface_metal_temperature, 
        ion_pump_temperature, 
        sublimaton_pump_temperature,
    ]
   
    chamber_heating_condition = (
        current_pressure < max_pressure and # Pressure low enough
        chamber_sleeve_temperature < goal_temperature and 
        max(chamber_temperatures) < goal_temperature and # Goal temperature is not reached
        all(temp < current_setpoint for temp in chamber_temperatures) and # Step temperature is not reached
        abs(cube_temperature - interface_metal_temperature) < 22 and # Interface temperature difference is too high
        max(current_temperatures) - min(chamber_temperatures) < 40 # Temperature difference is too high 
    )

    if chamber_heating_condition:
        if not heater_chamber_on:
            heater_chamber_on = True
            chamber_relay.turnOn()
            
    else:
        # Turn heater OFF if any temp is at or above the setpoint, or if goal is reached
        if heater_chamber_on:
            heater_chamber_on = False
            chamber_relay.turnOff()
           
    bellow_heating_condition = (
        bellow_sleeve_temperature < current_setpoint and # Bellow temperature is too low
        bellow_sleeve_temperature < goal_temperature and # Goal temperature is not reached
        current_pressure < max_pressure # Pressure is too high
    )

    if bellow_heating_condition:
        if not heater_bellow_on:
            heater_bellow_on = True
            bellow_relay.turnOn()
            # Allow time for the relay to stabilize
    else:
        # Turn heater OFF if any temp is at or above the setpoint, or if goal is reached
        if heater_bellow_on:
            heater_bellow_on = False
            bellow_relay.turnOff()
            # Allow time for the relay to stabilize
    
    return heater_chamber_on, heater_bellow_on


def run_heating_cycle(goal_temperature, max_pressure=1e-2, max_rate_c_per_min=1.0, time_step_s=0):
    """
    Runs a heating cycle with a controlled temperature ramp rate using real sensor data.

    Args:
        ser: Initialized serial connection object.
        goal_temperature: The final target temperature in degrees Celsius.
        initial_temperatures: A list of starting temperatures in degrees Celsius.
        max_rate_c_per_min: The maximum heating rate in degrees Celsius per minute.
        time_step_s: The simulation time step in seconds.
    """

    # Load configuration
    config = load_config()
    temp_sensor_port_cube = config.get('temperature_sensor_port_cube')
    temp_sensor_port_bellow = config.get('temperature_sensor_bellow')

    if not temp_sensor_port_cube:
        print("Error: 'temperature_sensor_port_cube' not found in config.json")
        sys.exit(1)

    if not temp_sensor_port_bellow:
        print("Error: 'temperature_sensor_port_bellow' not found in config.json")
        sys.exit(1)

    # Initialize connections
    ser_cube = initialize_serial_connection(temp_sensor_port_cube)
    ser_bellow = initialize_serial_connection(temp_sensor_port_bellow)
    
    pressure_gauge_port = config.get('pressure_gauge_port')
    
    if not pressure_gauge_port:
        print("Error: 'pressure_gauge_port' not found in config.json")
        sys.exit(1)

    ngc2d: NGC2D = initialize_pressure_gauge()
    
    fig, (ax1, ax2), (pressure_line, temp_lines) = initialize_plot()

    time.sleep(10)  # Allow time for the arduino to stabilize (I guess)

    current_temperatures = list(read_temperature_data(ser_cube)+read_temperature_data(ser_bellow))
    
    max_initial_temp = max(current_temperatures)
    print("Maximum initial temp:", max_initial_temp)
    start_time = time.time()

    print(f"Starting heating cycle. Goal: {goal_temperature}°C, Initial Max: {max_initial_temp}°C, Rate: {max_rate_c_per_min}°C/min")

    heater_chamber_on = False # Initial state
    heater_bellow_on = False # Initial state

    chamber_relay_ip = config.get('relay_main_chamber_ip')
    bellow_relay_ip = config.get('relay_bellow_ip')

    relays_email = config.get('relays_email')
    relays_password = config.get('relays_password')

    chamber_relay = initialize_relay(
        ip=chamber_relay_ip,
        email=relays_email,
        password=relays_password,
    )

    bellow_relay = initialize_relay(
        ip=bellow_relay_ip,
        email=relays_email,
        password=relays_password,
    )
 
    # Data storage
    times = []
    temps = [[], [], [], [], [], []]
    pressures = []

    with open('heating_cycle_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time', 'Chamber Temp', 'Bellow Temp', 'Pressure'])

        while (current_temperatures[5] < goal_temperature):
            elapsed_seconds = time.time() - start_time
            times.append(elapsed_seconds)

            elapsed_minutes = elapsed_seconds / 60.0

            # Calculate the target temperature based on the ramp rate, starting from the highest initial temp
            target_temperature_on_ramp = max_initial_temp + elapsed_minutes * max_rate_c_per_min

            # The actual setpoint cannot exceed the goal temperature
            current_setpoint = min(target_temperature_on_ramp, goal_temperature)

            ngc2_d_status = ngc2d.get_status()
            gauge: Gauge = next((g for g in ngc2_d_status.gauges if g.number == GaugeSelection.ION_GAUGE_1), None)
            pressure = gauge.pressure  # Get pressure in mbar

            if pressure:
                current_pressure = pressure
            else:
                print("Warning: Failed to read pressure. Using last known values.")
                # Optional: Add logic here to handle repeated read failures (e.g., stop the cycle)

            # Read current temperatures from the sensor
            new_temps = read_temperature_data(ser_cube) + read_temperature_data(ser_bellow)

            if new_temps:
                current_temperatures = new_temps
            else:
                print("Warning: Failed to read temperatures. Using last known values.")
                # Optional: Add logic here to handle repeated read failures (e.g., stop the cycle)

            if None not in [pressure_gauge_port, temp_sensor_port_cube]:
                progress_plot(pressure, current_temperatures, times, pressures, pressure_line, temps, temp_lines, ax1, ax2, fig)
               
            heater_chamber_on, heater_bellow_on = progress_relay_control(current_pressure, current_temperatures, goal_temperature, max_pressure, current_setpoint, chamber_relay, bellow_relay, heater_chamber_on, heater_bellow_on)
            
            max_chamber_temp = max(current_temperatures)
            
            # Format temperatures for printing
            temp_str = ", ".join([f"{t:.2f}°C" for t in current_temperatures])
            print(f"Time: {elapsed_seconds:.1f}s | Max Temp: {max_chamber_temp:.2f}°C | Setpoint: {current_setpoint:.2f}°C | Heater chamber: {'ON' if heater_chamber_on else 'OFF'} | Heater bellow: {'ON' if heater_bellow_on else 'OFF'} | Cube temp: {current_temperatures[5]:.2f}°C | Pressure: {pressure:.2e} mbar")
            writer.writerow([elapsed_seconds] + current_temperatures + [pressure])
            f.flush()
            #print(f"Data saved: Temperatures {current_temperatures}, Pressure {pressure:.2e} mbar")

            # Check if goal is reached by the maximum temperature
            
            if (current_temperatures[5] >= goal_temperature):
                # Ensure final print shows the exact goal temperature if overshot slightly
                current_temperatures = [min(t, goal_temperature) for t in current_temperatures]
                max_chamber_temp = goal_temperature
                elapsed_seconds = time.time() - start_time # Recalculate for final print
                temp_str = ", ".join([f"{t:.2f}°C" for t in current_temperatures])
                print(f"Time: {elapsed_seconds:.1f}s | Temps: [{temp_str}] | Max Temp: {max_chamber_temp:.2f}°C | Setpoint: {current_setpoint:.2f}°C | Heater: {'OFF'}")
                print(f"Goal temperature ({goal_temperature}°C) reached by maximum sensor.")
                break

            # Wait for the next time step
            time.sleep(time_step_s)
    
    #now run the heating cycle in "watch dog" mode: i.e. make sure all temps are ok.
    
    while(1):
        elapsed_seconds = time.time() - start_time
        times.append(elapsed_seconds)
            
        elapsed_minutes = elapsed_seconds / 60.0

        ngc2_d_status = ngc2d.get_status()
        gauge: Gauge = next((g for g in ngc2_d_status.gauges if g.number == GaugeSelection.ION_GAUGE_1), None)
        pressure = gauge.pressure  # Get pressure in mbar
            
        if pressure:
            current_pressure = pressure
        else:
            print("Warning: Failed to read pressure. Using last known values.")
            # Optional: Add logic here to handle repeated read failures (e.g., stop the cycle)

        # Read current temperatures from the sensor
        new_temps = read_temperature_data(ser_cube)+read_temperature_data(ser_bellow)

        if new_temps:
            current_temperatures = new_temps
        else:
            print("Warning: Failed to read temperatures. Using last known values.")
            # Optional: Add logic here to handle repeated read failures (e.g., stop the cycle)
        

        if None not in [pressure_gauge_port, temp_sensor_port_cube]:
            progress_plot(
                pressure,
                current_temperatures,
                times,
                pressures,
                pressure_line,
                temps,
                temp_lines,
                ax1,
                ax2,
                fig,
            )         
        
        Max_alloable_temp = goal_temperature + 10
        #watch dog mode: check if all temps are ok.
        cube_temperature = current_temperatures[5]
        interface_metal_temperature = current_temperatures[3]
        ion_pump_temperature = current_temperatures[4]
        sublimaton_pump_temperature = current_temperatures[0] + 5 #too agressive 
        Delta_hysteresis_bellow = - 35 #since the bellow heats up so fast
        bellow_sleeve_temperature = current_temperatures[2] - Delta_hysteresis_bellow
        Delta_hysteresis= 5 # Hysteresis for the sleeve temperature
        chamber_sleeve_temperature = current_temperatures[1] -Delta_hysteresis

        chamber_temperatures = [
            cube_temperature, 
            interface_metal_temperature, 
            ion_pump_temperature, 
            sublimaton_pump_temperature,
        ]
   
        chamber_heating_condition = (
            current_pressure < max_pressure and # Pressure low enough
            chamber_sleeve_temperature < Max_alloable_temp and 
            max(chamber_temperatures) < Max_alloable_temp and # Goal temperature is not reached
            abs(cube_temperature - interface_metal_temperature) < 30 and # Interface temperature difference is too high
            max(current_temperatures) - min(chamber_temperatures) < 40 # Temperature difference is too high
        )

        if chamber_heating_condition:
            if not heater_chamber_on:
                heater_chamber_on = True
                chamber_relay.turnOn()    
        else:
            # Turn heater OFF if any temp is at or above the setpoint, or if goal is reached
            if heater_chamber_on:
                heater_chamber_on = False
                chamber_relay.turnOff()

        bellow_heating_condition = (
            bellow_sleeve_temperature < goal_temperature and # Bellow temperature is too low
            bellow_sleeve_temperature < goal_temperature and # Goal temperature is not reached
            current_pressure < max_pressure # Pressure is too high
        )

        if bellow_heating_condition:
            if not heater_bellow_on:
                heater_bellow_on = True
                bellow_relay.turnOn()     
        else:
            # Turn heater OFF if any temp is at or above the setpoint, or if goal is reached
            if heater_bellow_on:
                heater_bellow_on = False
                bellow_relay.turnOff()
    

    # Ensure heater is off at the end
    if heater_chamber_on or heater_bellow_on:
        chamber_relay.turnOff()
        bellow_relay.turnOff()

    total_time_s = time.time() - start_time
    print(f"Heating cycle finished in {total_time_s:.1f} seconds ({total_time_s/60.0:.2f} minutes).")

if __name__ == "__main__":
    # --- Configuration --- 
    TARGET_TEMP_C = 120.0  # Final target temperature in Celsius
    # INITIAL_TEMP_C is now read from the sensor
    MAX_RAMP_RATE_C_MIN = 0.5 # Maximum heating rate in Celsius per minute
    SIMULATION_STEP_S = 0   # Update interval in seconds (adjust based on sensor read time)
    # ---------------------

    while True:
        ser = None
        try:
            run_heating_cycle(
                goal_temperature=TARGET_TEMP_C,
                max_rate_c_per_min=MAX_RAMP_RATE_C_MIN,
                time_step_s=SIMULATION_STEP_S
            )

        except KeyboardInterrupt:
            print("\nHeating cycle interrupted by user.")

            chamber_relay = initialize_relay("192.168.31.53", "labmottec@gmail.com", "MP2018-2023Laser")
            bellow_relay = initialize_relay("192.168.31.251", "labmottec@gmail.com", "MP2018-2023Laser")
            chamber_relay.turnOff()
            bellow_relay.turnOff()

        except Exception as e:
            print(f"An error occurred: {e}")
            
            chamber_relay = initialize_relay("192.168.31.53", "labmottec@gmail.com", "MP2018-2023Laser")
            bellow_relay = initialize_relay("192.168.31.251", "labmottec@gmail.com", "MP2018-2023Laser")
            chamber_relay.turnOff()
            bellow_relay.turnOff()

        finally:
            if ser and ser.is_open:
                ser.close()
                print("Serial port closed.")
                chamber_relay = initialize_relay("192.168.31.53", "labmottec@gmail.com", "MP2018-2023Laser")
                bellow_relay = initialize_relay("192.168.31.251", "labmottec@gmail.com", "MP2018-2023Laser")
                chamber_relay.turnOff()
                bellow_relay.turnOff()
                break
    
