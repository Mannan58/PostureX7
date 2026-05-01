import argparse
import math
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import cv2
import numpy as np
import pyttsx3

from pose_module import LandmarkPoint, PoseDetector
from utils import MovingAverage, calculate_angle, first_message


DEFAULT_CAMERA = "0"

GREEN = (40, 220, 90)
RED = (40, 40, 235)
WHITE = (240, 240, 240)
BLACK = (0, 0, 0)
DARK = (18, 22, 24)
DARK_BG = (10, 15, 20)
YELLOW = (0, 210, 255)
CYAN = (255, 210, 80)
MUTED = (150, 160, 160)
ORANGE = (0, 140, 255)
LIGHT_GREEN = (100, 255, 100)
BRIGHT_CYAN = (255, 200, 0)
PURPLE = (180, 0, 200)
PINK = (200, 50, 150)
LIME = (0, 255, 150)
GOLD = (0, 215, 255)
BRIGHT_RED = (0, 100, 255)
TEAL = (200, 170, 0)
VIOLET = (230, 100, 200)

MIN_TRACKING_QUALITY = 0.58
STABLE_FRAMES_FOR_STAGE = 3
STABLE_FRAMES_FOR_WARNING = 2
WARNING_HOLD_SECONDS = 0.8


@dataclass
class ExerciseState:
    name: str = "SQUAT"
    reps: int = 0
    stage: str = "UP"
    warnings: List[str] = field(default_factory=list)
    error_joints: Set[int] = field(default_factory=set)
    error_segments: Set[frozenset] = field(default_factory=set)
    angles: Dict[str, float] = field(default_factory=dict)
    side: str = "left"
    tracking_quality: float = 0.0
    accuracy: float = 100.0
    rep_progress: float = 0.0
    joint_status: Dict[int, str] = field(default_factory=dict)



class VoiceCoach:
    """Non-blocking offline voice feedback for right and wrong form detection."""

    def __init__(self, cooldown_seconds: float = 0.5, rate: int = 175) -> None:
        self.cooldown_seconds = cooldown_seconds
        self.last_spoken_at: Dict[str, float] = {}
        self.messages: "queue.Queue[str]" = queue.Queue(maxsize=3)
        self.thread = threading.Thread(target=self._run, args=(rate,), daemon=True)
        self.thread.start()

    def speak(self, message: str) -> None:
        if not message:
            return

        now = time.monotonic()
        if now - self.last_spoken_at.get(message, 0.0) < self.cooldown_seconds:
            return

        self.last_spoken_at[message] = now
        try:
            self.messages.put_nowait(message)
        except queue.Full:
            pass

    def _run(self, rate: int) -> None:
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", rate)
        except Exception as exc:
            print(f"Voice feedback disabled: {exc}")
            return

        while True:
            message = self.messages.get()
            if message is None:
                break
            try:
                engine.say(message)
                engine.runAndWait()
            except Exception as exc:
                print(f"Voice feedback error: {exc}")


