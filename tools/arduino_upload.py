import argparse
import subprocess
import os
import sys
import platform
from pathlib import Path
import re


def get_required_libraries(sketch_path):
    """Analyze the sketch file to determine required libraries."""
    required_libraries = set()
    
    try:
        with open(sketch_path, 'r') as f:
            content = f.read()
            
        # Find all #include statements
        includes = re.findall(r'#include\s*[<"]([^>"]+)[>"]', content)
        
        # Map include names to library names and versions
        library_map = {
            'thermistor.h': {
                'name': 'ThermistorLibrary',
                'version': '1.0.6'  # Latest version from GitHub
            }
        }
        
        for include in includes:
            if include in library_map:
                lib_info = library_map[include]
                required_libraries.add(f"{lib_info['name']}@{lib_info['version']}")
            else:
                # If no mapping exists, use the include name as a fallback
                required_libraries.add(include.split('/')[0])
                
        return list(required_libraries)
        
    except Exception as e:
        print(f"Error analyzing sketch for libraries: {e}")
        return []


def install_arduino_cli():
    """Install arduino-cli if not present."""
    try:
        subprocess.run(["arduino-cli", "version"], capture_output=True, check=True)
        print("arduino-cli is already installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing arduino-cli...")
        if platform.system() == "Linux":
            # For Raspberry Pi
            install_script = "curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh"
            subprocess.run(install_script, shell=True, check=True)
            
            # Add arduino-cli to PATH if it's not already there
            if not os.path.exists(os.path.expanduser("~/.local/bin/arduino-cli")):
                print("Error: arduino-cli installation failed")
                sys.exit(1)
                
            # Add to PATH for current session
            os.environ["PATH"] = os.path.expanduser("~/.local/bin") + ":" + os.environ["PATH"]
        else:
            print("Please install arduino-cli manually for your system")
            sys.exit(1)


def install_required_libraries(sketch_path):
    """Install required libraries for the sketch."""
    required_libraries = get_required_libraries(sketch_path)
    
    if not required_libraries:
        print("No external libraries required for this sketch")
        return
        
    print(f"Required libraries: {', '.join(required_libraries)}")
    
    for library in required_libraries:
        try:
            print(f"Installing library: {library}")
            # First try to install from Arduino Library Manager
            subprocess.run([
                "arduino-cli",
                "lib",
                "install",
                library
            ], check=True)
            
            print(f"Library {library} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error installing library {library}: {e}")
            sys.exit(1)


def upload_sketch(sketch_path, port):
    """Upload a sketch to the Arduino."""
    try:
        # Update core index
        subprocess.run(["arduino-cli", "core", "update-index"], check=True)
        
        # Install Arduino 5 core
        subprocess.run([
            "arduino-cli",
            "core",
            "install",
            "arduino:avr"
        ], check=True)

        # Compile the sketch
        compile_cmd = [
            "arduino-cli",
            "compile",
            "--fqbn",
            "arduino:avr:mega:cpu=atmega2560",
            sketch_path,
        ]
        subprocess.run(compile_cmd, check=True)
        print("Sketch compiled successfully")

        # Upload the sketch
        upload_cmd = [
            "arduino-cli",
            "upload",
            "-p",
            port,
            "--fqbn",
            "arduino:avr:mega:cpu=atmega2560",
            sketch_path,
        ]
        subprocess.run(upload_cmd, check=True)
        print("Sketch uploaded successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error uploading sketch: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Upload Arduino sketch with required libraries")
    parser.add_argument(
        "--sketch_name",
        type=str,
        required=True,
        help="Name of the Arduino sketch (without .ino extension)"
    )
    parser.add_argument(
        "--port",
        type=str,
        required=True,
        help="Serial port where Arduino is connected (e.g., /dev/ttyACM0)"
    )
    args = parser.parse_args()

    # Verify sketch exists
    sketch_path = f"{args.sketch_name}/{args.sketch_name}.ino"
    if not os.path.exists(sketch_path):
        print(f"Error: Sketch file not found at {sketch_path}")
        sys.exit(1)

    # Install arduino-cli if needed
    install_arduino_cli()

    # Install required libraries
    install_required_libraries(sketch_path)

    # Upload the sketch
    success = upload_sketch(sketch_path, args.port)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
