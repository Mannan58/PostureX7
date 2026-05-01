# 🎨 GUI Visual Guide - GYM AI

## Exercise Selection Screen

This is what you'll see when you run the application:

```
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║                       💪 GYM AI TRAINER                                            ║
║                                                                                    ║
║            Choose Your Exercise & Start Training                                   ║
║                                                                                    ║
║ ════════════════════════════════════════════════════════════════════════════════  ║
║                                                                                    ║
║    ┌──────────────────────────┐  ┌──────────────────────────┐  ┌────────────────┐  ║
║    │                          │  │                          │  │                │  ║
║    │         🦵               │  │         🏋️               │  │      🤸        │  ║
║    │       (RED)              │  │       (TEAL)             │  │     (BLUE)     │  ║
║    │                          │  │                          │  │                │  ║
║    │       SQUATS             │  │      DEADLIFTS           │  │    PUSHUPS     │  ║
║    │                          │  │                          │  │                │  ║
║    │    Legs & Core           │  │    Full Body             │  │  Chest & Arms  │  ║
║    │                          │  │                          │  │                │  ║
║    │  ▶ START TRAINING ▶      │  │  ▶ START TRAINING ▶      │  │ ▶ START...     │  ║
║    │                          │  │                          │  │                │  ║
║    └──────────────────────────┘  └──────────────────────────┘  └────────────────┘  ║
║                                                                                    ║
║              (Hover effects on cards - they highlight when you move mouse)        ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
```

## Color Scheme

### Main Title (Cyan)
```
💪 GYM AI TRAINER
#00d4ff (Bright Cyan)
Large, Bold, Eye-catching
```

### Exercise Cards

#### Squats Card (Red Theme)
```
┌─ Red Bar (#ff6b6b) ─────────┐
│                              │
│         🦵 Emoji             │
│                              │
│       SQUATS                 │
│    (Bold White Text)         │
│                              │
│    Legs & Core               │
│   (Gray Description)         │
│                              │
│  ▶ START TRAINING ▶          │
│  (Red Button, Hover = Bright)│
│                              │
└──────────────────────────────┘
```

#### Deadlifts Card (Teal Theme)
```
┌─ Teal Bar (#4ecdc4) ────────┐
│                              │
│         🏋️ Emoji             │
│                              │
│      DEADLIFTS               │
│    (Bold White Text)         │
│                              │
│    Full Body                 │
│   (Gray Description)         │
│                              │
│  ▶ START TRAINING ▶          │
│  (Teal Button, Hover = Bright│
│                              │
└──────────────────────────────┘
```

#### Push-ups Card (Blue Theme)
```
┌─ Blue Bar (#45b7d1) ────────┐
│                              │
│         🤸 Emoji             │
│                              │
│       PUSHUPS                │
│    (Bold White Text)         │
│                              │
│    Chest & Arms              │
│   (Gray Description)         │
│                              │
│  ▶ START TRAINING ▶          │
│  (Blue Button, Hover = Bright│
│                              │
└──────────────────────────────┘
```

## Hover Animation

When you move your mouse over a card:

```
BEFORE HOVER:              AFTER HOVER:
┌──────────────┐          ┌═════════════════┐
│              │    →     │ ■ Highlight ■   │
│    CARD      │          │                 │
│              │          │    CARD         │
└──────────────┘          │                 │
                          └═════════════════┘
                        (Border highlights,
                         button appears pressed)
```

## Training Screen

Once you click an exercise, you'll see:

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║  AI GYM TRAINER                                      30 FPS    ║
║  ═══════════════════════════════════════════════════════════  ║
║                                                               ║
║                    [Live Camera Feed]                         ║
║                                                               ║
║               (Your body with skeleton overlay)               ║
║                                                               ║
║              Joints marked: • (Green = Good, Red = Bad)      ║
║              Angles shown:  ∠ (for key joints)               ║
║                                                               ║
║                                                               ║
║  ┌─────────────────────────────────────────────────────────┐ ║
║  │ REPS: 5    │  STAGE: DOWN  │  Knee: 87°  │  Good form!  │ ║
║  │ Left Side  │  SQUAT        │  Hip: 95°   │  ✓           │ ║
║  └─────────────────────────────────────────────────────────┘ ║
║                                                               ║
║  [Warnings appear here when form is incorrect]                ║
║  e.g., "Keep your back straight"                             ║
║                                                               ║
║  [Keyboard hints: Q=Exit, S=Squat, D=Deadlift, P=Pushup]     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

## Visual Elements Breakdown

