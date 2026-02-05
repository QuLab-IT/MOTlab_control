"""
Background utilities for camera live view scripts.
Provides functions to capture a background baseline (averaged frames)
and to subtract that baseline from frames.
"""

import time

import cv2
import numpy as np
from pypylon import pylon


def capture_background(camera, converter, num_frames=30, delay=0.02):
    """
    Capture a background baseline by averaging `num_frames` frames from `camera`.
    Returns a uint8 numpy array with the same shape as camera frames, or None on failure.
    """
    print(f"Capturing background baseline ({num_frames} frames)...")
    frames_collected = 0
    acc = None
    start = time.time()
    while frames_collected < num_frames and camera.IsGrabbing():
        try:
            grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grabResult.GrabSucceeded():
                image = converter.Convert(grabResult)
                arr = image.GetArray().astype(np.float32)
                if acc is None:
                    acc = arr
                else:
                    acc += arr
                frames_collected += 1
                if frames_collected % 10 == 0:
                    print(f"  Collected {frames_collected}/{num_frames} frames...")
            grabResult.Release()
            time.sleep(delay)
        except Exception as e:
            print(f"  Error capturing background frame: {e}")
            break

    if acc is None:
        print("  No frames collected for background.")
        return None

    bg = (acc / frames_collected).round().astype(np.uint8)
    elapsed = time.time() - start
    print(f"Background captured ({frames_collected} frames, {elapsed:.1f}s).")
    return bg


def subtract_background(frame, background):
    """
    Subtract `background` from `frame` safely using OpenCV. Both must be uint8 arrays
    with the same shape. Returns result uint8 array.
    """
    if background is None:
        return frame
    try:
        return cv2.subtract(frame, background)
    except Exception:
        # Fallback to simple numpy subtraction with clipping
        try:
            res = frame.astype(np.int16) - background.astype(np.int16)
            res = np.clip(res, 0, 255).astype(np.uint8)
            return res
        except Exception:
            return frame
