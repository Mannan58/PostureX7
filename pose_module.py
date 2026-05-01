from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.request import urlretrieve

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


Point = Tuple[float, float]
PixelPoint = Tuple[int, int]

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
MODEL_PATH = Path(__file__).with_name("pose_landmarker_lite.task")


@dataclass(frozen=True)
class LandmarkPoint:
    x: float
    y: float
    z: float
    visibility: float
    pixel: PixelPoint

    @property
    def xy(self) -> Point:
        return (self.x, self.y)


class PoseDetector:
    """MediaPipe Tasks PoseLandmarker wrapper for normalized and pixel landmarks."""

    IMPORTANT_LANDMARKS = {
        "left_shoulder": 11,
        "right_shoulder": 12,
        "left_elbow": 13,
        "right_elbow": 14,
        "left_wrist": 15,
        "right_wrist": 16,
        "left_hip": 23,
        "right_hip": 24,
        "left_knee": 25,
        "right_knee": 26,
        "left_ankle": 27,
        "right_ankle": 28,
        "left_wrist": 15,
        "right_wrist": 16,
        "left_foot_index": 31,
        "right_foot_index": 32,
    }

    # Standard MediaPipe Pose topology. Keeping it local avoids depending on
    # the removed mp.solutions namespace in newer Python 3.14 builds.
    POSE_CONNECTIONS = (
        (0, 1), (1, 2), (2, 3), (3, 7),
        (0, 4), (4, 5), (5, 6), (6, 8),
        (9, 10),
        (11, 12),
        (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
        (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
        (11, 23), (12, 24), (23, 24),
        (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),
        (24, 26), (26, 28), (28, 30), (30, 32), (28, 32),
    )

    def __init__(
        self,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.6,
    ) -> None:
        self._ensure_model()
        base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_pose_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_segmentation_masks=False,
        )
        self.pose = vision.PoseLandmarker.create_from_options(options)
        self.connections = self.POSE_CONNECTIONS
        self._timestamp_ms = 0

    def _ensure_model(self) -> None:
        if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 0:
            return

        print("Downloading MediaPipe pose model. This happens once...")
        try:
            urlretrieve(MODEL_URL, MODEL_PATH)
        except Exception as exc:
            raise RuntimeError(
                "Could not download pose_landmarker_lite.task. "
                f"Download it manually from {MODEL_URL} and place it beside main.py."
            ) from exc

    def detect(self, frame) -> Tuple[Optional[Dict[int, LandmarkPoint]], object]:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._timestamp_ms += 33
        results = self.pose.detect_for_video(mp_image, self._timestamp_ms)

        if not results.pose_landmarks:
            return None, results

        height, width = frame.shape[:2]
        landmarks: Dict[int, LandmarkPoint] = {}
        for idx, landmark in enumerate(results.pose_landmarks[0]):
            visibility = getattr(landmark, "visibility", 1.0)
            landmarks[idx] = LandmarkPoint(
                x=landmark.x,
                y=landmark.y,
                z=landmark.z,
                visibility=visibility,
                pixel=(int(landmark.x * width), int(landmark.y * height)),
            )

        return landmarks, results

    def close(self) -> None:
        self.pose.close()

    def choose_visible_side(self, landmarks: Dict[int, LandmarkPoint]) -> str:
        left_ids = (11, 23, 25, 27, 15)
        right_ids = (12, 24, 26, 28, 16)
        left_score = sum(landmarks[idx].visibility for idx in left_ids)
        right_score = sum(landmarks[idx].visibility for idx in right_ids)
        return "left" if left_score >= right_score else "right"