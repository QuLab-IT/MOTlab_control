#!/usr/bin/env python3
"""
Basler Camera Live View Script with Background Subtraction
First records a background video, then displays live video feed from a connected 
Basler camera with real-time background subtraction using pypylon library.
"""

import argparse
import os
import sys
import time
from datetime import datetime
from typing import Optional

import cv2
import numpy as np

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from camera_utils import (BaslerCameraError, create_image_converter,
                          create_output_directory, initialize_basler_camera,
                          record_video_from_camera, safe_camera_cleanup)
from pypylon import pylon

# Import background functions from existing module
try:
    from acquire_without_background import (extract_background_from_video,
                                            subtract_background)
except ImportError:
    # Fallback if import fails
    def extract_background_from_video(video_path: str) -> np.ndarray:
        """Fallback implementation if import fails."""
        raise ImportError("acquire_without_background module not available")
    
    def subtract_background(image_path: str, background: np.ndarray, method: str = "subtract") -> np.ndarray:
        """Fallback implementation if import fails."""
        raise ImportError("acquire_without_background module not available")


def initialize_camera():
    """Initialize and configure the Basler camera for live view."""
    try:
        # Use unified initialization with smaller buffer for live view
        return initialize_basler_camera(max_buffer_size=5, fps=30.0)
    except BaslerCameraError as e:
        print(f"Camera initialization failed: {e}")
        return None


def record_background_video(camera, output_path: str, duration: float = 10.0) -> bool:
    """
    Record background video for later subtraction.
    
    Args:
        camera: Initialized camera object
        output_path: Path where to save the background video
        duration: Recording duration in seconds
        
    Returns:
        True if recording successful, False otherwise
    """
    print(f"\n=== Recording Background Video ===")
    print(f"Duration: {duration} seconds")
    print(f"Output: {output_path}")
    print("Please ensure the scene is empty (no objects to track)")
    print("Press Enter when ready to start recording, or Ctrl+C to skip...")
    
    try:
        input()  # Wait for user confirmation
    except KeyboardInterrupt:
        print("\nBackground recording skipped by user")
        return False
    
    def progress_callback(frame_count: int, elapsed: float, progress: float) -> None:
        """Progress callback for recording."""
        print(f"Recording progress: {progress:.1f}% ({frame_count} frames, {elapsed:.1f}s)")
    
    try:
        success, stats = record_video_from_camera(
            camera, 
            output_path, 
            duration, 
            progress_callback
        )
        
        if success:
            print(f"Background video recorded successfully!")
            print(f"Frames: {stats['frame_count']}, Duration: {stats['duration']:.1f}s")
        else:
            print("Background recording failed!")
        
        return success
        
    except Exception as e:
        print(f"Error during background recording: {e}")
        return False





def apply_background_subtraction_to_array(
    frame: np.ndarray, 
    background: np.ndarray, 
    method: str = "subtract",
    threshold: int = 25
) -> np.ndarray:
    """
    Apply background subtraction to a frame array using the existing subtract_background logic.
    
    Args:
        frame: Current frame (BGR or grayscale)
        background: Background image (grayscale)  
        method: Background subtraction method ('subtract' or 'divide')
        threshold: Threshold for binary conversion (only used for 'subtract' method)
        
    Returns:
        Background-subtracted frame
    """
    # Convert frame to grayscale if needed
    if len(frame.shape) == 3:
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        frame_gray = frame
    
    # Ensure dimensions match
    if frame_gray.shape != background.shape:
        background = cv2.resize(background, (frame_gray.shape[1], frame_gray.shape[0]))
    
    # Apply the same logic as the existing subtract_background function
    if method == "subtract":
        # Simple subtraction with clipping
        result = cv2.subtract(frame_gray, background)
        # Apply threshold to enhance contrast for live view
        _, result = cv2.threshold(result, threshold, 255, cv2.THRESH_BINARY)
    elif method == "divide":
        # Division method (good for illumination correction)
        # Avoid division by zero
        background_safe = np.where(background == 0, 1, background)
        result = (frame_gray.astype(np.float32) / background_safe.astype(np.float32) * 128).astype(np.uint8)
        result = np.clip(result, 0, 255)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Always convert result to BGR for consistent display and text overlay
    if len(result.shape) == 2:  # If result is grayscale
        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
    
    return result

