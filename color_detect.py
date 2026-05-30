"""
Color Detection App  |  Task 1
================================
Double-click any pixel → exact color name via RGB Manhattan-distance matching (CSV)
Use HSV trackbars     → isolate & highlight a color range across the whole image

Tech : Python, OpenCV, NumPy, pandas
Usage: python color_detect.py --image pic2.jpg
       python color_detect.py --image pic2.jpg --csv colors.csv
"""

import cv2
import numpy as np
import pandas as pd
import argparse
import os
import sys

# ── Load color database ───────────────────────────────────────────────────────
def load_colors(csv_path: str) -> pd.DataFrame:
    index = ['color', 'color_name', 'hex', 'R', 'G', 'B']
    df = pd.read_csv(csv_path, names=index, header=None)
    # coerce numeric columns
    for col in ('R', 'G', 'B'):
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=['R', 'G', 'B'], inplace=True)
    df = df.reset_index(drop=True)
    return df

# ── Color name lookup (Manhattan distance — same as reference) ────────────────
def get_color_name(R: int, G: int, B: int, df: pd.DataFrame) -> str:
    diff = (df['R'] - R).abs() + (df['G'] - G).abs() + (df['B'] - B).abs()
    idx  = diff.idxmin()
    return df.loc[idx, 'color_name']

# ── HSV trackbar helpers ──────────────────────────────────────────────────────
def nothing(_):
    pass

HSV_PRESETS = {
    ord('r'): ("Red",    [0,  120,  70], [10,  255, 255]),
    ord('g'): ("Green",  [35,  50,  50], [85,  255, 255]),
    ord('b'): ("Blue",   [101, 50,  50], [130, 255, 255]),
    ord('y'): ("Yellow", [20, 100,  70], [34,  255, 255]),
    ord('p'): ("Purple", [131, 50,  50], [160, 255, 255]),
    ord('o'): ("Orange", [11, 100,  70], [25,  255, 255]),
    ord('c'): ("Cyan",   [86,  50,  50], [100, 255, 255]),
}

def create_trackbars(win: str):
    cv2.createTrackbar("H Min", win, 0,   180, nothing)
    cv2.createTrackbar("H Max", win, 180, 180, nothing)
    cv2.createTrackbar("S Min", win, 0,   255, nothing)
    cv2.createTrackbar("S Max", win, 255, 255, nothing)
    cv2.createTrackbar("V Min", win, 0,   255, nothing)
    cv2.createTrackbar("V Max", win, 255, 255, nothing)

def set_preset(win: str, lo: list, hi: list):
    cv2.setTrackbarPos("H Min", win, lo[0])
    cv2.setTrackbarPos("H Max", win, hi[0])
    cv2.setTrackbarPos("S Min", win, lo[1])
    cv2.setTrackbarPos("S Max", win, hi[1])
    cv2.setTrackbarPos("V Min", win, lo[2])
    cv2.setTrackbarPos("V Max", win, hi[2])

def get_trackbar_values(win: str):
    return (
        cv2.getTrackbarPos("H Min", win),
        cv2.getTrackbarPos("H Max", win),
        cv2.getTrackbarPos("S Min", win),
        cv2.getTrackbarPos("S Max", win),
        cv2.getTrackbarPos("V Min", win),
        cv2.getTrackbarPos("V Max", win),
    )

# ── Shared mouse state ────────────────────────────────────────────────────────
mouse = {"x": 0, "y": 0, "clicked": False, "r": 0, "g": 0, "b": 0}

def mouse_callback(event, x, y, flags, param):
    """Double-click → capture pixel color  |  Move → track position."""
    if event == cv2.EVENT_LBUTTONDBLCLK:
        img = param["img"]
        h, w = img.shape[:2]
        x, y = np.clip(x, 0, w-1), np.clip(y, 0, h-1)
        b, g, r = img[y, x]
        mouse.update({"x": x, "y": y, "clicked": True,
                      "r": int(r), "g": int(g), "b": int(b)})
    elif event == cv2.EVENT_MOUSEMOVE:
        mouse["x"], mouse["y"] = x, y

# ── HUD drawing ───────────────────────────────────────────────────────────────
def draw_click_banner(img, r, g, b, name):
    """Replicates the reference code's color banner at the top."""
    cv2.rectangle(img, (20, 20), (600, 60), (b, g, r), -1)
    text = f"{name}   R={r}  G={g}  B={b}"
    color = (0, 0, 0) if (r + g + b) >= 600 else (255, 255, 255)
    cv2.putText(img, text, (30, 47), cv2.FONT_HERSHEY_SIMPLEX,
                0.75, color, 2, cv2.LINE_AA)