class ExerciseAnalyzer:
    def __init__(self, smoothing_window: int = 12) -> None:
        self.exercise = "SQUAT"
        self.state = ExerciseState(name=self.exercise)
        self.stage_candidate = self.state.stage
        self.stage_candidate_frames = 0
        self.side_candidate = self.state.side
        self.side_candidate_frames = 0
        self.warning_counts: Dict[str, int] = {}
        self.held_warnings: List[str] = []
        self.hold_warnings_until = 0.0
        self.rep_progress = 0.0
        self.smoothers = {
            "knee": MovingAverage(smoothing_window),
            "hip": MovingAverage(smoothing_window),
            "back": MovingAverage(smoothing_window),
            "torso": MovingAverage(smoothing_window),
            "ankle": MovingAverage(smoothing_window),
            "elbow": MovingAverage(smoothing_window),
            "shoulder": MovingAverage(smoothing_window),
            "knee_ankle_offset": MovingAverage(smoothing_window),
            "shoulder_hip_offset": MovingAverage(smoothing_window),
            "hand_bar_offset": MovingAverage(smoothing_window),
        }
        self.tracking_quality_smoother = MovingAverage(smoothing_window)

    def switch(self, exercise: str) -> None:
        self.exercise = exercise.upper()
        self.state = ExerciseState(name=self.exercise)
        self.stage_candidate = self.state.stage
        self.stage_candidate_frames = 0
        self.side_candidate = self.state.side
        self.side_candidate_frames = 0
        self.warning_counts.clear()
        self.held_warnings.clear()
        self.hold_warnings_until = 0.0
        self.rep_progress = 0.0
        for smoother in self.smoothers.values():
            smoother.values.clear()
        self.tracking_quality_smoother.values.clear()

    def update(self, landmarks: Dict[int, LandmarkPoint], side: str) -> ExerciseState:
        side = self._stable_side(side)
        ids = self._side_ids(side)
        tracking_quality = self._tracking_quality(landmarks, ids)
        tracking_quality = self.tracking_quality_smoother.update(tracking_quality) or tracking_quality
        self.state.tracking_quality = tracking_quality
        self.state.side = side

        if tracking_quality < MIN_TRACKING_QUALITY:
            self.state.warnings = ["Improve camera view"]
            self.state.error_joints = set(ids.values())
            self.state.error_segments = set()
            self.state.rep_progress = 0.0
            return self.state

        raw_angles = self._angles(landmarks, ids)
        angles = {
            name: self.smoothers[name].update(value) or value
            for name, value in raw_angles.items()
        }

        warnings: List[str] = []
        error_joints: Set[int] = set()
        error_segments: Set[frozenset] = set()
        joint_status: Dict[int, str] = {}

        if self.exercise == "SQUAT":
            self._update_squat(angles)
            self._squat_errors(angles, ids, warnings, error_joints, error_segments, joint_status)
        elif self.exercise == "DEADLIFT":
            self._update_deadlift(angles)
            self._deadlift_errors(angles, ids, warnings, error_joints, error_segments, joint_status)
        elif self.exercise == "PUSHUP":
            self._update_pushup(angles)
            self._pushup_errors(angles, ids, warnings, error_joints, error_segments, joint_status)
        elif self.exercise == "FRONT_SQUAT":
            self._update_front_squat(angles)
            self._front_squat_errors(angles, ids, warnings, error_joints, error_segments, joint_status)
        elif self.exercise == "HYBRID_DEADLIFT":
            self._update_hybrid_deadlift(angles)
            self._hybrid_deadlift_errors(angles, ids, warnings, error_joints, error_segments, joint_status)
        elif self.exercise == "REVERSE_LUNGE":
            self._update_reverse_lunge(angles)
            self._reverse_lunge_errors(angles, ids, warnings, error_joints, error_segments, joint_status)
        elif self.exercise == "LEANING_LUNGE":
            self._update_leaning_lunge(angles)
            self._leaning_lunge_errors(angles, ids, warnings, error_joints, error_segments, joint_status)
        elif self.exercise == "BULGARIAN":
            self._update_bulgarian(angles)
            self._bulgarian_errors(angles, ids, warnings, error_joints, error_segments, joint_status)
        elif self.exercise == "SINGLE_LEG_SQUAT":
            self._update_single_leg_squat(angles)
            self._single_leg_squat_errors(angles, ids, warnings, error_joints, error_segments, joint_status)
        elif self.exercise == "HIP_EXTENSION":
            self._update_hip_extension(angles)
            self._hip_extension_errors(angles, ids, warnings, error_joints, error_segments, joint_status)
        elif self.exercise == "STEPUP":
            self._update_stepup(angles)
            self._stepup_errors(angles, ids, warnings, error_joints, error_segments, joint_status)
        elif self.exercise == "SQUAT_JUMP":
            self._update_squat_jump(angles)
            self._squat_jump_errors(angles, ids, warnings, error_joints, error_segments, joint_status)
        elif self.exercise == "RDL":
            self._update_rdl(angles)
            self._rdl_errors(angles, ids, warnings, error_joints, error_segments, joint_status)
        elif self.exercise == "BICEP_CURL":
            self._update_bicep_curl(angles)
            self._bicep_curl_errors(angles, ids, warnings, error_joints, error_segments, joint_status)

        self.state.name = self.exercise
        self.state.side = side
        self.state.angles = angles
        self.state.accuracy = self._accuracy(angles) if self.exercise == "DEADLIFT" else 100.0
        self.state.warnings = self._stable_warnings(warnings)
        self.state.error_joints = error_joints
        self.state.error_segments = error_segments
        self.state.joint_status = joint_status
        return self.state

    # ===================== HELPER FUNCTIONS =====================

    def _side_ids(self, side: str) -> Dict[str, int]:
        prefix = "left" if side == "left" else "right"
        return {
            "shoulder": PoseDetector.IMPORTANT_LANDMARKS[f"{prefix}_shoulder"],
            "elbow": PoseDetector.IMPORTANT_LANDMARKS[f"{prefix}_elbow"],
            "wrist": PoseDetector.IMPORTANT_LANDMARKS[f"{prefix}_wrist"],
            "hip": PoseDetector.IMPORTANT_LANDMARKS[f"{prefix}_hip"],
            "knee": PoseDetector.IMPORTANT_LANDMARKS[f"{prefix}_knee"],
            "ankle": PoseDetector.IMPORTANT_LANDMARKS[f"{prefix}_ankle"],
            "foot": PoseDetector.IMPORTANT_LANDMARKS[f"{prefix}_foot_index"],
        }

    def _stable_side(self, side: str) -> str:
        if side == self.state.side:
            self.side_candidate = side
            self.side_candidate_frames = 0
            return side

        if self.side_candidate != side:
            self.side_candidate = side
            self.side_candidate_frames = 1
            return self.state.side

        self.side_candidate_frames += 1
        if self.side_candidate_frames >= STABLE_FRAMES_FOR_STAGE:
            self.state.side = side
            self.side_candidate_frames = 0

        return self.state.side

    def _tracking_quality(self, landmarks: Dict[int, LandmarkPoint], ids: Dict[str, int]) -> float:
        required = ("shoulder", "elbow", "hip", "knee", "ankle")
        scores = [landmarks[ids[name]].visibility for name in required if ids[name] in landmarks]
        if len(scores) != len(required):
            return 0.0
        return float(min(scores))

    def _angles(self, landmarks: Dict[int, LandmarkPoint], ids: Dict[str, int]) -> Dict[str, float]:
        shoulder = landmarks[ids["shoulder"]].xy
        elbow = landmarks[ids["elbow"]].xy
        wrist = landmarks[ids["wrist"]].xy
        hip = landmarks[ids["hip"]].xy
        knee = landmarks[ids["knee"]].xy
        ankle = landmarks[ids["ankle"]].xy
        foot = landmarks[ids["foot"]].xy

        vertical_below_hip = (hip[0], hip[1] + 0.35)

        return {
            "knee": calculate_angle(hip, knee, ankle),
            "hip": calculate_angle(shoulder, hip, knee),
            "back": calculate_angle(shoulder, hip, knee),
            "torso": calculate_angle(shoulder, hip, vertical_below_hip),
            "ankle": calculate_angle(knee, ankle, foot),
            "elbow": calculate_angle(shoulder, elbow, wrist),
            "shoulder": calculate_angle(elbow, shoulder, hip),
            "knee_ankle_offset": abs(knee[0] - ankle[0]),
            "shoulder_hip_offset": abs(shoulder[0] - hip[0]),
            "hand_bar_offset": abs(wrist[0] - ankle[0]),
        }

    def _check_posture(self, torso: float, min_angle: float = 155) -> Tuple[bool, str]:
        """Check if torso posture is acceptable."""
        if torso < min_angle:
            return False, "Keep chest up"
        return True, ""

    def _check_alignment(self, offset: float, threshold: float, msg: str) -> Tuple[bool, str]:
        """Check if alignment offset is within threshold."""
        if offset > threshold:
            return False, msg
        return True, ""

    def _check_angle_range(self, angle: float, low: float, high: float, msg_low: str = "", msg_high: str = "") -> Tuple[bool, str]:
        """Check if angle is within acceptable range."""
        if angle < low and msg_low:
            return False, msg_low
        if angle > high and msg_high:
            return False, msg_high
        return True, ""

    def _mark_joint(self, joint_id: int, status: str, ids: Dict[str, int], 
                   joint_status: Dict[int, str], error_joints: Set[int]) -> None:
        """Mark a joint with status and add to error set if needed."""
        joint_status[joint_id] = status
        if status == "error":
            error_joints.add(joint_id)

    def _mark_segment(self, joint1_id: int, joint2_id: int, error_segments: Set[frozenset]) -> None:
        """Mark a body segment as having error."""
        error_segments.add(frozenset((joint1_id, joint2_id)))

    def _confirm_stage(self, stage: str, count_rep: bool = False) -> None:
        if self.stage_candidate != stage:
            self.stage_candidate = stage
            self.stage_candidate_frames = 1
            return

        self.stage_candidate_frames += 1
        if self.stage_candidate_frames < STABLE_FRAMES_FOR_STAGE:
            return
        if self.state.stage == stage:
            return

        self.state.stage = stage
        if count_rep:
            self.state.reps += 1

    def _stable_warnings(self, warnings: List[str]) -> List[str]:
        now = time.monotonic()
        current = set(warnings)
        for message in list(self.warning_counts):
            if message not in current:
                self.warning_counts[message] = 0

        active: List[str] = []
        for message in warnings:
            self.warning_counts[message] = self.warning_counts.get(message, 0) + 1
            if self.warning_counts[message] >= STABLE_FRAMES_FOR_WARNING:
                active.append(message)

        if active:
            self.held_warnings = active
            self.hold_warnings_until = now + WARNING_HOLD_SECONDS
            return active[:2]

        if now < self.hold_warnings_until:
            return self.held_warnings

        return []

    # ===================== SQUAT =====================

    def _update_squat(self, angles):
        knee = angles["knee"]
        hip = angles["hip"]
        if knee < 100 and hip < 120:
            self._confirm_stage("DOWN")
        elif knee > 155 and hip > 140 and self.state.stage == "DOWN":
            self._confirm_stage("UP", count_rep=True)
        
        # Progress bar
        if self.state.stage == "DOWN":
            self.rep_progress = 1.0 - (knee / 155.0)
        else:
            self.rep_progress = (knee / 155.0)
        self.state.rep_progress = max(0.0, min(1.0, self.rep_progress))

    def _squat_errors(self, angles, ids, warnings, error_joints, error_segments, joint_status):
        knee = angles["knee"]
        hip = angles["hip"]
        torso = angles["torso"]
        ankle = angles["ankle"]
        knee_offset = angles["knee_ankle_offset"]

        # Posture check
        if torso < 155:
            warnings.append("Keep chest up — don't lean forward")
            self._mark_joint(ids["shoulder"], "error", ids, joint_status, error_joints)
            self._mark_segment(ids["shoulder"], ids["hip"], error_segments)

        # Depth check
        if self.state.stage == "DOWN" and knee > 105:
            warnings.append("Go deeper with control")
            self._mark_joint(ids["knee"], "error", ids, joint_status, error_joints)

        # Knee valgus (inward collapse)
        if knee_offset > 0.12:
            warnings.append("Drive knees outward")
            self._mark_joint(ids["knee"], "error", ids, joint_status, error_joints)

        # Hip dominance
        if hip < 75 and self.state.stage == "DOWN":
            warnings.append("Slow descent — control the weight")
            self._mark_joint(ids["hip"], "error", ids, joint_status, error_joints)

        # Ankle mobility
        if ankle < 60:
            warnings.append("Limited ankle mobility — use heel plates")
            self._mark_joint(ids["ankle"], "warning", ids, joint_status, error_joints)

        # Lockout
        if self.state.stage == "UP" and knee < 160:
            warnings.append("Stand fully up")
            self._mark_joint(ids["knee"], "error", ids, joint_status, error_joints)

    # ===================== DEADLIFT =====================

    def _update_deadlift(self, angles: Dict[str, float]) -> None:
        hip = angles["hip"]
        if hip < 110:
            self._confirm_stage("DOWN")
        elif hip > 165 and self.state.stage == "DOWN":
            self._confirm_stage("UP", count_rep=True)
        
        if self.state.stage == "DOWN":
            self.rep_progress = 1.0 - (hip / 165.0)
        else:
            self.rep_progress = (hip / 165.0)
        self.state.rep_progress = max(0.0, min(1.0, self.rep_progress))

    def _deadlift_errors(self, angles, ids, warnings, error_joints, error_segments, joint_status):
        hip = angles["hip"]
        knee = angles["knee"]
        torso = angles["torso"]
        hand_offset = angles["hand_bar_offset"]
        bottom_position = hip <= 130
        top_position = hip >= 155

        if bottom_position:
            # Bar path
            if hand_offset > 0.14:
                warnings.append("Hands closer to midfoot — straighter bar path")
                self._mark_joint(ids["wrist"], "error", ids, joint_status, error_joints)
                self._mark_segment(ids["wrist"], ids["ankle"], error_segments)

            # Hip height
            if hip > 120:
                warnings.append("Hinge deeper — more horizontal back")
                self._mark_joint(ids["hip"], "error", ids, joint_status, error_joints)

            # Knee bend
            if knee < 95:
                warnings.append("Straighten legs slightly")
                self._mark_joint(ids["knee"], "error", ids, joint_status, error_joints)

            # Spine
            if torso < 155:
                warnings.append("Neutral spine — tighten core")
                self._mark_segment(ids["shoulder"], ids["hip"], error_segments)

        if top_position:
            # Lockout
            if hip < 165:
                warnings.append("Drive hips forward — complete lockout")
                self._mark_joint(ids["hip"], "error", ids, joint_status, error_joints)

            if knee < 160:
                warnings.append("Full knee extension")
                self._mark_joint(ids["knee"], "error", ids, joint_status, error_joints)

    # ===================== PUSHUP =====================

    def _update_pushup(self, angles):
        elbow = angles["elbow"]
        if elbow < 85:
            self._confirm_stage("DOWN")
        elif elbow > 165 and self.state.stage == "DOWN":
            self._confirm_stage("UP", count_rep=True)
        
        if self.state.stage == "DOWN":
            self.rep_progress = 1.0 - (elbow / 165.0)
        else:
            self.rep_progress = (elbow / 165.0)
        self.state.rep_progress = max(0.0, min(1.0, self.rep_progress))

    def _pushup_errors(self, angles, ids, warnings, error_joints, error_segments, joint_status):
        elbow = angles["elbow"]
        torso = angles["torso"]
        hip = angles["hip"]
        shoulder = angles["shoulder"]

        # Body alignment
        if torso < 160 or hip < 150:
            warnings.append("Keep body straight — engage core")
            self._mark_segment(ids["shoulder"], ids["hip"], error_segments)
            self._mark_joint(ids["hip"], "error", ids, joint_status, error_joints)

        # Depth
        if self.state.stage == "DOWN" and elbow > 95:
            warnings.append("Lower chest to ground")
            self._mark_joint(ids["elbow"], "error", ids, joint_status, error_joints)

        # Extension
        if self.state.stage == "UP" and elbow < 160:
            warnings.append("Lock out elbows — full extension")
            self._mark_joint(ids["elbow"], "error", ids, joint_status, error_joints)

        # Elbow flare
        if shoulder > 75:
            warnings.append("Elbows closer to body — reduce flare")
            self._mark_joint(ids["elbow"], "error", ids, joint_status, error_joints)

    # ===================== FRONT SQUAT =====================

    def _update_front_squat(self, angles):
        knee = angles["knee"]
        if knee < 110:
            self._confirm_stage("DOWN")
        elif knee > 160 and self.state.stage == "DOWN":
            self._confirm_stage("UP", count_rep=True)
        
        if self.state.stage == "DOWN":
            self.rep_progress = 1.0 - (knee / 160.0)
        else:
            self.rep_progress = (knee / 160.0)
        self.state.rep_progress = max(0.0, min(1.0, self.rep_progress))

    def _front_squat_errors(self, angles, ids, warnings, error_joints, error_segments, joint_status):
        knee = angles["knee"]
        torso = angles["torso"]
        hip = angles["hip"]

        # Upright torso is critical
        if torso < 165:
            warnings.append("Torso upright — keep bar over midfoot")
            self._mark_segment(ids["shoulder"], ids["hip"], error_segments)

        # Depth
        if self.state.stage == "DOWN" and knee > 115:
            warnings.append("Go deeper — below parallel")
            self._mark_joint(ids["knee"], "error", ids, joint_status, error_joints)

        # Hip collapse
        if hip < 85:
            warnings.append("Control descent — don't collapse")
            self._mark_joint(ids["hip"], "error", ids, joint_status, error_joints)

        # Lockout
        if self.state.stage == "UP" and knee < 160:
            warnings.append("Stand fully up")
            self._mark_joint(ids["knee"], "error", ids, joint_status, error_joints)

    # ===================== HYBRID DEADLIFT =====================

    def _update_hybrid_deadlift(self, angles):
        hip = angles["hip"]
        if hip < 125:
            self._confirm_stage("DOWN")
        elif hip > 165 and self.state.stage == "DOWN":
            self._confirm_stage("UP", count_rep=True)
        
        if self.state.stage == "DOWN":
            self.rep_progress = 1.0 - (hip / 165.0)
        else:
            self.rep_progress = (hip / 165.0)
        self.state.rep_progress = max(0.0, min(1.0, self.rep_progress))

    def _hybrid_deadlift_errors(self, angles, ids, warnings, error_joints, error_segments, joint_status):
        if angles["knee"] < 120:
            warnings.append("Less knee bend — more hip dominant")
            self._mark_joint(ids["knee"], "error", ids, joint_status, error_joints)

        if angles["torso"] < 155:
            warnings.append("Keep back straight")
            self._mark_segment(ids["shoulder"], ids["hip"], error_segments)

    # ===================== REVERSE LUNGE =====================

    def _update_reverse_lunge(self, angles):
        knee = angles["knee"]
        if knee < 105:
            self._confirm_stage("DOWN")
        elif knee > 165 and self.state.stage == "DOWN":
            self._confirm_stage("UP", count_rep=True)
        
        if self.state.stage == "DOWN":
            self.rep_progress = 1.0 - (knee / 165.0)
        else:
            self.rep_progress = (knee / 165.0)
        self.state.rep_progress = max(0.0, min(1.0, self.rep_progress))

    def _reverse_lunge_errors(self, angles, ids, warnings, error_joints, error_segments, joint_status):
        if angles["torso"] < 165:
            warnings.append("Torso upright — stay vertical")
            self._mark_segment(ids["shoulder"], ids["hip"], error_segments)

        if self.state.stage == "DOWN" and angles["knee"] > 115:
            warnings.append("Lower more — back knee toward ground")
            self._mark_joint(ids["knee"], "error", ids, joint_status, error_joints)

    # ===================== LEANING LUNGE =====================

    def _update_leaning_lunge(self, angles):
        knee = angles["knee"]
        if knee < 105:
            self._confirm_stage("DOWN")
        elif knee > 165 and self.state.stage == "DOWN":
            self._confirm_stage("UP", count_rep=True)
        
        if self.state.stage == "DOWN":
            self.rep_progress = 1.0 - (knee / 165.0)
        else:
            self.rep_progress = (knee / 165.0)
        self.state.rep_progress = max(0.0, min(1.0, self.rep_progress))

    def _leaning_lunge_errors(self, angles, ids, warnings, error_joints, error_segments, joint_status):
        if angles["torso"] > 175:
            warnings.append("Lean forward into stretch")

        if angles["torso"] < 130:
            warnings.append("Don't over lean — balance control")
            self._mark_segment(ids["shoulder"], ids["hip"], error_segments)

    # ===================== BULGARIAN SPLIT SQUAT =====================

    def _update_bulgarian(self, angles):
        knee = angles["knee"]
        if knee < 105:
            self._confirm_stage("DOWN")
        elif knee > 165 and self.state.stage == "DOWN":
            self._confirm_stage("UP", count_rep=True)
        
        if self.state.stage == "DOWN":
            self.rep_progress = 1.0 - (knee / 165.0)
        else:
            self.rep_progress = (knee / 165.0)
        self.state.rep_progress = max(0.0, min(1.0, self.rep_progress))

    def _bulgarian_errors(self, angles, ids, warnings, error_joints, error_segments, joint_status):
        if self.state.stage == "DOWN" and angles["knee"] > 115:
            warnings.append("Go deeper")
            self._mark_joint(ids["knee"], "error", ids, joint_status, error_joints)

        if angles["torso"] < 155:
            warnings.append("Keep back straight — torso upright")
            self._mark_segment(ids["shoulder"], ids["hip"], error_segments)

    # ===================== SINGLE LEG SQUAT =====================

    def _update_single_leg_squat(self, angles):
        knee = angles["knee"]
        if knee < 105:
            self._confirm_stage("DOWN")
        elif knee > 165 and self.state.stage == "DOWN":
            self._confirm_stage("UP", count_rep=True)
        
        if self.state.stage == "DOWN":
            self.rep_progress = 1.0 - (knee / 165.0)
        else:
            self.rep_progress = (knee / 165.0)
        self.state.rep_progress = max(0.0, min(1.0, self.rep_progress))

    def _single_leg_squat_errors(self, angles, ids, warnings, error_joints, error_segments, joint_status):
        if angles["torso"] < 160:
            warnings.append("Stay upright — balance")

        if self.state.stage == "DOWN" and angles["knee"] > 115:
            warnings.append("Go deeper")
            self._mark_joint(ids["knee"], "error", ids, joint_status, error_joints)

    # ===================== HIP EXTENSION =====================

    def _update_hip_extension(self, angles):
        hip = angles["hip"]
        if hip < 125:
            self._confirm_stage("DOWN")
        elif hip > 170 and self.state.stage == "DOWN":
            self._confirm_stage("UP", count_rep=True)
        
        if self.state.stage == "DOWN":
            self.rep_progress = 1.0 - (hip / 170.0)
        else:
            self.rep_progress = (hip / 170.0)
        self.state.rep_progress = max(0.0, min(1.0, self.rep_progress))

    def _hip_extension_errors(self, angles, ids, warnings, error_joints, error_segments, joint_status):
        if angles["torso"] < 170:
            warnings.append("Keep body straight — no arching")

        if angles["hip"] < 110:
            warnings.append("Lower more controlled")
            self._mark_joint(ids["hip"], "error", ids, joint_status, error_joints)

    # ===================== STEP-UP =====================

    def _update_stepup(self, angles):
        knee = angles["knee"]
        if knee < 105:
            self._confirm_stage("DOWN")
        elif knee > 170 and self.state.stage == "DOWN":
            self._confirm_stage("UP", count_rep=True)
        
        if self.state.stage == "DOWN":
            self.rep_progress = 1.0 - (knee / 170.0)
        else:
            self.rep_progress = (knee / 170.0)
        self.state.rep_progress = max(0.0, min(1.0, self.rep_progress))

    def _stepup_errors(self, angles, ids, warnings, error_joints, error_segments, joint_status):
        if angles["knee"] < 160:
            warnings.append("Fully extend leg — drive through heel")
            self._mark_joint(ids["knee"], "error", ids, joint_status, error_joints)

        if angles["torso"] < 160:
            warnings.append("Keep torso stable")
            self._mark_segment(ids["shoulder"], ids["hip"], error_segments)

    # ===================== SQUAT JUMP =====================

    def _update_squat_jump(self, angles):
        knee = angles["knee"]
        if knee < 105:
            self._confirm_stage("DOWN")
        elif knee > 170 and self.state.stage == "DOWN":
            self._confirm_stage("UP", count_rep=True)
        
        if self.state.stage == "DOWN":
            self.rep_progress = 1.0 - (knee / 170.0)
        else:
            self.rep_progress = (knee / 170.0)
        self.state.rep_progress = max(0.0, min(1.0, self.rep_progress))

    def _squat_jump_errors(self, angles, ids, warnings, error_joints, error_segments, joint_status):
        if angles["torso"] < 155:
            warnings.append("Keep chest up — explosive")
            self._mark_segment(ids["shoulder"], ids["hip"], error_segments)

        if angles["knee"] > 115:
            warnings.append("Go deeper before jump")
            self._mark_joint(ids["knee"], "error", ids, joint_status, error_joints)

    # ===================== ROMANIAN DEADLIFT =====================

    def _update_rdl(self, angles):
        hip = angles["hip"]
        if hip < 115:
            self._confirm_stage("DOWN")
        elif hip > 170 and self.state.stage == "DOWN":
            self._confirm_stage("UP", count_rep=True)
        
        if self.state.stage == "DOWN":
            self.rep_progress = 1.0 - (hip / 170.0)
        else:
            self.rep_progress = (hip / 170.0)
        self.state.rep_progress = max(0.0, min(1.0, self.rep_progress))

    def _rdl_errors(self, angles, ids, warnings, error_joints, error_segments, joint_status):
        if angles["knee"] > 35:
            warnings.append("Keep knees slightly bent — not locked")
            self._mark_joint(ids["knee"], "error", ids, joint_status, error_joints)

        if angles["torso"] < 160:
            warnings.append("Keep back straight — neutral spine")
            self._mark_segment(ids["shoulder"], ids["hip"], error_segments)

    # ===================== BICEP CURL =====================

    def _update_bicep_curl(self, angles):
        elbow = angles["elbow"]
        if elbow > 150:
            self._confirm_stage("DOWN")
        elif elbow < 65 and self.state.stage == "DOWN":
            self._confirm_stage("UP", count_rep=True)
        
        if self.state.stage == "DOWN":
            self.rep_progress = (elbow / 150.0)
        else:
            self.rep_progress = 1.0 - (elbow / 150.0)
        self.state.rep_progress = max(0.0, min(1.0, self.rep_progress))

    def _bicep_curl_errors(self, angles, ids, warnings, error_joints, error_segments, joint_status):
        elbow = angles["elbow"]
        shoulder = angles["shoulder"]
        torso = angles["torso"]

        # Elbow position stability
        if shoulder > 50:
            warnings.append("Elbows locked at sides — no swinging")
            self._mark_joint(ids["elbow"], "error", ids, joint_status, error_joints)

        # Partial reps
        if self.state.stage == "UP" and elbow > 75:
            warnings.append("Full contraction — bring weights up")
            self._mark_joint(ids["elbow"], "error", ids, joint_status, error_joints)

        # Lockout at bottom
        if self.state.stage == "DOWN" and elbow < 145:
            warnings.append("Full extension — control the weight")
            self._mark_joint(ids["elbow"], "error", ids, joint_status, error_joints)

        # Body swinging
        if torso < 160:
            warnings.append("Control movement — no swinging")
            self._mark_segment(ids["shoulder"], ids["hip"], error_segments)

    def _accuracy(self, angles: Dict[str, float]) -> float:
        hip = angles["hip"]
        knee = angles["knee"]
        hand_offset = angles["hand_bar_offset"]

        score = 100.0
        score -= (1.0 - self.state.tracking_quality) * 30.0

        if hip < 130:
            score -= self._range_penalty(hip, 70, 115, scale=0.9)
            score -= self._range_penalty(knee, 100, 145, scale=0.8)
            score -= max(0.0, hand_offset - 0.08) * 130.0
        else:
            score -= self._range_penalty(hip, 160, 180, scale=1.0)
            score -= self._range_penalty(knee, 150, 180, scale=0.7)

        return max(0.0, min(100.0, score))

    def _range_penalty(self, value: float, low: float, high: float, scale: float = 1.0) -> float:
        if low <= value <= high:
            return 0.0
        if value < low:
            return (low - value) * scale
        return (value - high) * scale



