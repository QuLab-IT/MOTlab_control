"""
Unified Basler Camera Utilities for MOTlab Control.

This module provides common functions for initializing and configuring
Basler cameras across different scripts in the MOTlab control system.
"""

import os
import time
from typing import Optional, Tuple

import cv2
import numpy as np
from pypylon import pylon


class BaslerCameraError(Exception):
    """Custom exception for Basler camera related errors."""
    pass


def initialize_basler_camera(
    max_buffer_size: int = 10,
    pixel_format: str = "BGR8packed",
    fps: float = 30.0,
    acquisition_mode: str = "Continuous"
) -> Optional[pylon.InstantCamera]:
    """
    Initialize and configure a Basler camera with specified parameters.
    
    Args:
        max_buffer_size: Maximum number of buffers for frame storage
        pixel_format: Pixel format for the camera ("BGR8packed", "Mono8", etc.)
        fps: Target frames per second
        acquisition_mode: Acquisition mode ("Continuous", "SingleFrame")
        
    Returns:
        Initialized camera object or None if initialization fails
        
    Raises:
        BaslerCameraError: If camera initialization fails
    """
    try:
        # Create an instant camera object with the first available camera device
        instance = pylon.TlFactory.GetInstance()
        available_devices = instance.EnumerateDevices()
        
        if not available_devices:
            raise BaslerCameraError("No Basler cameras found")
        
        camera = pylon.InstantCamera(instance.CreateFirstDevice())
        
        # Print camera information
        print(f"Using device: {camera.GetDeviceInfo().GetModelName()}")
        print(f"Camera serial number: {camera.GetDeviceInfo().GetSerialNumber()}")
        
        # Open the camera
        camera.Open()
        
        # Set camera parameters
        camera.MaxNumBuffer = max_buffer_size
        
        # Set pixel format
        try:
            if pixel_format == "BGR8packed":
                camera.PixelFormat.SetValue(pylon.PixelType_BGR8packed)
            elif pixel_format == "Mono8":
                camera.PixelFormat.SetValue(pylon.PixelType_Mono8)
            else:
                print(f"Warning: Unsupported pixel format '{pixel_format}', using default")
        except Exception as e:
            print(f"Could not set pixel format to {pixel_format}: {e}")
        
        # Set acquisition mode
        try:
            if acquisition_mode == "Continuous":
                camera.AcquisitionMode.SetValue(pylon.AcquisitionMode_Continuous)
            elif acquisition_mode == "SingleFrame":
                camera.AcquisitionMode.SetValue(pylon.AcquisitionMode_SingleFrame)
            else:
                print(f"Warning: Unsupported acquisition mode '{acquisition_mode}', using default")
        except Exception as e:
            print(f"Could not set acquisition mode to {acquisition_mode}: {e}")
        
        # Enable frame rate control if available
        try:
            camera.AcquisitionFrameRateEnable.SetValue(True)
            camera.AcquisitionFrameRate.SetValue(fps)
        except Exception as e:
            print(f"Could not set frame rate to {fps}: {e}")
        
        # Get and display camera properties
        width = camera.Width.GetValue()
        height = camera.Height.GetValue()
        print(f"Camera resolution: {width}x{height}")
        
        # Try to get actual frame rate
        try:
            actual_fps = camera.AcquisitionFrameRate.GetValue()
            print(f"Camera frame rate: {actual_fps:.1f} FPS")
        except Exception:
            print(f"Target frame rate: {fps} FPS")
        
        return camera
        
    except Exception as e:
        raise BaslerCameraError(f"Error initializing camera: {e}")


def get_camera_properties(camera: pylon.InstantCamera) -> dict:
    """
    Get camera properties as a dictionary.
    
    Args:
        camera: Initialized camera object
        
    Returns:
        Dictionary containing camera properties
    """
    properties = {
        "model": camera.GetDeviceInfo().GetModelName(),
        "serial_number": camera.GetDeviceInfo().GetSerialNumber(),
        "width": camera.Width.GetValue(),
        "height": camera.Height.GetValue(),
    }
    
    # Try to get frame rate
    try:
        properties["fps"] = camera.AcquisitionFrameRate.GetValue()
    except Exception:
        properties["fps"] = None
    
    # Try to get pixel format
    try:
        properties["pixel_format"] = camera.PixelFormat.GetValue()
    except Exception:
        properties["pixel_format"] = None
    
    return properties


def create_image_converter(
    output_format: str = "BGR8packed",
    bit_alignment: str = "MsbAligned"
) -> pylon.ImageFormatConverter:
    """
    Create and configure an image format converter.
    
    Args:
        output_format: Output pixel format ("BGR8packed", "Mono8")
        bit_alignment: Bit alignment ("MsbAligned", "LsbAligned")
        
    Returns:
        Configured image format converter
    """
    converter = pylon.ImageFormatConverter()
    
    if output_format == "BGR8packed":
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
    elif output_format == "Mono8":
        converter.OutputPixelFormat = pylon.PixelType_Mono8
    else:
        # Default to BGR8packed
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
    
    if bit_alignment == "MsbAligned":
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
    elif bit_alignment == "LsbAligned":
        converter.OutputBitAlignment = pylon.OutputBitAlignment_LsbAligned
    else:
        # Default to MsbAligned
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
    
    return converter


