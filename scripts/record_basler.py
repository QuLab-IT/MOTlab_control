#!/usr/bin/env python3
"""
Basler Camera Recording Script
Records video from a connected Basler camera using pypylon library
and saves it to the output directory with timestamp.
"""

import os
import sys
import time
import cv2
import numpy as np
from datetime import datetime
from pypylon import pylon

def create_output_directory():
    """Create output directory if it doesn't exist."""
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def initialize_camera():
    """Initialize and configure the Basler camera."""
    try:
        # Create an instant camera object with the first available camera device
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        
        # Print camera information
        print(f"Using device: {camera.GetDeviceInfo().GetModelName()}")
        print(f"Camera serial number: {camera.GetDeviceInfo().GetSerialNumber()}")
        
        # Open the camera
        camera.Open()
        # Set camera parameters for optimal video recording
        camera.MaxNumBuffer = 10
        
        # Set pixel format (try to set, skip if not available)
        try:
            camera.PixelFormat.SetValue(pylon.PixelType_BGR8packed)
        except Exception as e:
            print(f"Could not set pixel format: {e}")
        print(f"Camera opened")
        
        # Set acquisition mode to continuous
        try:
            camera.AcquisitionMode.SetValue(pylon.AcquisitionMode_Continuous)
        except Exception as e:
            print(f"Could not set acquisition mode: {e}")
        
        # Enable frame rate control if available
        try:
            camera.AcquisitionFrameRateEnable.SetValue(True)
            camera.AcquisitionFrameRate.SetValue(30.0)  # Set to 30 FPS
        except Exception as e:
            print(f"Could not set frame rate: {e}")
        
        return camera
        
    except Exception as e:
        print(f"Error initializing camera: {e}")
        return None

def record_video(camera, output_path, duration=10):
    """Record video from the camera and save to file."""
    try:
        # Get camera properties for video writer
        width = camera.Width.GetValue()
        height = camera.Height.GetValue()
        fps = 30.0  # Default FPS
        
        # Try to get actual frame rate if available
        try:
            fps = camera.AcquisitionFrameRate.GetValue()
        except Exception:
            # If we can't read the frame rate, keep the default
            pass
        
        print(f"Recording video: {width}x{height} at {fps} FPS")
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Create image converter
        converter = pylon.ImageFormatConverter()
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        
        # Start grabbing
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        
        start_time = time.time()
        frame_count = 0
        
        print(f"Recording for {duration} seconds...")
        print("Press Ctrl+C to stop recording early")
        
        while camera.IsGrabbing():
            # Check if duration has elapsed
            if time.time() - start_time > duration:
                break
                
            # Grab an image
            grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            
            if grabResult.GrabSucceeded():
                # Convert to OpenCV format
                image = converter.Convert(grabResult)
                img_array = image.GetArray()
                
                # Write frame to video file
                out.write(img_array)
                frame_count += 1
                
                # Print progress every 30 frames
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    print(f"Recorded {frame_count} frames in {elapsed:.1f}s")
            
            grabResult.Release()
        
        # Clean up
        camera.StopGrabbing()
        out.release()
        
        elapsed_time = time.time() - start_time
        print(f"\nRecording complete!")
        print(f"Total frames recorded: {frame_count}")
        print(f"Total time: {elapsed_time:.1f} seconds")
        print(f"Average FPS: {frame_count / elapsed_time:.1f}")
        print(f"Video saved to: {output_path}")
        
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
        camera.StopGrabbing()
        out.release()
        
    except Exception as e:
        print(f"Error during recording: {e}")
        if camera.IsGrabbing():
            camera.StopGrabbing()
        if 'out' in locals():
            out.release()

def main():
    """Main function to run the recording script."""
    print("Basler Camera Recording Script")
    print("=" * 40)
    
    # Create output directory
    output_dir = create_output_directory()
    print(f"Output directory: {output_dir}")
    
    # Initialize camera
    print("\nInitializing camera...")
    camera = initialize_camera()
    
    if camera is None:
        print("Failed to initialize camera. Exiting.")
        sys.exit(1)
    
    try:
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"basler_recording_{timestamp}.avi"
        output_path = os.path.join(output_dir, output_filename)
        
        # Get recording duration from user or use default
        duration = 10  # Default 10 seconds
        try:
            user_input = input(f"\nEnter recording duration in seconds (default: {duration}): ")
            if user_input.strip():
                duration = float(user_input)
        except ValueError:
            print("Invalid input, using default duration")
        
        # Start recording
        print(f"\nStarting recording...")
        record_video(camera, output_path, duration)
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        # Clean up
        if camera.IsOpen():
            camera.Close()
        print("\nCamera closed successfully")

if __name__ == "__main__":
    main()
