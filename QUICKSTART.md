# 🚀 Quick Start Guide - GYM AI

## First Time Setup (5 minutes)

### Step 1: Install Dependencies
Open PowerShell in the GYM AI folder and run:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 2: Start the Application
#### Option A: Use the Launcher (Easiest)
Double-click: `RUN_GYM_AI.bat`

#### Option B: Use PowerShell
```powershell
.venv\Scripts\Activate.ps1
python Main.py
```

## Using the GUI

### Exercise Selection Screen
When you run the application, you'll see a beautiful menu with three options:

1. **🦵 SQUATS** (Red)
   - Great for legs and core
   - Click to start squat training

2. **🏋️ DEADLIFTS** (Teal)
   - Full body workout
   - Click to start deadlift training

3. **🤸 PUSHUPS** (Blue)
   - Chest and arms
   - Click to start pushup training

### During Training

**What You'll See:**
- Real-time video feed from your camera
- Rep counter (how many reps you've completed)
- Joint angles (hip, knee, shoulder angles)
- Form feedback (green = good, red = needs improvement)
- Messages on screen (guidance and corrections)

**Voice Feedback:**
- The app will speak corrections like "Keep your back straight"
- Encouragement messages when you maintain good form
- Automatic rep announcements

**Controls:**
- Press **Q** or **ESC** to exit
- Press **S** for Squats (switch mid-workout)
- Press **D** for Deadlifts (switch mid-workout)
- Press **P** for Push-ups (switch mid-workout)

## Tips for Best Performance

### Setup Your Camera
1. **Distance**: Stand 6-10 feet from camera
2. **Height**: Camera should be at chest level
3. **Angle**: Point camera straight at your body
4. **Lighting**: Use good lighting (natural light is best)
5. **Background**: Use a plain background if possible

### Exercise Tips

**SQUATS:**
- Place feet shoulder-width apart
- Keep chest up and back straight
- Go as deep as comfortable
- Push through your heels

**DEADLIFTS:**
- Keep bar close to your body
- Maintain neutral spine throughout
- Drive through your heels
- Full hip extension at the top

**PUSHUPS:**
- Keep body straight from head to heels
- Lower until chest nearly touches ground
- Push back up to full arm extension
- Maintain core tension

## Troubleshooting

### GUI Won't Show
**Problem**: Exercise selection menu doesn't appear

**Solution**:
1. Ensure Tkinter is installed: `python -m tkinter`
2. Try running directly: `python gui.py`
3. Check for error messages in PowerShell

### No Camera Feed
**Problem**: Camera window doesn't open or shows black

**Solution**:
1. Check camera connection
2. Try with default camera: `python Main.py --camera 0`
3. Close other applications using camera
4. Restart the application

### Poor Form Tracking
**Problem**: Angles are incorrect or tracking is jittery

**Solution**:
1. Improve lighting
2. Move closer to camera
3. Wear contrasting clothing
4. Stand more perpendicular to camera

### No Voice Feedback
**Problem**: App doesn't speak corrections

**Solution**:
1. Check Windows volume settings
2. Ensure speakers are connected
3. Test: `python -c "import pyttsx3; pyttsx3.init().say('test').runAndWait()"`

## Advanced Options

### Custom Camera Source
For DroidCam on your phone:
```powershell
python Main.py --camera http://192.168.1.100:4747/video
```
(Replace IP with your phone's IP)

### Adjust Smoothing (Advanced)
Edit Main.py line ~615 to adjust angle smoothing:
- Lower value (8): More responsive, jittery
- Higher value (15): Smoother, slower response

## Performance Expectations

### Minimum Setup
- Intel i3 or AMD Ryzen 3
- 4GB RAM
- Standard webcam
- **FPS**: 15-25

### Recommended Setup
- Intel i5/i7 or AMD Ryzen 5/7
- 8GB+ RAM
- 1080p+ webcam
- **FPS**: 25-35+

### Optimal Setup
- Intel i7+ or Ryzen 7+
- 16GB+ RAM
- 1440p+ or high-FPS camera
- GPU (RTX/Radeon)
- **FPS**: 35+

## File Structure

```
GYM AI/
├── Main.py                 ← Main application (run this)
├── gui.py                  ← Exercise selection menu
├── pose_module.py          ← Pose detection
├── utils.py                ← Helper functions
├── README.md               ← Full documentation
├── QUICKSTART.md           ← This file
├── requirements.txt        ← Dependencies
├── RUN_GYM_AI.bat          ← Easy launcher
└── pose_landmarker_lite.task ← AI model

Virtual Environment:
└── .venv/                  ← Created after setup
```

## Next Steps

1. ✅ Install dependencies
2. ✅ Run the application
3. ✅ Try each exercise
4. 💪 Start training!

## Getting Help

If you encounter issues:
1. Check this Quick Start Guide
2. Check README.md for detailed documentation
3. Verify all dependencies are installed
4. Check Python version (3.8+ required)
5. Try running from PowerShell to see error messages

## Version Info

- **Application**: GYM AI v2.0 with GUI
- **Python Required**: 3.8 or higher
- **GUI Framework**: Tkinter (built-in)
- **AI Model**: MediaPipe Pose v0.4+

---

Ready to start training? Run `RUN_GYM_AI.bat` now! 💪

Questions? Check README.md for more details.
