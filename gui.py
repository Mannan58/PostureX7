import tkinter as tk
from tkinter import font
import sys
from typing import Optional


import tkinter as tk
from tkinter import font
import sys
from typing import Optional


class ExerciseSelectionGUI:
    """Modern exercise selection interface with attractive graphics."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GYM AI - Exercise Selection")
        self.root.geometry("1200x750")
        self.root.config(bg="#0f1419")
        self.root.resizable(False, False)
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        
        self.selected_exercise: Optional[str] = None
        self.setup_ui()
        
    def setup_ui(self):
        """Create the main UI with title and exercise cards."""
        # Title Section
        title_frame = tk.Frame(self.root, bg="#0f1419")
        title_frame.pack(pady=40)
        
        # Main Title
        title = tk.Label(
            title_frame,
            text="💪 GYM AI TRAINER",
            font=("Arial", 56, "bold"),
            bg="#0f1419",
            fg="#00d4ff"
        )
        title.pack()
        
        # Subtitle
        subtitle = tk.Label(
            title_frame,
            text="Choose Your Exercise & Start Training",
            font=("Arial", 18),
            bg="#0f1419",
            fg="#b0b8c0"
        )
        subtitle.pack(pady=15)
        
        # Divider line
        divider = tk.Frame(self.root, bg="#00d4ff", height=2)
        divider.pack(fill=tk.X, padx=50)
        
        # Exercises Container with Canvas for scrolling
        canvas_container = tk.Frame(self.root, bg="#0f1419")
        canvas_container.pack(pady=40, padx=40, fill=tk.BOTH, expand=True)
        
        # Create canvas for horizontal scrolling
        canvas = tk.Canvas(canvas_container, bg="#0f1419", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_container, orient=tk.HORIZONTAL, command=canvas.xview)
        
        exercises_frame = tk.Frame(canvas, bg="#0f1419")
        exercises_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=exercises_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)
        
        canvas.pack(fill=tk.BOTH, expand=True)
        scrollbar.pack(fill=tk.X)
        
        exercises = [
            {
                "name": "SQUATS",
                "code": "SQUAT",
                "emoji": "🦵",
                "color": "#ff6b6b",
                "bg_color": "#2d1f1f",
                "description": "Legs & Core"
            },
            {
                "name": "DEADLIFTS",
                "code": "DEADLIFT",
                "emoji": "🏋️",
                "color": "#4ecdc4",
                "bg_color": "#1f2d2b",
                "description": "Full Body"
            },
            {
                "name": "PUSHUPS",
                "code": "PUSHUP",
                "emoji": "🤸",
                "color": "#45b7d1",
                "bg_color": "#1f2a2d",
                "description": "Chest & Arms"
            },
            {
                "name": "FRONT SQUATS",
                "code": "FRONT_SQUAT",
                "emoji": "🦵",
                "color": "#ff8c42",
                "bg_color": "#2d2419",
                "description": "Quads Focus"
            },
            {
                "name": "LEANING LUNGE",
                "code": "LEANING_LUNGE",
                "emoji": "🚶",
                "color": "#95e1d3",
                "bg_color": "#1f2d2a",
                "description": "Leg & Balance"
            },
            {
                "name": "BULGARIAN SQUAT",
                "code": "BULGARIAN",
                "emoji": "🪜",
                "color": "#f38181",
                "bg_color": "#2d1f25",
                "description": "Single Leg"
            },
            {
                "name": "HYBRID DEADLIFT",
                "code": "HYBRID_DEADLIFT",
                "emoji": "⚙️",
                "color": "#aa96da",
                "bg_color": "#2a1f2d",
                "description": "Full Body Power"
            },
            {
                "name": "REVERSE LUNGE",
                "code": "REVERSE_LUNGE",
                "emoji": "🔙",
                "color": "#fcbad3",
                "bg_color": "#2d1f27",
                "description": "Quad & Glute"
            },
            {
                "name": "SINGLE LEG SQUAT",
                "code": "SINGLE_LEG_SQUAT",
                "emoji": "🦵",
                "color": "#a8dadc",
                "bg_color": "#1f2a2d",
                "description": "Balance & Power"
            },
            {
                "name": "HIP EXTENSION",
                "code": "HIP_EXTENSION",
                "emoji": "🍑",
                "color": "#ffe66d",
                "bg_color": "#2d2619",
                "description": "Glute Activation"
            },
            {
                "name": "SQUAT JUMP",
                "code": "SQUAT_JUMP",
                "emoji": "⚡",
                "color": "#ff006e",
                "bg_color": "#2d1f26",
                "description": "Explosive Power"
            },
            {
                "name": "BICEP CURL",
                "code": "BICEP_CURL",
                "emoji": "💪",
                "color": "#ff1493",
                "bg_color": "#2d1a22",
                "description": "Arm Strength"
            }
        ]
        
        # Create exercise buttons
        for exercise in exercises:
            self.create_exercise_card(
                exercises_frame,
                exercise["name"],
                exercise["code"],
                exercise["emoji"],
                exercise["color"],
                exercise["bg_color"],
                exercise["description"]
            )
    
    def create_exercise_card(
        self,
        parent: tk.Frame,
        name: str,
        code: str,
        emoji: str,
        color: str,
        bg_color: str,
        description: str
    ):
        """Create an individual exercise selection card."""
        # Main card container
        card_container = tk.Frame(parent, bg="#0f1419")
        card_container.pack(side=tk.LEFT, padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Card
        card = tk.Frame(
            card_container,
            bg=bg_color,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2"
        )
        card.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Top accent bar
        accent_bar = tk.Frame(card, bg=color, height=6)
        accent_bar.pack(fill=tk.X)
        
        # Emoji/Icon
        emoji_label = tk.Label(
            card,
            text=emoji,
            font=("Arial", 72),
            bg=bg_color,
            fg=color
        )
        emoji_label.pack(pady=(30, 10), padx=20)
        
        # Exercise Name
        name_label = tk.Label(
            card,
            text=name,
            font=("Arial", 26, "bold"),
            bg=bg_color,
            fg="#ffffff"
        )
        name_label.pack(pady=10)
        
        # Description
        desc_label = tk.Label(
            card,
            text=description,
            font=("Arial", 13),
            bg=bg_color,
            fg="#a0a8b0"
        )
        desc_label.pack(pady=5)
        
        # Click Button
        btn = tk.Button(
            card,
            text="▶ START TRAINING ▶",
            font=("Arial", 13, "bold"),
            bg=color,
            fg="#000000",
            relief=tk.FLAT,
            padx=25,
            pady=12,
            cursor="hand2",
            command=lambda: self.select_exercise(code),
            activebackground="#ffffff",
            activeforeground="#000000",
            bd=0,
            highlightthickness=0
        )
        btn.pack(pady=20, padx=20)
        
        # Bind hover effects to all components
        hover_widgets = [card, emoji_label, name_label, desc_label, btn]
        for widget in hover_widgets:
            widget.bind("<Enter>", lambda e: self.on_hover_enter(card, btn, color, bg_color))
            widget.bind("<Leave>", lambda e: self.on_hover_leave(card, btn, color, bg_color))
    
    def on_hover_enter(self, card: tk.Frame, btn: tk.Button, color: str, bg_color: str):
        """Handle hover effect on exercise card."""
        card.config(bg=bg_color, relief=tk.RAISED, bd=1, highlightbackground=color, highlightthickness=2)
        btn.config(relief=tk.SUNKEN, bd=2)
    
    def on_hover_leave(self, card: tk.Frame, btn: tk.Button, color: str, bg_color: str):
        """Handle mouse leave effect on exercise card."""
        card.config(bg=bg_color, relief=tk.FLAT, bd=0, highlightthickness=0)
        btn.config(relief=tk.FLAT, bd=0)
    
    def select_exercise(self, exercise: str):
        """Handle exercise selection."""
        self.selected_exercise = exercise
        self.root.quit()
        self.root.destroy()


def show_exercise_menu() -> Optional[str]:
    """Display exercise selection menu and return selected exercise."""
    root = tk.Tk()
    gui = ExerciseSelectionGUI(root)
    root.mainloop()
    return gui.selected_exercise


if __name__ == "__main__":
    selected = show_exercise_menu()
    if selected:
        print(f"Selected exercise: {selected}")
    else:
        print("No exercise selected")
