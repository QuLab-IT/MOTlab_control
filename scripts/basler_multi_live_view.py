#!/usr/bin/env python3
"""
Basler Multi-Camera Live View Script
Displays live video feed from all connected Basler cameras simultaneously
using pypylon and OpenCV.

Controls:
  - Press 'q' or ESC to quit
  - Press 's' to save frames from all cameras
  - Press 'c' to cycle selected camera
  - Press '[' / ']' to decrease / increase exposure on selected camera (if supported)
  - Press 'f' to toggle fullscreen on selected camera's window
"""

import os
import sys
import math
import time
import cv2
from pypylon import pylon

WINDOW_BASE_NAME = "Basler Camera"

def create_camera(device):
    """Create and configure a Basler camera for live view."""
    cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(device))
    cam.Open()
    cam.MaxNumBuffer = 5
    try:
        cam.PixelFormat.SetValue(pylon.PixelType_BGR8packed)
    except Exception:
        pass
    try:
        cam.AcquisitionMode.SetValue(pylon.AcquisitionMode_Continuous)
    except Exception:
        pass
    try:
        cam.AcquisitionFrameRateEnable.SetValue(True)
        cam.AcquisitionFrameRate.SetValue(30.0)
    except Exception:
        pass
    return cam

def init_cameras():
    """Enumerate and initialize all connected Basler cameras."""
    instance = pylon.TlFactory.GetInstance()
    devices = instance.EnumerateDevices()
    if not devices:
        print("No Basler cameras found.")
        return []

    cameras = []
    for idx, dev in enumerate(devices):
        model = "<unknown>"
        serial = "<unknown>"
        try:
            model = dev.GetModelName()
        except Exception:
            pass
        try:
            serial = dev.GetSerialNumber()
        except Exception:
            pass

        print(f"[{idx}] {model} (S/N: {serial})")

        try:
            cam = create_camera(dev)
            info = cam.GetDeviceInfo()
            print(f"Opened camera [{idx}] {info.GetModelName()} (S/N: {info.GetSerialNumber()})")
            cameras.append({
                "device": dev,
                "camera": cam,
                "model": model,
                "serial": serial,
                "window_name": f"{WINDOW_BASE_NAME} {idx} - {model} (S/N:{serial})",
                "converter": pylon.ImageFormatConverter(),
                "frame": None,
                "frames_count": 0,
                "fps_time": time.time(),
                "fps": 0.0,
                "fullscreen": False,
                "exposure_supported": False,
                "exp_val": None,
                "exp_min": None,
                "exp_max": None
            })
        except Exception as e:
            print(f"Could not initialize camera {idx}: {e}")

    # Configure converters and exposure settings per camera
    for cam_info in cameras:
        conv = cam_info["converter"]
        conv.OutputPixelFormat = pylon.PixelType_BGR8packed
        conv.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        cam = cam_info["camera"]
        # Try to setup exposure controls (best-effort)
        try:
            if hasattr(cam, "ExposureAuto"):
                try:
                    cam.ExposureAuto.SetValue("Off")
                except Exception:
                    try:
                        cam.ExposureAuto.SetValue(pylon.ExposureAuto_Off)
                    except Exception:
                        pass
            if hasattr(cam, "ExposureTime"):
                try:
                    cam_info["exp_val"] = cam.ExposureTime.GetValue()
                    cam_info["exp_min"] = cam.ExposureTime.GetMin()
                    cam_info["exp_max"] = cam.ExposureTime.GetMax()
                    cam_info["exposure_supported"] = True
                except Exception:
                    cam_info["exposure_supported"] = False
        except Exception:
            cam_info["exposure_supported"] = False

    return cameras

def start_grabbing_all(cameras):
    for cam_info in cameras:
        try:
            cam_info["camera"].StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        except Exception as e:
            print(f"Warning: could not start grabbing for {cam_info['window_name']}: {e}")

def stop_and_close_all(cameras):
    for cam_info in cameras:
        cam = cam_info["camera"]
        try:
            if cam.IsGrabbing():
                cam.StopGrabbing()
        except Exception:
            pass
        try:
            if cam.IsOpen():
                cam.Close()
        except Exception:
            pass

def tile_windows(cameras, max_win_w=640, max_win_h=480, gap=10):
    """Tiling windows in a grid on the screen."""
    n = len(cameras)
    if n == 0:
        return
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    # Determine window size: scale cameras to fit max sizes, use first camera resolution as base
    first_cam = cameras[0]["camera"]
    try:
        w = first_cam.Width.GetValue()
        h = first_cam.Height.GetValue()
    except Exception:
        w, h = 640, 480
    scale = min(max_win_w / w, max_win_h / h, 1.0)
    win_w, win_h = int(w * scale), int(h * scale)

    screen_x, screen_y = 0, 0
    for idx, cam_info in enumerate(cameras):
        r = idx // cols
        c = idx % cols
        x = screen_x + c * (win_w + gap)
        y = screen_y + r * (win_h + gap)
        cv2.namedWindow(cam_info["window_name"], cv2.WINDOW_NORMAL)
        cv2.resizeWindow(cam_info["window_name"], win_w, win_h)
        cv2.moveWindow(cam_info["window_name"], x, y)

def save_frames(cameras, out_dir="output"):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    ts = time.strftime("%Y%m%d_%H%M%S")
    for idx, cam_info in enumerate(cameras):
        frame = cam_info.get("frame")
        if frame is None:
            continue
        filename = f"basler_cam{idx}_{cam_info['serial']}_{ts}.jpg"
        filepath = os.path.join(out_dir, filename)
        try:
            cv2.imwrite(filepath, frame)
            print(f"Saved {filepath}")
        except Exception as e:
            print(f"Could not save frame for camera {idx}: {e}")

