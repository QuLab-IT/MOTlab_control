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
from pypylon import pylon

# ...existing code...
def initialize_camera():
    """Initialize and configure the Basler camera."""
    try:
        # Create an instant camera object with the chosen camera device
        instance = pylon.TlFactory.GetInstance()
        devices = instance.EnumerateDevices()
        if not devices:
            print("No Basler cameras found.")
            return None

        # If multiple devices, let the user select which one to use
        if len(devices) > 1:
            print("Multiple cameras found:")
            for idx, dev in enumerate(devices):
                try:
                    model = dev.GetModelName()
                except Exception:
                    model = "<unknown model>"
                try:
                    serial = dev.GetSerialNumber()
                except Exception:
                    serial = "<unknown serial>"
                print(f"  [{idx}] {model} (S/N: {serial})")

            # Prompt user until valid selection
            selected = None
            while selected is None:
                try:
                    choice = input(f"Select camera index [0-{len(devices)-1}] (default 0): ").strip()
                    if choice == "":
                        selected = 0
                    else:
                        ival = int(choice)
                        if 0 <= ival < len(devices):
                            selected = ival
                        else:
                            print("Index out of range.")
                except ValueError:
                    print("Please enter a valid integer index.")
        else:
            selected = 0
            dev = devices[0]
            try:
                print(f"Found one camera: {dev.GetModelName()} (S/N: {dev.GetSerialNumber()})")
            except Exception:
                pass

        # Create camera from selected device
        selected_device = devices[selected]
        camera = pylon.InstantCamera(instance.CreateDevice(selected_device))

        # Print camera information
        try:
            print(f"Using device: {camera.GetDeviceInfo().GetModelName()}")
            print(f"Camera serial number: {camera.GetDeviceInfo().GetSerialNumber()}")
        except Exception:
            pass

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
        # Prepare exposure control (best-effort). Many Basler cameras expose
        # exposure as `ExposureTime`. Try to disable auto exposure and read
        # min/max/current values if available.
        exposure_supported = False
        exp_val = None
        exp_min = None
        exp_max = None
        try:
            if hasattr(camera, "ExposureAuto"):
                try:
                    camera.ExposureAuto.SetValue("Off")
                except Exception:
                    try:
                        camera.ExposureAuto.SetValue(pylon.ExposureAuto_Off)
                    except Exception:
                        pass

            if hasattr(camera, "ExposureTime"):
                try:
                    exp_val = camera.ExposureTime.GetValue()
                    exp_min = camera.ExposureTime.GetMin()
                    exp_max = camera.ExposureTime.GetMax()
                except Exception:
                    # Some cameras may not provide min/max or may raise
                    exp_min = None
                    exp_max = None

                exposure_supported = True
                print(f"Exposure control available. Current: {exp_val}")
        except Exception as e:
            print(f"Exposure control not available: {e}")
        
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
                    
                    # Add controls info (include exposure controls)
                    cv2.putText(img_display, "Press 'q' to quit", (10, img_display.shape[0] - 110), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.putText(img_display, "Press 'f' for fullscreen", (10, img_display.shape[0] - 80), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.putText(img_display, "Press 's' to save frame", (10, img_display.shape[0] - 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.putText(img_display, "Press '[' / ']' to decrease / increase exposure", (10, img_display.shape[0] - 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
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
                elif key == ord(']'):
                    print("Increasing exposure...")
                    # Increase exposure (best-effort)
                    if exposure_supported and exp_val is not None:
                        try:
                            new_exp = int(exp_val * 1.2)
                            if exp_max is not None:
                                new_exp = min(new_exp, exp_max)
                            camera.ExposureTime.SetValue(new_exp)
                            exp_val = camera.ExposureTime.GetValue()
                            print(f"Exposure increased -> {exp_val}")
                        except Exception as e:
                            print(f"Could not increase exposure: {e}")
                    else:
                        print("Exposure adjustment not supported on this camera.")
                elif key == ord('['):
                    # Decrease exposure (best-effort)
                    if exposure_supported and exp_val is not None:
                        try:
                            new_exp = int(max(1, exp_val / 1.2))
                            if exp_min is not None:
                                new_exp = max(new_exp, exp_min)
                            camera.ExposureTime.SetValue(new_exp)
                            exp_val = camera.ExposureTime.GetValue()
                            print(f"Exposure decreased -> {exp_val}")
                        except Exception as e:
                            print(f"Could not decrease exposure: {e}")
                    else:
                        print("Exposure adjustment not supported on this camera.")
            
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



