#!/usr/bin/env python3
"""
Basler Camera Recording Script
Records video from a connected Basler camera using pypylon library
and saves it to the output directory with timestamp.
"""

import os
import sys
from datetime import datetime

from camera_utils import (BaslerCameraError, create_output_directory,
                          initialize_basler_camera, record_video_from_camera,
                          safe_camera_cleanup)


def record_video(camera, output_path, duration=10):
    """Record video from the camera and save to file using unified utilities."""
    def progress_callback(frame_count: int, elapsed: float, progress: float) -> None:
        """Progress callback for recording."""
        if frame_count % 30 == 0:  # Print every 30 frames like original
            print(f"Recorded {frame_count} frames in {elapsed:.1f}s")
    
    success, stats = record_video_from_camera(camera, output_path, duration, progress_callback)
    return success

def main():
    """Main function to run the recording script."""
    print("Basler Camera Recording Script")
    print("=" * 40)
    
    # Create output directory
    output_dir = create_output_directory(os.path.dirname(__file__))
    print(f"Output directory: {output_dir}")
    
    try:
        # Initialize camera
        print("\nInitializing camera...")
        camera = initialize_basler_camera()
        
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
        success = record_video(camera, output_path, duration)
        
        if not success:
            print("Recording failed!")
            sys.exit(1)
        
    except BaslerCameraError as e:
        print(f"Camera error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        # Clean up using unified function
        if 'camera' in locals():
            safe_camera_cleanup(camera)

if __name__ == "__main__":
    main()
