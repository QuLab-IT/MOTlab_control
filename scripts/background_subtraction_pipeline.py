
#!/usr/bin/env python3
"""
Background subtraction / division with normalization (lab imaging)

Features:
- Dark-frame subtraction
- Background subtraction (fluorescence) OR division (absorption)
- Exposure/gain normalization via a reference patch or histogram matching
- Optional flat-field correction
- Robust I/O for common image formats (8/16-bit, mono or color)
- CLI + Python API

Examples
--------
Fluorescence (subtraction) with patch normalization:
    python background_subtraction_pipeline.py \
        --signal signal.png --background background.png \
        --mode subtract \
        --normalize patch --ref-patch "50,50,150,150" \
        --output corrected.png

Absorption (division) with histogram normalization and dark frame:
    python background_subtraction_pipeline.py \
        --signal atoms.png --background no_atoms.png --dark dark.png \
        --mode divide --normalize hist --output od.png

Run synthetic demo:
    python background_subtraction_pipeline.py --demo
"""

from __future__ import annotations
import numpy as np
import cv2
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, Literal

# --------------------------- Utilities ---------------------------

def _read_any_image(path: Path) -> np.ndarray:
    """Read image as float64 in range [0, 1]. Supports 8/16-bit, mono or color.
    """
    if path is None:
        return None
    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    if img.dtype == np.uint8:
        img = img.astype(np.float64) / 255.0
    elif img.dtype == np.uint16:
        img = img.astype(np.float64) / 65535.0
    else:
        img = img.astype(np.float64)
        # best effort: scale to [0,1] if max > 1
        if img.max() > 1.0:
            img /= img.max() if img.max() > 0 else 1.0
    return img

def _save_image(path: Path, img: np.ndarray) -> None:
    """Save float image to 16-bit PNG (preserves dynamic range better)."""
    img = np.clip(img, 0, 1)
    out16 = (img * 65535.0 + 0.5).astype(np.uint16)
    # Use imencode to support non-ASCII paths cross-platform
    ext = path.suffix.lower()
    if ext not in {'.png', '.tif', '.tiff'}:
        path = path.with_suffix('.png')
    encoded, buf = cv2.imencode('.png', out16)
    if not encoded:
        raise IOError(f"Failed to encode image for saving: {path}")
    path.write_bytes(buf.tobytes())

def _to_gray(img: np.ndarray) -> np.ndarray:
    """Convert to grayscale safely (keeps single-channel as-is)."""
    if img.ndim == 2:
        return img
    if img.ndim == 3 and img.shape[2] == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if img.ndim == 3 and img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    # fallback: average channels
    return img.mean(axis=-1)

def _safe_eps(x: float = 1e-8) -> float:
    return x

# -------------------- Normalization Methods ----------------------

def compute_patch_scale(signal: np.ndarray, background: np.ndarray, patch: Tuple[int,int,int,int]) -> float:
    """Compute multiplicative scale so that background matches signal in a reference patch.
    patch = (x0, y0, x1, y1) in pixel coordinates (inclusive-exclusive on x1,y1)."""
    x0, y0, x1, y1 = patch
    sig_roi = _to_gray(signal)[y0:y1, x0:x1]
    bkg_roi = _to_gray(background)[y0:y1, x0:x1]
    s = sig_roi.mean()
    b = bkg_roi.mean() + _safe_eps()
    return float(s / b)

def histogram_match_scale(signal: np.ndarray, background: np.ndarray, clip: float = 0.01) -> float:
    """Compute a global multiplicative scale using robust percentiles (histogram/brightness matching).
    Returns scale 'k' to multiply background so its robust mean matches signal.
    """
    s_gray = _to_gray(signal).ravel()
    b_gray = _to_gray(background).ravel()
    # Robust slice via percentiles
    s_lo, s_hi = np.percentile(s_gray, [clip*100, 100-clip*100])
    b_lo, b_hi = np.percentile(b_gray, [clip*100, 100-clip*100])
    s_sel = s_gray[(s_gray >= s_lo) & (s_gray <= s_hi)]
    b_sel = b_gray[(b_gray >= b_lo) & (b_gray <= b_hi)]
    s_m = s_sel.mean()
    b_m = b_sel.mean() + _safe_eps()
    return float(s_m / b_m)

# ------------------------ Core Pipeline --------------------------

