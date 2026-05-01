# ⚙️ Configuration Guide - GYM AI

## Advanced Configuration

This guide covers advanced settings and optimizations for the GYM AI trainer.

## Main.py Settings

### 1. Color Scheme Customization

Located at the top of `Main.py` (~lines 14-24):

```python
GREEN = (40, 220, 90)      # Good form color
RED = (40, 40, 235)        # Bad form color
WHITE = (240, 240, 240)    # Text color
BLACK = (0, 0, 0)          # Background
DARK = (18, 22, 24)        # Dark background
YELLOW = (0, 210, 255)     # Warnings
CYAN = (255, 210, 80)      # Alerts
MUTED = (150, 160, 160)    # Muted text
```

**Format**: BGR (Blue, Green, Red) - OpenCV uses BGR not RGB

### 2. Exercise Detection Parameters

#### Squat Settings (~line 223-225):
```python
def _update_squat(self, angles: Dict[str, float]) -> None:
    knee = angles["knee"]
    if knee < 95:              # Angle for "DOWN" stage
        self._confirm_stage("DOWN")
    elif knee > 155 and self.state.stage == "DOWN":  # Angle for "UP"
        self._confirm_stage("UP", count_rep=True)
```

**Adjustment Tips:**
- Lower `95` = deeper squats required
- Higher `155` = easier to count as "up"

#### Deadlift Settings (~line 244-249):
```python
def _update_deadlift(self, angles: Dict[str, float]) -> None:
    hip = angles["hip"]
    if hip < 105:              # Hip angle for "DOWN" (bent)
        self._confirm_stage("DOWN")
    elif hip > 165 and self.state.stage == "DOWN":  # Hip angle for "UP"
        self._confirm_stage("UP", count_rep=True)
```

#### Pushup Settings (~line 299-307):
```python
def _update_pushup(self, angles: Dict[str, float]) -> None:
    elbow_proxy = angles["back"]
    if elbow_proxy < 110:              # Arms bent
        self._confirm_stage("DOWN")
    elif elbow_proxy > 150 and self.state.stage == "DOWN":  # Arms extended
        self._confirm_stage("UP", count_rep=True)
```

### 3. Form Validation Thresholds

#### Squat Form Checks (~line 252-261):
```python
def _squat_errors(self, ...):
    if angles["torso"] < 150:  # Back angle threshold
        warnings.append("Straighten your back")
    
    if self.state.stage == "DOWN" and angles["knee"] > 100:
        warnings.append("Go deeper")  # Depth check
```

**Customization:**
- `150`: Back angle threshold (higher = stricter)
- `100`: Knee depth during squat (higher = less depth required)

#### Deadlift Form Checks (~line 270-305):
```python
# Multiple validation checks with thresholds:
if bottom_position and shoulder_bar_offset > 0.16:
    warnings.append("Shoulders over bar")
```

**Key Thresholds:**
- `0.16`: Shoulder position relative to bar
- `0.12`: Hand position relative to bar
- `115` / `165`: Hip angle ranges

### 4. Tracking Quality Settings

Location: ~line 32
```python
MIN_TRACKING_QUALITY = 0.58  # Range: 0.0 to 1.0
```

**Meaning:**
- `0.58`: Minimum confidence in pose detection
- Lower = More lenient (may give false results)
- Higher = More strict (may miss reps)

**Recommended Values:**
- Poor lighting: 0.40-0.50
- Normal conditions: 0.55-0.65
- Excellent conditions: 0.65-0.75

### 5. Stability Frames

Location: ~line 29-30
```python
STABLE_FRAMES_FOR_STAGE = 3   # Frames to confirm stage change
STABLE_FRAMES_FOR_WARNING = 2 # Frames to show warning
```

**Impact:**
- Higher = More stable but slower response
- Lower = Faster response but more jittery warnings

### 6. Voice Coach Settings

Location: ~line 605-606
```python
voice = VoiceCoach(cooldown_seconds=2.0, rate=175)
```

**Parameters:**
- `cooldown_seconds`: Minimum time between same voice message (prevent spam)
- `rate`: Speech speed in words per minute
  - 100-150: Slow and clear
  - 175-200: Normal
  - 250+: Fast

### 7. Smoothing Window

Location: ~line 604
```python
analyzer = ExerciseAnalyzer(smoothing_window=12)
```

**Effect on Angles:**
- Smoothing window smooths pose angles over N frames
- Default: 12 frames
- Lower (8): Responsive, jerky
- Higher (15): Smooth, delayed

**Recommendation:** 12 for 30 FPS, adjust to `FPS/2.5` for other frame rates

### 8. Camera Settings