def clamp(val, mn, mx):
    if mn is None or mx is None:
        return val
    return max(mn, min(val, mx))

def main():
    print("Basler Multi-Camera Live View")
    print("=" * 30)
    cameras = init_cameras()
    if not cameras:
        sys.exit(1)

    # Show window names and properties
    for idx, cam_info in enumerate(cameras):
        try:
            w = cam_info["camera"].Width.GetValue()
            h = cam_info["camera"].Height.GetValue()
            print(f"[{idx}] {cam_info['window_name']} - resolution: {w}x{h}")
        except Exception:
            pass

    # Prepare windows tiled
    tile_windows(cameras)

    # Start grabbing
    start_grabbing_all(cameras)

    # Display loop variables
    running = True
    selected_idx = 0
    frame_save_count = 0
    fps_update_interval = 30

    print("\nLive view started! Controls:")
    print("  - Press 'q' or ESC to quit")
    print("  - Press 's' to save frames for all cameras")
    print("  - Press 'c' to cycle selected camera")
    print("  - Press '[' / ']' to decrease / increase exposure on selected camera")
    print("  - Press 'f' to toggle fullscreen on the selected camera window\n")

    try:
        # main loop
        while running:
            for idx, cam_info in enumerate(cameras):
                cam = cam_info["camera"]
                if not cam.IsGrabbing():
                    continue
                try:
                    grabResult = cam.RetrieveResult(2000, pylon.TimeoutHandling_ThrowException)
                except Exception as e:
                    # skip on timeout or errors
                    continue

                if grabResult and grabResult.GrabSucceeded():
                    # convert and store
                    img = cam_info["converter"].Convert(grabResult)
                    frame = img.GetArray()
                    cam_info["frame"] = frame

                    # Update FPS
                    cam_info["frames_count"] += 1
                    if cam_info["frames_count"] % fps_update_interval == 0:
                        elapsed = time.time() - cam_info["fps_time"]
                        if elapsed > 0:
                            cam_info["fps"] = fps_update_interval / elapsed
                        cam_info["fps_time"] = time.time()

                    # Annotate frame with info
                    disp = frame.copy()
                    cv2.putText(disp, f"Cam {idx} {cam_info['model']} (S/N:{cam_info['serial']})", (10, 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.putText(disp, f"FPS: {cam_info['fps']:.1f}", (10, 55),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.putText(disp, f"Selected: {'*' if idx == selected_idx else ' '}", (10, 85),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255) if idx == selected_idx else (255, 255, 255), 2)

                    # Display the frame
                    cv2.imshow(cam_info["window_name"], disp)

                if grabResult:
                    grabResult.Release()

            # Handle key input
            key = cv2.waitKey(1) & 0xFF
            if key != 255:  # a key was pressed
                if key == ord('q') or key == 27:
                    running = False
                    break
                elif key == ord('s'):
                    save_frames(cameras)
                    frame_save_count += 1
                elif key == ord('c'):
                    selected_idx = (selected_idx + 1) % len(cameras)
                    print(f"Selected camera {selected_idx}")
                elif key == ord('f'):
                    # toggle fullscreen for selected window
                    cam_info = cameras[selected_idx]
                    cam_info["fullscreen"] = not cam_info["fullscreen"]
                    prop = cv2.WINDOW_FULLSCREEN if cam_info["fullscreen"] else cv2.WINDOW_NORMAL
                    cv2.setWindowProperty(cam_info["window_name"], cv2.WND_PROP_FULLSCREEN, prop)
                elif key == ord(']'):
                    # increase exposure for selected camera
                    cam_info = cameras[selected_idx]
                    if cam_info["exposure_supported"] and cam_info["exp_val"] is not None:
                        try:
                            new_exp = int(cam_info["exp_val"] * 1.2)
                            if cam_info["exp_max"] is not None:
                                new_exp = min(new_exp, cam_info["exp_max"])
                            cam_info["camera"].ExposureTime.SetValue(new_exp)
                            cam_info["exp_val"] = cam_info["camera"].ExposureTime.GetValue()
                            print(f"Camera {selected_idx} exposure increased -> {cam_info['exp_val']}")
                        except Exception as e:
                            print(f"Could not increase exposure on camera {selected_idx}: {e}")
                    else:
                        print("Exposure adjustment not supported on this camera.")
                elif key == ord('['):
                    # decrease exposure for selected camera
                    cam_info = cameras[selected_idx]
                    if cam_info["exposure_supported"] and cam_info["exp_val"] is not None:
                        try:
                            new_exp = int(max(1, cam_info["exp_val"] / 1.2))
                            if cam_info["exp_min"] is not None:
                                new_exp = max(new_exp, cam_info["exp_min"])
                            cam_info["camera"].ExposureTime.SetValue(new_exp)
                            cam_info["exp_val"] = cam_info["camera"].ExposureTime.GetValue()
                            print(f"Camera {selected_idx} exposure decreased -> {cam_info['exp_val']}")
                        except Exception as e:
                            print(f"Could not decrease exposure on camera {selected_idx}: {e}")
                    else:
                        print("Exposure adjustment not supported on this camera.")
            # small sleep to reduce CPU usage
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\nLive view interrupted by user")

    except Exception as e:
        print(f"Error in main loop: {e}")

    finally:
        print("\nStopping and closing cameras...")
        stop_and_close_all(cameras)
        cv2.destroyAllWindows()
        print("Done.")

if __name__ == "__main__":
    main()