class Renderer:
    def draw(self, frame, landmarks: Optional[Dict[int, LandmarkPoint]], detector: PoseDetector, state: ExerciseState, fps: float) -> None:
        # Draw background gradient effect
        self._draw_background_effect(frame)
        
        if landmarks:
            self._draw_skeleton(frame, landmarks, detector, state)
            self._draw_angles(frame, landmarks, state)
            if state.name == "DEADLIFT":
                self._draw_deadlift_alignment(frame, landmarks, state)

        self._draw_rep_progress(frame, state)
        self._draw_status_panel(frame, state, fps)
        self._draw_warning(frame, first_message(state.warnings))
        self._draw_footer(frame)
        self._draw_corner_accents(frame)

    def _draw_background_effect(self, frame) -> None:
        """Draw subtle background effects."""
        height, width = frame.shape[:2]
        # Subtle dark vignette effect
        overlay = frame.copy()
        for i in range(0, height, 50):
            cv2.line(overlay, (0, i), (width, i), DARK_BG, 1)
        cv2.addWeighted(overlay, 0.03, frame, 0.97, 0, frame)

    def _draw_corner_accents(self, frame) -> None:
        """Draw decorative corner accents."""
        height, width = frame.shape[:2]
        accent_size = 25
        thickness = 3
        
        # Top-left corner
        cv2.line(frame, (accent_size, 0), (accent_size, accent_size), CYAN, thickness, cv2.LINE_AA)
        cv2.line(frame, (0, accent_size), (accent_size, accent_size), CYAN, thickness, cv2.LINE_AA)
        
        # Top-right corner
        cv2.line(frame, (width - accent_size, 0), (width - accent_size, accent_size), BRIGHT_CYAN, thickness, cv2.LINE_AA)
        cv2.line(frame, (width - accent_size, accent_size), (width, accent_size), BRIGHT_CYAN, thickness, cv2.LINE_AA)
        
        # Bottom-left corner
        cv2.line(frame, (accent_size, height), (accent_size, height - accent_size), LIME, thickness, cv2.LINE_AA)
        cv2.line(frame, (0, height - accent_size), (accent_size, height - accent_size), LIME, thickness, cv2.LINE_AA)
        
        # Bottom-right corner
        cv2.line(frame, (width - accent_size, height), (width - accent_size, height - accent_size), TEAL, thickness, cv2.LINE_AA)
        cv2.line(frame, (width - accent_size, height - accent_size), (width, height - accent_size), TEAL, thickness, cv2.LINE_AA)

    def _draw_skeleton(self, frame, landmarks: Dict[int, LandmarkPoint], detector: PoseDetector, state: ExerciseState) -> None:
        # Draw connections with gradient effect
        for start, end in detector.connections:
            if start not in landmarks or end not in landmarks:
                continue
            if min(landmarks[start].visibility, landmarks[end].visibility) < 0.45:
                continue

            segment = frozenset((start, end))
            is_error = segment in state.error_segments
            
            if is_error:
                color = BRIGHT_RED
                thickness = 5
            else:
                color = LIME
                thickness = 3
            
            cv2.line(frame, landmarks[start].pixel, landmarks[end].pixel, color, thickness, cv2.LINE_AA)

        # Draw joints with enhanced visuals
        for idx, landmark in landmarks.items():
            if landmark.visibility < 0.45:
                continue

            is_error = idx in state.error_joints
            status = state.joint_status.get(idx, "ok")
            
            if is_error or status == "error":
                color = BRIGHT_RED
                radius = 10
                glow_color = RED
            elif status == "warning":
                color = ORANGE
                radius = 8
                glow_color = (0, 165, 255)
            else:
                color = LIME
                radius = 6
                glow_color = GREEN

            # Draw glow effect
            cv2.circle(frame, landmark.pixel, radius + 4, glow_color, 2, cv2.LINE_AA)
            # Draw main joint
            cv2.circle(frame, landmark.pixel, radius, color, -1, cv2.LINE_AA)
            # Draw outline
            cv2.circle(frame, landmark.pixel, radius + 1, WHITE, 1, cv2.LINE_AA)

    def _draw_angles(self, frame, landmarks, state):
        prefix = "left" if state.side == "left" else "right"

        ids = {
            "Knee": PoseDetector.IMPORTANT_LANDMARKS[f"{prefix}_knee"],
            "Hip": PoseDetector.IMPORTANT_LANDMARKS[f"{prefix}_hip"],
            "Elbow": PoseDetector.IMPORTANT_LANDMARKS[f"{prefix}_elbow"],
            "Ankle": PoseDetector.IMPORTANT_LANDMARKS[f"{prefix}_ankle"],
        }

        angle_keys = {
            "Knee": "knee",
            "Hip": "hip",
            "Elbow": "elbow",
            "Ankle": "ankle",
        }

        angle_colors = {
            "Knee": CYAN,
            "Hip": TEAL,
            "Elbow": GOLD,
            "Ankle": BRIGHT_CYAN,
        }

        for label, idx in ids.items():
            if idx not in landmarks or landmarks[idx].visibility < 0.45:
                continue

            value = state.angles.get(angle_keys[label])
            if value is None:
                continue

            x, y = landmarks[idx].pixel
            is_error = idx in state.error_joints
            color = angle_colors.get(label, YELLOW)
            
            if is_error:
                color = BRIGHT_RED
            
            # Draw background box for angle
            text = f"{label} {int(value)}°"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            box_coords = (x + 10, y - 22)
            box_end = (x + 12 + text_size[0], y - 2)
            
            cv2.rectangle(frame, box_coords, box_end, DARK_BG, -1)
            cv2.rectangle(frame, box_coords, box_end, color, 2, cv2.LINE_AA)
            
            self._text_with_shadow(frame, text, (x + 12, y - 10), 0.50, color, 1)
            
            # Draw angle arc
            self._draw_angle_arc(frame, landmarks[idx].pixel, int(value), is_error, color)

    def _draw_angle_arc(self, frame, center: Tuple[int, int], angle: int, is_error: bool, color: Tuple[int, int, int]) -> None:
        """Draw a visual arc representing the angle."""
        radius = 25
        arc_color = color if not is_error else BRIGHT_RED
        
        start_angle = max(0, min(180, angle - 25))
        end_angle = max(0, min(180, angle + 25))
        
        # Draw arc segments with varying thickness
        for i in range(int(start_angle), int(end_angle), 3):
            rad = math.radians(i)
            x = int(center[0] + radius * math.cos(rad))
            y = int(center[1] + radius * math.sin(rad))
            cv2.circle(frame, (x, y), 2, arc_color, -1)

    def _draw_rep_progress(self, frame, state: ExerciseState) -> None:
        """Draw enhanced progress bar for current rep."""
        height, width = frame.shape[:2]
        bar_width = 240
        bar_height = 18
        x = width - bar_width - 20
        y = 12

        progress = max(0.0, min(1.0, state.rep_progress))
        fill = int(bar_width * progress)

        # Background with border
        cv2.rectangle(frame, (x - 2, y - 2), (x + bar_width + 2, y + bar_height + 2), DARK_BG, -1)
        cv2.rectangle(frame, (x - 2, y - 2), (x + bar_width + 2, y + bar_height + 2), CYAN, 2, cv2.LINE_AA)
        
        # Background
        cv2.rectangle(frame, (x, y), (x + bar_width, y + bar_height), (30, 30, 40), -1)
        
        # Fill with gradient effect
        if state.stage == "DOWN":
            fill_color = BRIGHT_RED
            accent_color = RED
        else:
            fill_color = LIME
            accent_color = GREEN
        
        cv2.rectangle(frame, (x, y), (x + fill, y + bar_height), fill_color, -1)
        
        # Accent line
        cv2.line(frame, (x + fill, y), (x + fill, y + bar_height), accent_color, 2, cv2.LINE_AA)
        
        # Border
        cv2.rectangle(frame, (x, y), (x + bar_width, y + bar_height), CYAN, 2, cv2.LINE_AA)
        
        # Percentage label
        pct = int(progress * 100)
        pct_text = f"{pct}%"
        cv2.putText(frame, pct_text, (x + bar_width - 35, y + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, WHITE, 1, cv2.LINE_AA)
        
        # Label
        self._text_with_shadow(frame, "REP PROGRESS", (x + 5, y + 32), 0.38, CYAN, 1)

    def _draw_deadlift_alignment(self, frame, landmarks: Dict[int, LandmarkPoint], state: ExerciseState) -> None:
        prefix = "left" if state.side == "left" else "right"
        shoulder_id = PoseDetector.IMPORTANT_LANDMARKS[f"{prefix}_shoulder"]
        wrist_id = PoseDetector.IMPORTANT_LANDMARKS[f"{prefix}_wrist"]
        ankle_id = PoseDetector.IMPORTANT_LANDMARKS[f"{prefix}_ankle"]

        if not all(idx in landmarks for idx in (shoulder_id, wrist_id, ankle_id)):
            return

        shoulder = landmarks[shoulder_id]
        wrist = landmarks[wrist_id]
        ankle = landmarks[ankle_id]
        if min(shoulder.visibility, wrist.visibility, ankle.visibility) < 0.45:
            return

        hand_ok = state.angles.get("hand_bar_offset", 1.0) <= 0.12
        color = LIME if hand_ok else BRIGHT_RED
        x = ankle.pixel[0]
        y1 = min(shoulder.pixel[1], wrist.pixel[1], ankle.pixel[1])
        y2 = max(shoulder.pixel[1], wrist.pixel[1], ankle.pixel[1])
        
        # Draw bar path with glow
        cv2.line(frame, (x - 1, y1), (x - 1, y2), (50, 50, 150), 12, cv2.LINE_AA)
        cv2.line(frame, (x, y1), (x, y2), color, 8, cv2.LINE_AA)
        cv2.circle(frame, ankle.pixel, 10, color, -1, cv2.LINE_AA)
        cv2.circle(frame, ankle.pixel, 11, WHITE, 1, cv2.LINE_AA)

    def _draw_status_panel(self, frame, state: ExerciseState, fps: float) -> None:
        height, width = frame.shape[:2]
        panel_width = 360
        panel_height = 180
        x1, y1 = 12, 12
        x2, y2 = x1 + panel_width, y1 + panel_height

        # Draw outer glow
        cv2.rectangle(frame, (x1 - 2, y1 - 2), (x2 + 2, y2 + 2), CYAN, 2, cv2.LINE_AA)
        
        # Main panel
        self._panel_gradient(frame, (x1, y1), (x2, y2), DARK_BG, DARK, alpha=0.85)

        # Top accent line
        cv2.line(frame, (x1, y1 + 2), (x2, y1 + 2), CYAN, 2, cv2.LINE_AA)

        # Exercise name with icon
        self._text_with_shadow(frame, "💪 " + state.name, (x1 + 16, y1 + 38), 0.95, LIME, 2)

        # Reps badge
        rep_text = f"Rep {state.reps}"
        cv2.rectangle(frame, (x1 + 16, y1 + 50), (x1 + 110, y1 + 80), BRIGHT_RED, -1, cv2.LINE_AA)
        cv2.rectangle(frame, (x1 + 16, y1 + 50), (x1 + 110, y1 + 80), GOLD, 2, cv2.LINE_AA)
        self._text_with_shadow(frame, rep_text, (x1 + 25, y1 + 72), 0.75, WHITE, 2)

        # Stage badge
        stage_color = LIME if state.stage == "UP" else BRIGHT_CYAN
        badge_x = x1 + 140
        cv2.rectangle(frame, (badge_x, y1 + 50), (badge_x + 100, y1 + 80), stage_color, -1, cv2.LINE_AA)
        cv2.rectangle(frame, (badge_x, y1 + 50), (badge_x + 100, y1 + 80), WHITE, 2, cv2.LINE_AA)
        self._badge_text(frame, state.stage, (badge_x + 50, y1 + 72), 0.70, BLACK, 2)

        # Side indicator
        side_color = TEAL if state.side == "left" else PURPLE
        side_text = f"👈 {state.side.upper()}" if state.side == "left" else f"{state.side.upper()} 👉"
        self._text_with_shadow(frame, side_text, (x1 + 260, y1 + 72), 0.50, side_color, 1)

        # Tracking quality bar with gradient
        self._draw_tracking_bar_gradient(frame, state.tracking_quality, (x1 + 16, y1 + 100), panel_width - 40, 14)
        
        tracking_pct = int(state.tracking_quality * 100)
        fps_text = f"Track {tracking_pct:02d}% │ FPS {fps:05.1f}"
        self._text_with_shadow(frame, fps_text, (x1 + 16, y1 + 145), 0.48, CYAN, 1)

        if state.name == "DEADLIFT":
            color = LIME if state.accuracy >= 80 else GOLD if state.accuracy >= 60 else BRIGHT_RED
            acc_text = f"Accuracy {int(state.accuracy):02d}%"
            self._text_with_shadow(frame, acc_text, (x1 + 16, y1 + 165), 0.50, color, 1)

    def _draw_warning(self, frame, message: str) -> None:
        height, width = frame.shape[:2]
        box_width = 420
        box_height = 85
        x1 = width - box_width - 12
        x2 = width - 12
        y2 = height - 12
        y1 = y2 - box_height

        if message:
            # Error panel with glow
            cv2.rectangle(frame, (x1 - 2, y1 - 2), (x2 + 2, y2 + 2), BRIGHT_RED, 2, cv2.LINE_AA)
            self._panel_gradient(frame, (x1, y1), (x2, y2), DARK_BG, (50, 30, 30), alpha=0.90)
            cv2.line(frame, (x1 + 2, y1 + 2), (x2 - 2, y1 + 2), BRIGHT_RED, 3, cv2.LINE_AA)
            self._text_with_shadow(frame, "⚠ WARNING", (x1 + 16, y1 + 25), 0.65, BRIGHT_RED, 2)
            self._text_with_shadow(frame, message, (x1 + 16, y1 + 58), 0.55, WHITE, 1)
            return

        # Good form panel
        cv2.rectangle(frame, (x1 - 2, y1 - 2), (x2 + 2, y2 + 2), LIME, 2, cv2.LINE_AA)
        self._panel_gradient(frame, (x1, y1), (x2, y2), DARK_BG, (30, 50, 30), alpha=0.90)
        cv2.line(frame, (x1 + 2, y1 + 2), (x2 - 2, y1 + 2), LIME, 3, cv2.LINE_AA)
        self._text_with_shadow(frame, "✓ PERFECT FORM", (x1 + 16, y1 + 25), 0.65, LIME, 2)
        self._text_with_shadow(frame, "Keep it up!", (x1 + 16, y1 + 58), 0.55, WHITE, 1)

    def _draw_footer(self, frame) -> None:
        height, width = frame.shape[:2]
        footer_height = 55
        
        # Footer panel
        cv2.rectangle(frame, (12, height - footer_height), (width - 12, height - 12), DARK_BG, -1)
        cv2.rectangle(frame, (12, height - footer_height), (width - 12, height - 12), BRIGHT_CYAN, 2, cv2.LINE_AA)
        cv2.line(frame, (12, height - footer_height + 2), (width - 12, height - footer_height + 2), BRIGHT_CYAN, 2, cv2.LINE_AA)
        
        footer_text = "1:SQ 2:DL 3:PU 4:FSQ 5:HDL 6:RL 7:LL 8:BG 9:SLS 0:HE Q:SU W:SJ E:RDL R:CURL"
        hint_text = "Press key to switch exercise | ESC to quit"
        self._text_with_shadow(frame, footer_text, (24, height - 32), 0.42, CYAN, 1)
        self._text_with_shadow(frame, hint_text, (24, height - 12), 0.38, MUTED, 1)

    def _panel_gradient(self, frame, top_left: Tuple[int, int], bottom_right: Tuple[int, int], 
                       color1: Tuple[int, int, int], color2: Tuple[int, int, int], alpha: float) -> None:
        """Draw a gradient panel."""
        overlay = frame.copy()
        x1, y1 = top_left
        x2, y2 = bottom_right
        
        # Create gradient effect
        for i in range(y1, y2):
            t = (i - y1) / (y2 - y1)
            r = int(color1[0] + (color2[0] - color1[0]) * t)
            g = int(color1[1] + (color2[1] - color1[1]) * t)
            b = int(color1[2] + (color2[2] - color1[2]) * t)
            cv2.line(overlay, (x1, i), (x2, i), (b, g, r), 1)
        
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    def _draw_tracking_bar_gradient(self, frame, value: float, origin: Tuple[int, int], width: int, height: int) -> None:
        """Draw tracking quality bar with gradient."""
        x, y = origin
        value = max(0.0, min(1.0, value))
        fill = int(width * value)
        
        # Determine color based on value
        if value >= MIN_TRACKING_QUALITY:
            color = LIME
        elif value >= 0.4:
            color = GOLD
        else:
            color = BRIGHT_RED
        
        # Background
        cv2.rectangle(frame, (x - 2, y - 2), (x + width + 2, y + height + 2), DARK_BG, -1)
        cv2.rectangle(frame, (x - 2, y - 2), (x + width + 2, y + height + 2), CYAN, 2, cv2.LINE_AA)
        cv2.rectangle(frame, (x, y), (x + width, y + height), (40, 40, 50), -1)
        
        # Gradient fill
        for i in range(fill):
            t = i / max(1, fill)
            r = int(color[0] * t)
            g = int(color[1] * t)
            b = int(color[2] * t)
            cv2.line(frame, (x + i, y), (x + i, y + height), (b, g, r), 1)
        
        # Border
        cv2.rectangle(frame, (x, y), (x + width, y + height), CYAN, 1, cv2.LINE_AA)

    def _panel(self, frame, top_left: Tuple[int, int], bottom_right: Tuple[int, int], color: Tuple[int, int, int], alpha: float) -> None:
        overlay = frame.copy()
        cv2.rectangle(overlay, top_left, bottom_right, color, -1)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        cv2.rectangle(frame, top_left, bottom_right, WHITE, 1, cv2.LINE_AA)

    def _badge(self, frame, text: str, center: Tuple[int, int], color: Tuple[int, int, int]) -> None:
        x, y = center
        cv2.rectangle(frame, (x - 20, y - 18), (x + 110, y + 16), color, -1, cv2.LINE_AA)
        cv2.rectangle(frame, (x - 20, y - 18), (x + 110, y + 16), BLACK, 1, cv2.LINE_AA)
        self._text_with_shadow(frame, text, (x - 2, y + 6), 0.55, WHITE, 1)

    def _badge_text(self, frame, text: str, center: Tuple[int, int], scale: float, color: Tuple[int, int, int], thickness: int) -> None:
        x, y = center
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)[0]
        cv2.putText(frame, text, (x - text_size[0] // 2, y + text_size[1] // 2), 
                   cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)

    def _tracking_bar(self, frame, value: float, origin: Tuple[int, int], width: int, height: int) -> None:
        x, y = origin
        value = max(0.0, min(1.0, value))
        fill = int(width * value)
        color = GREEN if value >= MIN_TRACKING_QUALITY else RED
        
        cv2.rectangle(frame, (x, y), (x + width, y + height), (65, 70, 72), -1)
        cv2.rectangle(frame, (x, y), (x + fill, y + height), color, -1)
        cv2.rectangle(frame, (x, y), (x + width, y + height), WHITE, 1)

    def _text_with_shadow(self, frame, text: str, origin: Tuple[int, int], scale: float, color: Tuple[int, int, int], thickness: int) -> None:
        cv2.putText(frame, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, BLACK, thickness + 2, cv2.LINE_AA)
        cv2.putText(frame, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)



def open_camera(source, label: str = "camera", retries: int = 1, retry_delay: float = 0.6):
    if isinstance(source, cv2.VideoCapture):
        cap = source
        if cap.isOpened():
            return cap
        print(f"Could not connect to {label}: {source}")
        return None

    for attempt in range(1, retries + 1):
        cap = cv2.VideoCapture(source)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if cap.isOpened():
            return cap

        cap.release()
        if attempt < retries:
            time.sleep(retry_delay)

    print(f"Could not connect to {label}: {source}")
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Real-time AI gym trainer using DroidCam, OpenCV, and MediaPipe.")
    parser.add_argument("--camera", default=DEFAULT_CAMERA, help="DroidCam video URL or local camera index. Default: %(default)s")
    parser.add_argument("--fallback-camera", default="0", help="Local webcam index to use if DroidCam is unreachable. Use 'none' to disable.")
    parser.add_argument("--exercise", choices=("squat", "deadlift", "pushup"), default="squat", help="Starting exercise.")
    return parser.parse_args()


def normalize_camera_source(source):
    if isinstance(source, cv2.VideoCapture):
        return source
    if isinstance(source, int):
        return source
    if str(source).isdigit():
        return int(source)
    return source


def main_with_exercise(exercise: str, camera_source: str = DEFAULT_CAMERA, fallback_source: str = "0") -> None:
    """Run the AI gym trainer with the specified exercise."""
    camera_source = normalize_camera_source(camera_source)
    cap = open_camera(camera_source, label="primary camera", retries=2)

    if cap is None and str(fallback_source).lower() != "none":
        fallback_source = normalize_camera_source(fallback_source)
        print(f"Trying fallback camera: {fallback_source}")
        cap = open_camera(fallback_source, label="fallback camera", retries=1)

    if cap is None:
        print("No camera opened.")
        print("For DroidCam, start the phone app and use the exact Wi-Fi IP shown there, for example:")
        print("python main.py --camera http://YOUR_PHONE_IP:4747/video")
        print("For a laptop webcam, try: python main.py --camera 0")
        return

    detector = PoseDetector()
    analyzer = ExerciseAnalyzer(smoothing_window=12)
    analyzer.switch(exercise)
    renderer = Renderer()
    voice = VoiceCoach(cooldown_seconds=2.0)

    cv2.namedWindow("AI Gym Trainer", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("AI Gym Trainer", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    previous_time = time.monotonic()
    fps = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                print("Camera frame not received. Reconnecting or check DroidCam connection.")
                break

            frame = cv2.flip(frame, 1)
            landmarks, _ = detector.detect(frame)

            if landmarks:
                side = detector.choose_visible_side(landmarks)
                state = analyzer.update(landmarks, side)
                voice_text = first_message(state.warnings) or "Good form"
                voice.speak(voice_text)
            else:
                state = analyzer.state
                state.warnings = ["Step into frame"]
                state.error_joints = set()
                state.error_segments = set()
                voice.speak("Step into frame")

            now = time.monotonic()
            elapsed = max(now - previous_time, 1e-6)
            previous_time = now
            instant_fps = 1.0 / elapsed
            fps = instant_fps if fps == 0 else (fps * 0.88 + instant_fps * 0.12)

            renderer.draw(frame, landmarks, detector, state, fps)
            cv2.imshow("AI Gym Trainer", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("1"):
                analyzer.switch("SQUAT")
            elif key == ord("2"):
                analyzer.switch("DEADLIFT")
            elif key == ord("3"):
                analyzer.switch("PUSHUP")
            elif key == ord("4"):
                analyzer.switch("FRONT_SQUAT")
            elif key == ord("5"):
                analyzer.switch("HYBRID_DEADLIFT")
            elif key == ord("6"):
                analyzer.switch("REVERSE_LUNGE")
            elif key == ord("7"):
                analyzer.switch("LEANING_LUNGE")
            elif key == ord("8"):
                analyzer.switch("BULGARIAN")
            elif key == ord("9"):
                analyzer.switch("SINGLE_LEG_SQUAT")
            elif key == ord("0"):
                analyzer.switch("HIP_EXTENSION")
            elif key == ord("q"):
                analyzer.switch("STEPUP")
            elif key == ord("w"):
                analyzer.switch("SQUAT_JUMP")
            elif key == ord("e"):
                analyzer.switch("RDL")
            elif key == ord("r"):
                analyzer.switch("BICEP_CURL")
    finally:
        detector.close()
        cap.release()
        cv2.destroyAllWindows()


def main() -> None:
    """Main entry point - shows GUI or uses command-line arguments."""
    import sys
    
    # Check if running with command-line arguments
    if len(sys.argv) > 1:
        # Use command-line arguments
        args = parse_args()
        main_with_exercise(args.exercise, args.camera, args.fallback_camera)
    else:
        # Show GUI for exercise selection
        try:
            from gui import show_exercise_menu
            selected_exercise = show_exercise_menu()
            if selected_exercise:
                main_with_exercise(selected_exercise.lower(), camera_source=0, fallback_source="none")
            else:
                print("No exercise selected. Exiting.")
        except ImportError:
            print("GUI module not found. Using command-line interface.")
            args = parse_args()
            main_with_exercise(args.exercise, args.camera, args.fallback_camera)


if __name__ == "__main__":
    main()