@dataclass
class PipelineConfig:
    mode: Literal["subtract", "divide"] = "subtract"
    normalize: Literal["none", "patch", "hist"] = "patch"
    ref_patch: Optional[Tuple[int,int,int,int]] = None  # x0,y0,x1,y1
    flat_field_path: Optional[Path] = None
    dark_path: Optional[Path] = None
    denoise_ksize: int = 0  # e.g., 3 for mild median filter

def process(signal: np.ndarray,
            background: np.ndarray,
            cfg: PipelineConfig) -> np.ndarray:
    """Apply dark subtraction, normalization, background subtraction/division, and optional flat-field + denoise.
    Returns float64 image in [0,1] (clipped)."""

    if signal.shape != background.shape:
        raise ValueError(f"Signal and background shapes differ: {signal.shape} vs {background.shape}")

    sig = signal.copy()
    bkg = background.copy()

    # 1) Dark subtraction
    if cfg.dark_path is not None:
        dark = _read_any_image(cfg.dark_path)
        if dark.shape != sig.shape:
            raise ValueError("Dark frame shape mismatch.")
        sig = sig - dark
        bkg = bkg - dark

    # 2) Flat-field (optional, multiplicative correction)
    if cfg.flat_field_path is not None:
        flat = _read_any_image(cfg.flat_field_path)
        if flat.shape != sig.shape:
            raise ValueError("Flat-field shape mismatch.")
        flat = np.clip(flat, _safe_eps(), None)
        sig = sig / flat
        bkg = bkg / flat

    # 3) Normalization
    if cfg.normalize == "patch":
        if cfg.ref_patch is None:
            raise ValueError("normalize='patch' requires ref_patch=(x0,y0,x1,y1).")
        k = compute_patch_scale(sig, bkg, cfg.ref_patch)
        bkg = bkg * k
    elif cfg.normalize == "hist":
        k = histogram_match_scale(sig, bkg, clip=0.01)
        bkg = bkg * k
    elif cfg.normalize == "none":
        pass
    else:
        raise ValueError(f"Unknown normalize mode: {cfg.normalize}")

    # 4) Background removal
    if cfg.mode == "subtract":
        out = sig - bkg
        # Zero floor, then scale to [0,1] by robust max
        out = np.maximum(out, 0)
        # Robust rescale for visualization
        p99 = np.percentile(out, 99.5)
        if p99 > _safe_eps():
            out = np.clip(out / p99, 0, 1)
        else:
            out = np.clip(out, 0, 1)
    elif cfg.mode == "divide":
        # Avoid divide-by-zero; produce a transmission-like image (1 => same as background)
        denom = np.clip(bkg, _safe_eps(), None)
        out = sig / denom
        # Optionally convert to optical density: OD = -log(out)
        # out = -np.log(np.clip(out, _safe_eps(), 1))
        # Normalize for display
        out = out / np.percentile(out, 99.5)
        out = np.clip(out, 0, 1)
    else:
        raise ValueError(f"Unknown mode: {cfg.mode}")

    # 5) Denoise (optional)
    if cfg.denoise_ksize and cfg.denoise_ksize >= 3:
        k = int(cfg.denoise_ksize) | 1  # ensure odd
        if out.ndim == 2:
            out = cv2.medianBlur((out*65535).astype(np.uint16), k).astype(np.float64) / 65535.0
        else:
            # apply per-channel
            chans = []
            for c in range(out.shape[2]):
                ch = cv2.medianBlur((out[...,c]*65535).astype(np.uint16), k).astype(np.float64) / 65535.0
                chans.append(ch)
            out = np.dstack(chans)

    return np.clip(out, 0, 1)

# ----------------------------- CLI -------------------------------

