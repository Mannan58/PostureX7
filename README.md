# 💪 GYM AI - AI-Powered Fitness Trainer

An advanced real-time fitness training assistant that uses AI pose detection to track your exercise form, give live feedback on your posture and angle, make sure you do it perfectly,count reps, and provide real-time feedback.

## Features

✨ **Beautiful GUI Interface** - Modern exercise selection menu with attractive graphics
🎯 **Real-time Pose Detection** - Uses MediaPipe to detect body landmarks
🏋️ **Multiple Exercises** - Squats, Deadlifts, and Push-ups with form analysis
🎤 **Voice Feedback** - Real-time audio coaching with form corrections
📊 **Rep Counter** - Automatic rep counting with visual display
⚡ **High Performance** - Optimized for smooth 30+ FPS performance
🎥 **Flexible Camera Support** - Works with webcam or DroidCam

## Supported Exercises

### 🦵 Squats
- Tracks knee and hip angles
- Monitors back alignment
- Provides feedback on depth and posture
- Real-time rep counter

### 🏋️ Deadlifts
- Tracks hip hinge movement
- Monitors bar path alignment
- Checks for proper form at top and bottom
- Accuracy score calculation

### 🤸 Push-ups
- Tracks arm extension
- Monitors back alignment
- Ensures proper form throughout movement
- Rep counting with feedback

## Installation

### 1. Clone or Download the Project
```bash
cd "c:\Users\DELL\Desktop\GYM AI"
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

Or manually install:
```bash
pip install opencv-python mediapipe pyttsx3 numpy
```

## Usage

### Option 1: GUI Mode (Recommended)
Simply run the main script to open the exercise selection menu:
```bash
python Main.py
```

This will:
1. Open a beautiful exercise selection window
2. Let you choose between Squats, Deadlifts, or Push-ups
3. Open your camera
4. Start real-time fitness coaching

### Option 2: Command Line Mode
Run with specific exercise:
```bash
python Main.py --exercise squat --camera 0
```

### Available Command Line Arguments
- `--exercise {squat,deadlift,pushup}` - Choose exercise (default: squat)
- `--camera` - Camera source (default: 0)
  - Use `0` for built-in webcam
  - Use `http://IP:4747/video` for DroidCam
- `--fallback-camera` - Fallback camera if primary fails (default: 0)

### In-Game Controls
- **Q** or **ESC** - Exit application
- **S** - Switch to Squats
- **D** - Switch to Deadlifts
- **P** - Switch to Push-ups

## How It Works

### Pose Detection
The system uses MediaPipe's pose landmarker to detect 33 body landmarks in real-time:
- Shoulders, hips, knees, ankles
- Wrists and other key joints
- Provides 3D coordinates and visibility scores

### Exercise Tracking
For each exercise, the system:
1. Calculates angles between key joints
2. Smooths angle data to reduce jitter
3. Compares against form thresholds
4. Tracks movement stages (UP/DOWN)
5. Counts completed reps

### Real-time Feedback
- **Visual Feedback**: Colored overlays show correct (green) and incorrect (red) form
- **Audio Feedback**: Voice announcements for errors and encouragement
- **On-screen Display**: 
  - Rep counter
  - Angle measurements
  - Form quality score
  - FPS counter
  - Warning messages

## File Structure

```
GYM AI/
├── Main.py                      # Main application with exercise logic
├── gui.py                       # Beautiful GUI interface
├── pose_module.py              # MediaPipe pose detection wrapper
├── utils.py                    # Utility functions for angle calculation
├── pose_landmarker_lite.task   # MediaPipe pose model
└── README.md                   # This file
```

## Configuration

### Smoothing Window
Adjust pose smoothing in `Main.py` line ~615:
```python
analyzer = ExerciseAnalyzer(smoothing_window=12)  # Default: 12 frames
```
- Higher values = more stable but slower response
- Lower values = faster response but more jittery

### Voice Settings
Customize voice in `Main.py` line ~605:
```python
voice = VoiceCoach(cooldown_seconds=2.0, rate=175)
```
- `cooldown_seconds`: Minimum time between voice alerts
- `rate`: Speech speed (default: 175 words per minute)

### Tracking Quality Threshold
Minimum confidence for tracking in `Main.py` line ~32:
```python
MIN_TRACKING_QUALITY = 0.58  # 0.0 to 1.0
```

## Performance Tips

1. **Lighting**: Use good lighting for best results
2. **Camera Position**: Position camera at chest height
3. **Distance**: Stand 6-10 feet from camera
4. **Clothing**: Wear fitted clothes for better pose detection
5. **Background**: Use solid background for cleaner tracking

## Troubleshooting

### GUI Window Won't Open
- Ensure Tkinter is installed: `python -m tkinter`
- On Linux: `sudo apt-get install python3-tk`

### No Camera Feed
- Check camera connection
- Try: `python Main.py --camera 0`
- For DroidCam: Use IP format like `http://192.168.1.100:4747/video`

### Voice Feedback Not Working
- Check system audio settings
- Verify pyttsx3 is installed: `pip install pyttsx3`
- On Windows: Ensure TTS engines are available in Settings > Speech

### Poor Pose Tracking
- Improve lighting
- Move closer to camera
- Wear contrasting clothing
- Check if pose_landmarker_lite.task exists

### Slow Performance
- Reduce smoothing_window value
- Lower camera resolution
- Close other applications
- Update GPU drivers

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Q / ESC | Exit application |
| S | Switch to Squats |
| D | Switch to Deadlifts |
| P | Switch to Push-ups |

## Requirements

- Python 3.8+
- Webcam or DroidCam
- 4GB+ RAM
- Decent processor (i5/Ryzen 5 or better recommended)

## Dependencies

- **opencv-python**: Video capture and rendering
- **mediapipe**: Pose detection
- **pyttsx3**: Text-to-speech voice feedback
- **numpy**: Numerical computations
- **tkinter**: GUI (built-in with Python)

## Tips for Best Results

### Squat Form
- Maintain upright posture
- Go deeper for better form feedback
- Keep feet aligned with camera

### Deadlift Form
- Keep bar close to body
- Maintain neutral spine
- Full hip extension at top

### Push-up Form
- Keep body straight
- Full arm extension
- Controlled descent

## License

This project is provided as-is for personal fitness training.

## Contributing

Feel free to modify and improve the code for your needs!

## Version

Current Version: 2.0 (With GUI Interface)

---

Made with ❤️ for fitness enthusiasts! 💪