#### In Code (Main.py):
```python
# Line ~624
cv2.namedWindow("AI Gym Trainer", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("AI Gym Trainer", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
```

**Options:**
- `cv2.WINDOW_NORMAL`: Resizable window
- `cv2.WINDOW_FULLSCREEN`: Full screen mode
- `cv2.WINDOW_AUTOSIZE`: Auto size to content

#### Command Line:
```bash
python Main.py --camera 0  # Webcam
python Main.py --camera http://192.168.1.5:4747/video  # DroidCam
python Main.py --fallback-camera none  # Disable fallback
```

## GUI Customization (gui.py)

### Window Size
Location: ~line 16
```python
self.root.geometry("1200x750")  # Width x Height
```

### Color Scheme
Location: ~line 61-77
```python
# Colors for exercise cards
{
    "color": "#ff6b6b",        # Main button color
    "bg_color": "#2d1f1f",     # Card background
}
```

**Pre-defined Colors:**
- Red (#ff6b6b) - Squats
- Teal (#4ecdc4) - Deadlifts
- Blue (#45b7d1) - Push-ups

### Font Sizes
Location: Various
```python
font=("Arial", 56, "bold")     # Main title
font=("Arial", 18)             # Subtitle
font=("Arial", 26, "bold")     # Exercise name
font=("Arial", 13, "bold")     # Button text
```

### Button Styling
Location: ~line 128-139
```python
btn = tk.Button(
    card,
    text="▶ START TRAINING ▶",
    bg=color,
    fg="#000000",
    padx=25,           # Horizontal padding
    pady=12,           # Vertical padding
    font=("Arial", 13, "bold")
)
```

## Performance Tuning

### For Slow Performance

1. **Reduce Smoothing:**
   ```python
   analyzer = ExerciseAnalyzer(smoothing_window=8)
   ```

2. **Lower Tracking Quality:**
   ```python
   MIN_TRACKING_QUALITY = 0.40
   ```

3. **Increase Stable Frames:**
   ```python
   STABLE_FRAMES_FOR_STAGE = 5
   ```

### For Better Accuracy

1. **Increase Smoothing:**
   ```python
   analyzer = ExerciseAnalyzer(smoothing_window=15)
   ```

2. **Higher Tracking Quality:**
   ```python
   MIN_TRACKING_QUALITY = 0.70
   ```

3. **Stricter Form Checks:**
   - Adjust angle thresholds higher
   - Reduce offset tolerances

## Custom Exercise Addition

To add a new exercise:

1. **Add update method:**
```python
def _update_custom_exercise(self, angles: Dict[str, float]) -> None:
    # Detect movement phases
    if some_angle < threshold:
        self._confirm_stage("PHASE1")
    elif another_angle > threshold and self.state.stage == "PHASE1":
        self._confirm_stage("PHASE2", count_rep=True)
```

2. **Add error checking:**
```python
def _custom_exercise_errors(self, angles, ids, warnings, error_joints, error_segments):
    if angles["something"] < expected:
        warnings.append("Correction message")
        # Mark joints/segments for visualization
```

3. **Update main analyzer:**
```python
elif self.exercise == "CUSTOM":
    self._update_custom_exercise(angles)
    self._custom_exercise_errors(...)
```

4. **Add to GUI:**
Edit `gui.py` exercises list to include new exercise

5. **Update argument parser:**
```python
parser.add_argument(
    "--exercise",
    choices=("squat", "deadlift", "pushup", "custom"),
    default="squat"
)
```

## Environment Variables

Create a `.env` file for persistent configuration (optional):

```
MIN_TRACKING_QUALITY=0.58
SMOOTHING_WINDOW=12
VOICE_RATE=175
VOICE_COOLDOWN=2.0
```

Load in code:
```python
from dotenv import load_dotenv
load_dotenv()
quality = float(os.getenv("MIN_TRACKING_QUALITY", "0.58"))
```

## Logging Configuration

Add to Main.py for debugging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gym_ai.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.debug(f"Exercise: {self.exercise}, Stage: {self.state.stage}, Reps: {self.state.reps}")
```

## Testing Custom Settings

Create `test_config.py`:
```python
from Main import ExerciseAnalyzer

# Test with custom settings
analyzer = ExerciseAnalyzer(smoothing_window=15)
analyzer.switch("SQUAT")

# Test form validation
test_angles = {
    "knee": 90,
    "hip": 120,
    "back": 160,
    # ... other angles
}

state = analyzer.update({}, "left")  # Would need real landmarks
print(f"Warnings: {state.warnings}")
print(f"Reps: {state.reps}")
```

---

For more information, see README.md and QUICKSTART.md

Last Updated: April 2026