### Color Psychology
- **Red (#ff6b6b)**: Energy, strength - Perfect for squats
- **Teal (#4ecdc4)**: Balance, strength - Good for full-body deadlifts
- **Blue (#45b7d1)**: Calm, endurance - Ideal for push-ups
- **Dark Background (#0f1419)**: Reduces eye strain
- **Cyan Accents (#00d4ff)**: High visibility for titles

### Typography Hierarchy

1. **Main Title** (Largest)
   ```
   💪 GYM AI TRAINER
   56pt Bold
   ```

2. **Subtitle** (Medium)
   ```
   Choose Your Exercise & Start Training
   18pt Regular
   ```

3. **Exercise Names** (Large)
   ```
   SQUATS / DEADLIFTS / PUSHUPS
   26pt Bold
   ```

4. **Descriptions** (Small)
   ```
   Legs & Core / Full Body / Chest & Arms
   13pt Regular
   ```

5. **Button Text** (Medium)
   ```
   ▶ START TRAINING ▶
   13pt Bold
   ```

## Responsive Design

### Screen Size Adaptation

**1200x750 Resolution (Default):**
- 3 cards fit perfectly side-by-side
- Optimal spacing and readability
- Professional appearance

**Larger Screens (1920x1080+):**
- Cards scale up
- More padding around elements
- Better for larger rooms

**Smaller Screens (1024x768):**
- Cards may wrap
- Still fully functional
- Buttons remain clickable

## Interactive Elements

### Buttons
```
Normal State:              Hover State:              Pressed State:
┌──────────────┐          ┌──────────────┐          ╔══════════════╗
│ START        │    →     │ START        │    →     ║ START        ║
│ TRAINING     │          │ TRAINING     │          ║ TRAINING     ║
└──────────────┘          └──────────────┘          ╚══════════════╝
(Flat)                    (Highlighted)             (Sunken)
```

### Cards
```
Normal:                    Hover:
┌──────────────┐          ┏══════════════┓
│   CONTENT    │    →     ┃   CONTENT    ┃
│              │          ┃              ┃
└──────────────┘          ┗══════════════┛
(Regular)                 (Border highlight)
```

## Window Layout Diagram

```
┌────────────────────────────────────────────────────┐
│                                                    │
│  ┌──────────────────────────────────────────────┐  │  40px
│  │  💪 GYM AI TRAINER                           │  │  padding
│  │  Choose Your Exercise & Start Training       │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ════════════════════════════════════════════════  │  Divider
│                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │  40px
│  │ SQUATS   │  │DEADLIFTS │  │ PUSHUPS  │        │  padding
│  │   🦵     │  │    🏋️     │  │   🤸     │        │
│  │ START    │  │  START   │  │  START   │        │
│  └──────────┘  └──────────┘  └──────────┘        │
│                                                    │
└────────────────────────────────────────────────────┘

Width: 1200px
Height: 750px
Centered on screen
```

## Color Values Reference

```
Primary Colors:
├─ Dark Background: #0f1419  (RGB: 15, 20, 25)
├─ Title Cyan: #00d4ff       (RGB: 0, 212, 255)
└─ Divider: #00d4ff          (RGB: 0, 212, 255)

Exercise Card Colors:
├─ Squats (Red)
│  ├─ Button: #ff6b6b        (RGB: 255, 107, 107)
│  └─ Card BG: #2d1f1f       (RGB: 45, 31, 31)
├─ Deadlifts (Teal)
│  ├─ Button: #4ecdc4        (RGB: 78, 205, 196)
│  └─ Card BG: #1f2d2b       (RGB: 31, 45, 43)
└─ Push-ups (Blue)
   ├─ Button: #45b7d1        (RGB: 69, 183, 209)
   └─ Card BG: #1f2a2d       (RGB: 31, 42, 45)

Text Colors:
├─ Primary Text: #ffffff     (RGB: 255, 255, 255)
├─ Secondary Text: #b0b8c0   (RGB: 176, 184, 192)
└─ Muted Text: #a0a8b0       (RGB: 160, 168, 176)
```

## Animation Details

### Button Hover Animation
```
Timeline:
0ms:     Button at normal state
100ms:   Border starts highlighting
200ms:   Full highlight effect
On Leave: Returns to normal over 100ms
```

### Card Hover Animation
```
Timeline:
0ms:     Card at normal state
150ms:   Border appears
250ms:   Full highlight effect
On Leave: Returns to normal over 150ms
```

## Accessibility Features

1. **Color Contrast**: All text meets WCAG AA standards
2. **Large Buttons**: Easy to click, ~25x12mm at 96 DPI
3. **Clear Labels**: All buttons and cards clearly labeled
4. **Icon Support**: Emojis provide visual identification
5. **Dark Theme**: Reduces eye strain during extended use

## Mobile/Tablet Considerations

While designed for desktop, the GUI can be adapted:
- Touch-friendly button sizes (50x50px minimum)
- Vertical stack on smaller screens
- Responsive text sizing
- Gesture support possible

---

**Design Philosophy**: Modern, Professional, User-Friendly
**Target Audience**: Fitness enthusiasts using desktop/laptop
**Accessibility**: High contrast, clear typography, intuitive layout

Ready to start training? The GUI makes it easy! 💪