def display_live_view(camera, background: Optional[np.ndarray] = None):
    """
    Display live video feed from the camera with optional background subtraction.
    
    Args:
        camera: Initialized camera object
        background: Optional background image for subtraction
    """
    try:
        # Create image converter using unified function
        converter = create_image_converter()
        
        # Start grabbing
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        
        # Create window
        window_name = "Basler Camera Live View"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        # Variables for FPS calculation
        frame_count = 0
        start_time = time.time()
        fps_update_interval = 30  # Update FPS every 30 frames
        
        # Background subtraction control
        bg_subtraction_enabled = background is not None
        show_original = False  # Toggle between original and processed
        bg_method = "subtract"  # Background subtraction method
        
        print("\nLive view started!")
        print("Controls:")
        print("  - Press 'q' or ESC to quit")
        print("  - Press 'f' to toggle fullscreen")
        print("  - Press 's' to save current frame")
        if bg_subtraction_enabled:
            print("  - Press 'b' to toggle background subtraction on/off")
            print("  - Press 'o' to toggle original/processed view")
            print("  - Press 't' to adjust threshold (10-100)")
            print("  - Press 'm' to switch method (subtract/divide)")
        
        fullscreen = False
        frame_save_count = 0
        threshold_value = 25  # Default threshold for background subtraction
        
        while camera.IsGrabbing():
            # Grab an image with error handling
            try:
                grabResult = camera.RetrieveResult(1000, pylon.TimeoutHandling_Return)
                
                if not grabResult.GrabSucceeded():
                    # Skip this frame if grab failed - common with "buffer cancelled" errors
                    grabResult.Release()
                    continue
                    
            except Exception as e:
                # Handle timeout and other grab errors gracefully
                if "timeout" not in str(e).lower():
                    print(f"Camera grab error: {e}")
                continue
                
            # Process the grabbed frame
            try:
                # Convert to OpenCV format
                image = converter.Convert(grabResult)
                img_array = image.GetArray()
                
                # Apply background subtraction if enabled
                if bg_subtraction_enabled and not show_original:
                    img_display = apply_background_subtraction_to_array(
                        img_array, background, method=bg_method, threshold=threshold_value
                    )
                else:
                    img_display = img_array.copy()
                
                # Calculate and display FPS
                frame_count += 1
                if frame_count % fps_update_interval == 0:
                    elapsed_time = time.time() - start_time
                    fps = fps_update_interval / elapsed_time
                    start_time = time.time()
                    # Add FPS text to image
                    cv2.putText(img_display, f"FPS: {fps:.1f}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                
                # Add overlay information
                if frame_count % fps_update_interval == 0 or frame_count <= fps_update_interval:
                    # Add frame counter
                    cv2.putText(img_display, f"Frame: {frame_count}", (10, 70), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Add background subtraction status
                    if bg_subtraction_enabled:
                        status = "BG Sub: ON" if not show_original else "BG Sub: OFF (Original)"
                        cv2.putText(img_display, status, (10, 110), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                        cv2.putText(img_display, f"Method: {bg_method}", (10, 150), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                        if bg_method == "subtract":
                            cv2.putText(img_display, f"Threshold: {threshold_value}", (10, 190), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                    
                    # Add controls info
                    y_pos = img_display.shape[0] - 80
                    cv2.putText(img_display, "Controls: 'q'-quit, 'f'-fullscreen, 's'-save", 
                            (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    if bg_subtraction_enabled:
                        cv2.putText(img_display, "'b'-toggle BG, 'o'-original, 't'-threshold, 'm'-method", 
                                (10, y_pos + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
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
                    output_dir = create_output_directory(os.path.dirname(__file__))
                    
                    # Save the original frame, not the processed one
                    filename = f"basler_frame_{timestamp}_{frame_save_count:03d}.jpg"
                    filepath = os.path.join(output_dir, filename)
                    cv2.imwrite(filepath, img_array)
                    print(f"Frame saved to: {filepath}")
                    
                    # Also save processed frame if background subtraction is active
                    if bg_subtraction_enabled and not show_original:
                        processed_filename = f"basler_frame_processed_{timestamp}_{frame_save_count:03d}.jpg"
                        processed_filepath = os.path.join(output_dir, processed_filename)
                        cv2.imwrite(processed_filepath, img_display)
                        print(f"Processed frame saved to: {processed_filepath}")
                
                # Background subtraction controls
                elif key == ord('b') and bg_subtraction_enabled:  # 'b' key to toggle background subtraction
                    show_original = not show_original
                    status = "OFF (showing original)" if show_original else "ON"
                    print(f"Background subtraction: {status}")
                elif key == ord('o') and bg_subtraction_enabled:  # 'o' key to toggle original view
                    show_original = not show_original
                    status = "original" if show_original else "processed"
                    print(f"Showing {status} view")
                elif key == ord('t') and bg_subtraction_enabled:  # 't' key to adjust threshold
                    threshold_value += 10
                    if threshold_value > 100:
                        threshold_value = 10
                    print(f"Threshold set to: {threshold_value}")
                elif key == ord('m') and bg_subtraction_enabled:  # 'm' key to switch method
                    bg_method = "divide" if bg_method == "subtract" else "subtract"
                    print(f"Background subtraction method: {bg_method}")
                    
            except Exception as e:
                print(f"Error in frame processing: {e}")
            finally:
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


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Basler Camera Live View with Background Subtraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Record background video, then start live view
  %(prog)s
  
  # Use existing background video file
  %(prog)s --background-video /path/to/background.avi
  
  # Record background for specific duration, then start live view
  %(prog)s --duration 15
        """
    )
    
    parser.add_argument(
        "-b", "--background-video",
        help="Path to existing background video file. If provided, skips recording step."
    )
    
    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Background recording duration in seconds (default: 10.0). Only used if recording."
    )
    
    return parser.parse_args()


def main():
    """Main function to run the live view script with background subtraction."""
    # Parse command line arguments
    args = parse_arguments()
    
    print("Basler Camera Live View with Background Subtraction")
    print("=" * 50)
    
    # Initialize camera
    print("Initializing camera...")
    camera = initialize_camera()
    
    if camera is None:
        print("Failed to initialize camera. Exiting.")
        sys.exit(1)
    
    background = None
    background_video_path = args.background_video
    
    try:
        # Step 1: Handle background video
        if background_video_path:
            # Use existing background video
            print(f"\nUsing existing background video: {background_video_path}")
            
            if not os.path.exists(background_video_path):
                print(f"Error: Background video file not found: {background_video_path}")
                sys.exit(1)
            
            # Extract background from existing video
            print(f"Extracting background from: {background_video_path}")
            try:
                background = extract_background_from_video(background_video_path)
                print("Background extraction successful!")
            except Exception as e:
                print(f"Background extraction failed: {e}")
                print("Continuing without background subtraction...")
                background = None
        else:
            # Record new background video
            output_dir = create_output_directory(os.path.dirname(__file__))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            background_video_path = os.path.join(output_dir, f"background_{timestamp}.avi")
            
            print(f"\nStep 1: Recording background video...")
            duration = args.duration
            
            # Ask user for recording duration if not specified via command line
            try:
                user_input = input(f"Enter background recording duration in seconds (default: {duration}): ")
                if user_input.strip():
                    duration = float(user_input)
            except ValueError:
                print("Invalid input, using default duration")
            except KeyboardInterrupt:
                print("\nOperation cancelled by user")
                return
            
            # Record background
            success = record_background_video(camera, background_video_path, duration)
            
            if not success:
                print("Background recording failed. Continuing without background subtraction...")
            else:
                # Step 2: Extract background from recorded video
                print(f"\nStep 2: Extracting background from recorded video...")
                try:
                    background = extract_background_from_video(background_video_path)
                    print("Background extraction successful!")
                except Exception as e:
                    print(f"Background extraction failed: {e}")
                    print("Continuing without background subtraction...")
                    background = None
        
        # Step 3: Start live view with background subtraction
        print(f"\nStep 3: Starting live view...")
        if background is not None:
            print("Background subtraction is enabled!")
            print(f"Background video: {background_video_path}")
        else:
            print("Background subtraction is disabled.")
        
        display_live_view(camera, background)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        # Clean up using unified function
        safe_camera_cleanup(camera)

if __name__ == "__main__":
    main() 



