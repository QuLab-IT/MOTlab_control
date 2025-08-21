#!/usr/bin/env python3
"""
Basler Camera Live View Script
Displays live video feed from a connected Basler camera using pypylon library
in a real-time OpenCV window.
"""

import os
import sys
import time
import cv2
import numpy as np
from pypylon import pylon

def initialize_camera():
    """Initialize and configure the Basler camera."""
    try:
        # Create an instant camera object with the first available camera device
        instance = pylon.TlFactory.GetInstance()
        print(f"Instance: {instance.EnumerateDevices()}")
        camera = pylon.InstantCamera(instance.CreateFirstDevice())
        
        # Print camera information
        print(f"Using device: {camera.GetDeviceInfo().GetModelName()}")
        print(f"Camera serial number: {camera.GetDeviceInfo().GetSerialNumber()}")
        
        # Open the camera
        camera.Open()
        
        # Set camera parameters for optimal live view
        camera.MaxNumBuffer = 5  # Smaller buffer for live view
        
        # Set pixel format (try to set, skip if not available)
        try:
            camera.PixelFormat.SetValue(pylon.PixelType_BGR8packed)
        except Exception as e:
            print(f"Could not set pixel format: {e}")
        
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
        
        # Get camera properties
        width = camera.Width.GetValue()
        height = camera.Height.GetValue()
        print(f"Camera resolution: {width}x{height}")
        
        return camera
        
    except Exception as e:
        print(f"Error initializing camera: {e}")
        return None

def display_live_view(camera):
    """Display live video feed from the camera."""
    try:
        # Create image converter
        converter = pylon.ImageFormatConverter()
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        
        # Start grabbing
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        
        # Create window
        window_name = "Basler Camera Live View"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        # Variables for FPS calculation
        frame_count = 0
        start_time = time.time()
        fps_update_interval = 30  # Update FPS every 30 frames
        
        print("\nLive view started!")
        print("Controls:")
        print("  - Press 'q' or ESC to quit")
        print("  - Press 'f' to toggle fullscreen")
        print("  - Press 's' to save current frame")
        
        fullscreen = False
        frame_save_count = 0
        
        while camera.IsGrabbing():
            # Grab an image
            grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            
            if grabResult.GrabSucceeded():
                # Convert to OpenCV format
                image = converter.Convert(grabResult)
                img_array = image.GetArray()
                
                # Calculate and display FPS
                frame_count += 1
                if frame_count % fps_update_interval == 0:
                    elapsed_time = time.time() - start_time
                    fps = fps_update_interval / elapsed_time
                    
                    # Add FPS text to image
                    img_display = img_array.copy()
                    cv2.putText(img_display, f"FPS: {fps:.1f}", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Add frame counter
                    cv2.putText(img_display, f"Frame: {frame_count}", (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Add controls info
                    cv2.putText(img_display, "Press 'q' to quit", (10, img_display.shape[0] - 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(img_display, "Press 'f' for fullscreen", (10, img_display.shape[0] - 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    start_time = time.time()
                else:
                    img_display = img_array
                
                # Display the image
                cv2.imshow(window_name, img_display)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or key == 27:  # 'q' or ESC key
                    print("Exiting live view...")
                    break
                elif key == ord('f'):  # 'f' key for fullscreen toggle
                    fullscreen = not fullscreen
                    if fullscreen:
                        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                        print("Switched to fullscreen mode")
                    else:
                        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                        print("Switched to windowed mode")
                elif key == ord('s'):  # 's' key to save frame
                    frame_save_count += 1
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    output_dir = os.path.join(os.path.dirname(__file__), "output")
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    
                    filename = f"basler_frame_{timestamp}_{frame_save_count:03d}.jpg"
                    filepath = os.path.join(output_dir, filename)
                    cv2.imwrite(filepath, img_array)
                    print(f"Frame saved to: {filepath}")
            
            grabResult.Release()
        
        # Clean up
        camera.StopGrabbing()
        cv2.destroyAllWindows()
        
        print(f"\nLive view ended after {frame_count} frames")
        
    except KeyboardInterrupt:
        print("\nLive view interrupted by user")
        camera.StopGrabbing()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error during live view: {e}")
        if camera.IsGrabbing():
            camera.StopGrabbing()
        cv2.destroyAllWindows()

def main():
    """Main function to run the live view script."""
    print("Basler Camera Live View")
    print("=" * 30)
    
    # Initialize camera
    print("Initializing camera...")
    camera = initialize_camera()
    
    if camera is None:
        print("Failed to initialize camera. Exiting.")
        sys.exit(1)
    
    try:
        # Start live view
        display_live_view(camera)
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        # Clean up
        if camera.IsOpen():
            camera.Close()
        print("Camera closed successfully")

if __name__ == "__main__":
    main() 



