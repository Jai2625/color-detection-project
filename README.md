# 🎨 Color Detection App — Task 1

Identifies colors in images using two complementary techniques:

1. **Double-click** any pixel → looks up the closest named color from a CSV database using RGB Manhattan-distance matching  
2. **HSV trackbars** → isolate and highlight a color range across the whole image with live bounding boxes

---

## Setup

```bash
pip install opencv-python numpy pandas
```

## Usage

```bash
python color_detect.py --image pic2.jpg
python color_detect.py --image pic2.jpg --csv colors.csv
```

## How It Works

### Technique 1 — Named Color Matching 
Double-clicking samples the pixel's R, G, B values, then searches every row of `colors.csv` for the minimum Manhattan distance:
```
distance = |R - csv_R| + |G - csv_G| + |B - csv_B|
```
The closest match is displayed in a color banner at the top of the image.

### Technique 2 — HSV Range Filtering
The image is converted to HSV color space. Six trackbars define a lower and upper HSV bound. `cv2.inRange()` produces a binary mask; contours are drawn as green bounding boxes on matched regions.

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `r` | Preset → Red |
| `g` | Preset → Green |
| `b` | Preset → Blue |
| `y` | Preset → Yellow |
| `p` | Preset → Purple |
| `o` | Preset → Orange |
| `c` | Preset → Cyan |
| `s` | Save screenshot |
| `q` / `Esc` | Quit |
| Double-click | Identify pixel color |

## Files

| File | Description |
|---|---|
| `color_detect.py` | Main application |
| `colors.csv` | 130 named colors (color, color_name, hex, R, G, B) |
| `sample.jpg` | Test image with 6 color regions |
| `screenshot_1.png` | Demo — Red detection |
| `screenshot_2.png` | Demo — Green detection |
| `screenshot_3.png` | Demo — Blue detection |