def safe_camera_cleanup(camera: pylon.InstantCamera) -> None:
    """
    Safely clean up camera resources.
    
    Args:
        camera: Camera object to clean up
    """
    try:
        if camera.IsGrabbing():
            camera.StopGrabbing()
        if camera.IsOpen():
            camera.Close()
        print("Camera closed successfully")
    except Exception as e:
        print(f"Error during camera cleanup: {e}")


def create_output_directory(base_path: str = ".", subdir: str = "output") -> str:
    """
    Create output directory if it doesn't exist.
    
    Args:
        base_path: Base path where to create the directory
        subdir: Subdirectory name
        
    Returns:
        Path to the created directory
    """
    output_dir = os.path.join(base_path, subdir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir


def record_video_from_camera(
    camera: pylon.InstantCamera,
    output_path: str,
    duration: float = 10.0,
    progress_callback: Optional[callable] = None
) -> Tuple[bool, dict]:
    """
    Record video from camera to file.
    
    Args:
        camera: Initialized camera object
        output_path: Path where to save the video
        duration: Recording duration in seconds
        progress_callback: Optional callback function for progress updates
        
    Returns:
        Tuple of (success: bool, stats: dict)
    """
    try:
        # Get camera properties
        properties = get_camera_properties(camera)
        width = properties["width"]
        height = properties["height"]
        fps = properties["fps"] or 30.0
        
        print(f"Recording video: {width}x{height} at {fps:.1f} FPS")
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            raise BaslerCameraError(f"Failed to open video writer for: {output_path}")
        
        # Create image converter
        converter = create_image_converter()
        
        # Start grabbing
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        
        start_time = time.time()
        frame_count = 0
        
        print(f"Recording for {duration} seconds...")
        print("Press Ctrl+C to stop recording early")
        
        while camera.IsGrabbing():
            # Check if duration has elapsed
            elapsed = time.time() - start_time
            if elapsed > duration:
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
                
                # Call progress callback if provided
                if progress_callback and frame_count % 60 == 0:
                    progress = (elapsed / duration) * 100
                    progress_callback(frame_count, elapsed, progress)
            
            grabResult.Release()
        
        # Clean up
        camera.StopGrabbing()
        out.release()
        
        elapsed_time = time.time() - start_time
        
        # Prepare statistics
        stats = {
            "frame_count": frame_count,
            "duration": elapsed_time,
            "average_fps": frame_count / elapsed_time if elapsed_time > 0 else 0,
            "target_fps": fps,
            "resolution": (width, height),
            "output_path": output_path
        }
        
        print(f"\nRecording complete!")
        print(f"Total frames recorded: {frame_count}")
        print(f"Total time: {elapsed_time:.1f} seconds")
        print(f"Average FPS: {stats['average_fps']:.1f}")
        print(f"Video saved to: {output_path}")
        
        return True, stats
        
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
        if camera.IsGrabbing():
            camera.StopGrabbing()
        if 'out' in locals():
            out.release()
        return False, {}
        
    except Exception as e:
        print(f"Error during recording: {e}")
        if camera.IsGrabbing():
            camera.StopGrabbing()
        if 'out' in locals():
            out.release()
        return False, {}


def capture_single_frame(
    camera: pylon.InstantCamera,
    output_path: str,
    timeout_ms: int = 5000
) -> bool:
    """
    Capture a single frame from the camera and save it.
    
    Args:
        camera: Initialized camera object
        output_path: Path where to save the image
        timeout_ms: Timeout in milliseconds for frame capture
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create image converter
        converter = create_image_converter()
        
        # Start grabbing if not already started
        was_grabbing = camera.IsGrabbing()
        if not was_grabbing:
            camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        
        # Grab an image
        grabResult = camera.RetrieveResult(timeout_ms, pylon.TimeoutHandling_ThrowException)
        
        if grabResult.GrabSucceeded():
            # Convert to OpenCV format
            image = converter.Convert(grabResult)
            img_array = image.GetArray()
            
            # Save the image
            success = cv2.imwrite(output_path, img_array)
            if success:
                print(f"Frame saved to: {output_path}")
                return True
            else:
                print(f"Failed to save frame to: {output_path}")
                return False
        else:
            print(f"Frame capture failed: {grabResult.GetErrorDescription()}")
            return False
            
        grabResult.Release()
        
        # Stop grabbing if we started it
        if not was_grabbing:
            camera.StopGrabbing()
            
    except Exception as e:
        print(f"Error capturing frame: {e}")
        return False
