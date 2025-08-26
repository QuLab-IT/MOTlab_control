"""
Background subtraction script for MOT lab experiments.

This script removes background from an image using a background video file.
The background is computed as the average of all frames in the video.
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

from camera_utils import (BaslerCameraError, create_output_directory,
                                    initialize_basler_camera,
                                    record_video_from_camera,
                                    safe_camera_cleanup)


def extract_background_from_video(video_path: str) -> np.ndarray:
    """
    Extract background by averaging all frames from a video file.
    
    Args:
        video_path: Path to the background video file
        
    Returns:
        Background image as numpy array
        
    Raises:
        ValueError: If video file cannot be opened or is empty
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")
    
    frames = []
    frame_count = 0
    
    print(f"Processing background video: {video_path}")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Convert to grayscale for consistency
        if len(frame.shape) == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
        frames.append(frame.astype(np.float32))
        frame_count += 1
        
        if frame_count % 100 == 0:
            print(f"Processed {frame_count} frames...")
    
    cap.release()
    
    if frame_count == 0:
        raise ValueError(f"No frames found in video: {video_path}")
    
    print(f"Computing background from {frame_count} frames...")
    
    # Compute average background
    background = np.mean(frames, axis=0).astype(np.uint8)
    
    return background


def subtract_background(
    image_path: str, 
    background: np.ndarray,
    method: str = "subtract"
) -> np.ndarray:
    """
    Remove background from an image.
    
    Args:
        image_path: Path to the input image
        background: Background image to subtract
        method: Background subtraction method ('subtract' or 'divide')
        
    Returns:
        Background-subtracted image
        
    Raises:
        ValueError: If image cannot be loaded or dimensions don't match
    """
    # Load the image
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if image is None:
        raise ValueError(f"Cannot load image: {image_path}")
    
    # Check dimensions match
    if image.shape != background.shape:
        raise ValueError(
            f"Image dimensions {image.shape} don't match background {background.shape}"
        )
    
    print(f"Applying {method} background subtraction...")
    
    if method == "subtract":
        # Simple subtraction with clipping
        result = cv2.subtract(image, background)
    elif method == "divide":
        # Division method (good for illumination correction)
        # Avoid division by zero
        background_safe = np.where(background == 0, 1, background)
        result = (image.astype(np.float32) / background_safe.astype(np.float32) * 128).astype(np.uint8)
        result = np.clip(result, 0, 255)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return result


def save_image(image: np.ndarray, output_path: str) -> None:
    """
    Save processed image to file.
    
    Args:
        image: Image array to save
        output_path: Output file path
    """
    success = cv2.imwrite(output_path, image)
    if not success:
        raise ValueError(f"Failed to save image to: {output_path}")
    print(f"Saved processed image to: {output_path}")



def record_background_video(
    output_path: str,
    duration: float = 10.0,
    fps: float = 30.0
) -> bool:
    """
    Record background video using Basler camera.
    
    Args:
        output_path: Path where to save the video file
        duration: Recording duration in seconds
        fps: Target frames per second
        
    Returns:
        True if recording was successful, False otherwise
    """
    try:
        camera = initialize_basler_camera(fps=fps)
        
        def progress_callback(frame_count: int, elapsed: float, progress: float) -> None:
            """Progress callback for recording."""
            print(f"Progress: {progress:.1f}% ({frame_count} frames)")
        
        success, stats = record_video_from_camera(
            camera, 
            output_path, 
            duration, 
            progress_callback
        )
        
        safe_camera_cleanup(camera)
        return success
        
    except BaslerCameraError as e:
        print(f"Camera error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def main() -> None:
    """Main function to handle command line arguments and process images."""
    parser = argparse.ArgumentParser(
        description="Background subtraction tool with Basler camera recording capability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Record background video first
  %(prog)s --record-background --duration 30 --output-dir ./output
  
  # Remove background from image using existing video
  %(prog)s -v background.avi -i image.jpg
  
  # Complete workflow: record then process
  %(prog)s --record-background --duration 10 -i image.jpg
        """
    )
    
    # Recording arguments
    parser.add_argument(
        "--record-background",
        action="store_true",
        help="Record background video using Basler camera"
    )
    
    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Recording duration in seconds (default: 10.0)"
    )
    
    parser.add_argument(
        "--fps",
        type=float,
        default=30.0,
        help="Target frame rate for recording (default: 30.0)"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Output directory for recorded video (default: ./output)"
    )
    
    # Background subtraction arguments
    parser.add_argument(
        "-v", "--video",
        help="Path to background video file (required for background subtraction)"
    )
    
    parser.add_argument(
        "-i", "--image", 
        help="Path to input image file (required for background subtraction)"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Path to output image file (default: input_no_bg.jpg)"
    )
    
    parser.add_argument(
        "-m", "--method",
        choices=["subtract", "divide"],
        default="subtract",
        help="Background subtraction method (default: subtract)"
    )
    
    parser.add_argument(
        "--save-background",
        help="Save computed background to this path"
    )
    
    args = parser.parse_args()
    
    # Determine operation mode
    if args.record_background:
        # Recording mode
        print("=== Background Video Recording Mode ===")
        
        # Set output directory
        if args.output_dir:
            output_dir = args.output_dir
        else:
            output_dir = create_output_directory()
        
        # Generate timestamp for video filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"background_recording_{timestamp}.avi"
        video_path = os.path.join(output_dir, video_filename)
        
        print(f"Recording background video to: {video_path}")
        print(f"Duration: {args.duration} seconds")
        print(f"Target FPS: {args.fps}")
        
        # Record the background video
        success = record_background_video(video_path, args.duration, args.fps)
        
        if not success:
            print("Background recording failed!")
            sys.exit(1)
        
        # If image processing is also requested, use the recorded video
        if args.image:
            args.video = video_path
            print(f"\n=== Processing image with recorded background ===")
        else:
            print("Background recording completed successfully!")
            print(f"Use the recorded video with: -v {video_path}")
            return
    
    # Background subtraction mode
    if args.image:
        print("=== Background Subtraction Mode ===")
        
        # Validate required arguments
        if not args.video:
            print("Error: Video file (-v/--video) is required for background subtraction")
            sys.exit(1)
        
        # Validate input files exist
        if not os.path.exists(args.video):
            print(f"Error: Video file not found: {args.video}")
            sys.exit(1)
            
        if not os.path.exists(args.image):
            print(f"Error: Image file not found: {args.image}")
            sys.exit(1)
        
        # Set default output path if not provided
        if args.output is None:
            image_path = Path(args.image)
            args.output = str(image_path.parent / f"{image_path.stem}_no_bg{image_path.suffix}")
        
        try:
            # Extract background from video
            background = extract_background_from_video(args.video)
            
            # Save background if requested
            if args.save_background:
                save_image(background, args.save_background)
            
            # Subtract background from image
            result = subtract_background(args.image, background, args.method)
            
            # Save result
            save_image(result, args.output)
            
            print("Background subtraction completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    # If neither recording nor image processing requested
    if not args.record_background and not args.image:
        print("Error: Please specify either --record-background or provide an image (-i)")
        print("Use --help for usage information")
        sys.exit(1)


if __name__ == "__main__":
    main()