def draw_hsv_hud(img, hmin, hmax, smin, smax, vmin, vmax, pixel_count, preset_name):
    """Semi-transparent HSV info panel at bottom."""
    h, w = img.shape[:2]
    overlay = img.copy()
    cv2.rectangle(overlay, (0, h-110), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)
    lines = [
        f"HSV Filter: [{hmin},{smin},{vmin}] → [{hmax},{smax},{vmax}]   |  Preset: {preset_name}",
        f"Matched pixels: {pixel_count:,}",
        "Keys: [r]Red [g]Green [b]Blue [y]Yellow [p]Purple [o]Orange [c]Cyan   [s]Save  [q]Quit",
        "Double-click any pixel to identify its color name",
    ]
    for i, line in enumerate(lines):
        cv2.putText(img, line, (10, h - 85 + i*22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (180, 255, 180), 1, cv2.LINE_AA)

# ── Main ──────────────────────────────────────────────────────────────────────
def run(image_path: str, csv_path: str, headless: bool = False):
    # --- load image ---
    if not os.path.exists(image_path):
        sys.exit(f"[ERROR] Image not found: {image_path}")
    img_orig = cv2.imread(image_path)
    if img_orig is None:
        sys.exit(f"[ERROR] Cannot read: {image_path}")
    img_orig = cv2.resize(img_orig, (800, 600))

    # --- load CSV ---
    if not os.path.exists(csv_path):
        sys.exit(f"[ERROR] CSV not found: {csv_path}")
    df = load_colors(csv_path)
    print(f"[OK] Loaded {len(df)} colors from {csv_path}")

    WIN = "Color Detection"
    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    create_trackbars(WIN)
    cv2.setMouseCallback(WIN, mouse_callback, {"img": img_orig})

    img = img_orig.copy()
    preset_name  = "None"
    shot_count   = 0
    saved_frames = []           # for headless demo

    # ── headless presets to capture ──────────────────────────────────────────
    headless_passes = [
        ("Red",    [0,  120, 70], [10,  255,255]),
        ("Green",  [35,  50, 50], [85,  255,255]),
        ("Blue",   [101, 50, 50], [130, 255,255]),
    ] if headless else []

    pass_idx = 0

    while True:
        img = img_orig.copy()

        # ── apply headless preset if needed ──────────────────────────────────
        if headless and pass_idx < len(headless_passes):
            pname, lo, hi = headless_passes[pass_idx]
            set_preset(WIN, lo, hi)
            preset_name = pname

        # ── HSV masking ───────────────────────────────────────────────────────
        hmin, hmax, smin, smax, vmin, vmax = get_trackbar_values(WIN)
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask    = cv2.inRange(img_hsv,
                              np.array([hmin, smin, vmin]),
                              np.array([hmax, smax, vmax]))
        result  = cv2.bitwise_and(img, img, mask=mask)

        # Contour bounding boxes
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) > 400:
                x, y, bw, bh = cv2.boundingRect(cnt)
                cv2.rectangle(img, (x, y), (x+bw, y+bh), (0, 255, 0), 2)

        pixel_count = int(np.sum(mask > 0))

        # ── double-click banner (reference style) ─────────────────────────────
        if mouse["clicked"]:
            name = get_color_name(mouse["r"], mouse["g"], mouse["b"], df)
            draw_click_banner(img, mouse["r"], mouse["g"], mouse["b"], name)

        # ── HSV HUD ───────────────────────────────────────────────────────────
        draw_hsv_hud(img, hmin, hmax, smin, smax, vmin, vmax, pixel_count, preset_name)

        # ── compose 2-panel display: annotated | result ───────────────────────
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        panel    = np.hstack([img, result])
        lbl_y    = panel.shape[0] - 5
        for col_x, lbl in [(10, "Original + Overlay"), (810, "Detected Result")]:
            cv2.putText(panel, lbl, (col_x, lbl_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100,255,255), 1)

        if not headless:
            cv2.imshow(WIN, panel)
        else:
            saved_frames.append((preset_name, panel.copy()))

        # ── key handling / headless advancement ───────────────────────────────
        key = cv2.waitKey(30) & 0xFF if not headless else 0xFF

        if headless:
            pass_idx += 1
            if pass_idx >= len(headless_passes):
                break
            continue

        if key == ord('q') or key == 27:
            break
        elif key == ord('s'):
            shot_count += 1
            fname = f"screenshot_{shot_count}.png"
            cv2.imwrite(fname, panel)
            print(f"[Saved] {fname}")
        elif key in HSV_PRESETS:
            preset_name, lo, hi = HSV_PRESETS[key]
            set_preset(WIN, lo, hi)

    cv2.destroyAllWindows()

    # ── save headless frames ──────────────────────────────────────────────────
    for i, (pname, frame) in enumerate(saved_frames, 1):
        fname = f"screenshot_{i}.png"
        cv2.imwrite(fname, frame)
        print(f"[Saved] screenshot_{i}.png  ({pname})")

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Color Detection — CSV + HSV trackbars")
    parser.add_argument("--image",   default="pic2.jpg",    help="Input image path")
    parser.add_argument("--csv",     default="colors.csv",  help="Color name CSV path")
    parser.add_argument("--headless",action="store_true",   help="Auto-save 3 demos and exit")
    args = parser.parse_args()
    run(args.image, args.csv, headless=args.headless)