def parse_patch(s: str) -> Tuple[int,int,int,int]:
    parts = [int(v) for v in s.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("ref patch must be 'x0,y0,x1,y1'")
    x0,y0,x1,y1 = parts
    if not (x0 < x1 and y0 < y1):
        raise argparse.ArgumentTypeError("ref patch must satisfy x0<x1 and y0<y1")
    return x0,y0,x1,y1

def run_cli():
    import argparse
    parser = argparse.ArgumentParser(description="Background subtraction/division with normalization.")
    parser.add_argument("--signal", type=str, help="Path to signal image (with object of interest).")
    parser.add_argument("--background", type=str, help="Path to background image (baseline).")
    parser.add_argument("--dark", type=str, default=None, help="Path to dark frame (optional).")
    parser.add_argument("--flat", type=str, default=None, help="Path to flat-field image (optional).")
    parser.add_argument("--mode", choices=["subtract","divide"], default="subtract", help="Use 'subtract' for fluorescence; 'divide' for absorption.")
    parser.add_argument("--normalize", choices=["none","patch","hist"], default="patch", help="Normalization method to match exposure/gain.")
    parser.add_argument("--ref-patch", type=parse_patch, default=None, help="Reference patch 'x0,y0,x1,y1' for patch normalization.")
    parser.add_argument("--denoise-ksize", type=int, default=0, help="Median filter kernel size (odd). 0 to disable.")
    parser.add_argument("--output", type=str, default="corrected.png", help="Output image path.")
    parser.add_argument("--demo", action="store_true", help="Run synthetic demo instead of reading files.")
    args = parser.parse_args()

    if args.demo:
        demo_path = Path("demo_out.png")
        demo(demo_path)
        print(f"Demo image written to {demo_path.resolve()}")
        return

    if not args.signal or not args.background:
        parser.error("Please provide --signal and --background paths, or use --demo.")

    signal = _read_any_image(Path(args.signal))
    background = _read_any_image(Path(args.background))

    cfg = PipelineConfig(
        mode=args.mode,
        normalize=args.normalize,
        ref_patch=args.ref_patch,
        flat_field_path=Path(args.flat) if args.flat else None,
        dark_path=Path(args.dark) if args.dark else None,
        denoise_ksize=args.denoise_ksize
    )

    out = process(signal, background, cfg)
    _save_image(Path(args.output), out)
    print(f"Saved: {Path(args.output).resolve()}")

# ------------------------- Synthetic Demo ------------------------

def demo(out_path: Path = Path("demo_out.png")):
    """Create synthetic images to showcase subtraction with patch normalization."""
    H, W = 400, 600
    rng = np.random.default_rng(42)

    # Baseline scene: smooth gradient + fixed dust specks
    yy, xx = np.mgrid[0:H, 0:W]
    base = 0.2 + 0.4*(xx/W) + 0.1*np.sin(2*np.pi*yy/80)
    # add some fixed dust / reflections
    for (cx,cy,r,amp) in [(120,120,20,0.15),(420,260,16,0.12),(300,80,10,0.08)]:
        rr2 = (xx-cx)**2 + (yy-cy)**2
        base += amp * np.exp(-rr2/(2*r*r))
    base = np.clip(base, 0, 1)

    # Background frame (baseline) + shot noise
    background = np.clip(base + rng.normal(0, 0.005, size=base.shape), 0, 1)

    # Signal frame: add "fluorescent sphere" (Gaussian blob) + DIFFERENT exposure/gain
    sphere = 0.0*base
    cx, cy, r = 320, 200, 35
    rr2 = (xx-cx)**2 + (yy-cy)**2
    sphere += 0.5 * np.exp(-rr2/(2*r*r))  # additive fluorescence
    # simulate ISO/exposure change (global multiplicative factor)
    gain = 1.15
    signal = np.clip(gain*(base) + sphere, 0, 1)
    signal += rng.normal(0, 0.005, size=signal.shape)
    signal = np.clip(signal, 0, 1)

    # Use patch normalization away from the sphere
    ref_patch = (30, 300, 180, 380)

    cfg = PipelineConfig(mode="subtract", normalize="patch", ref_patch=ref_patch, denoise_ksize=3)
    out = process(signal, background, cfg)

    # Stack a quick visualization panel
    def to8(x):
        return (np.clip(x,0,1)*255+0.5).astype(np.uint8)
    panel = np.hstack([to8(background), to8(signal), to8(out)])
    cv2.putText(panel, "Background | Signal | Corrected", (10,20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,), 1, cv2.LINE_AA)
    # draw ref patch on panel (on middle segment)
    x0,y0,x1,y1 = ref_patch
    offx = background.shape[1]  # middle image offset
    cv2.rectangle(panel, (offx+x0,y0), (offx+x1,y1), (255,), 1)

    # Save demo
    encoded, buf = cv2.imencode('.png', panel)
    out_path.write_bytes(buf.tobytes())

# ----------------------------- Entry -----------------------------

if __name__ == "__main__":
    run_cli()
