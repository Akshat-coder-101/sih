"""
Video stream generator for CAM-02, CAM-03, CAM-04 providing real MJPEG streams.
Simulates tactical border CCTV video with real frame drawing, moving entities,
night IR modes, and tactical overlays using OpenCV.
"""
import time
import math
import random
import cv2
import numpy as np

# Cache for frame generators
class CameraStreamGenerator:
    def __init__(self, cam_id: str, scene: str = "fence", is_night: bool = False):
        self.cam_id = cam_id
        self.scene = scene
        self.is_night = is_night
        self.width = 640
        self.height = 360
        self.frame_idx = 0
        
        # State variables for animated scene
        self.person_x = 100
        self.person_dir = 1
        self.vehicle_x = -150
        self.vehicle_active = False

    def generate_frame(self) -> bytes:
        self.frame_idx += 1
        t = self.frame_idx * 0.05

        # Base background
        if self.is_night:
            # Low light / IR green palette
            img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            img[:, :] = (15, 30, 20)  # Dark olive greenish
            # Horizon / ground
            cv2.rectangle(img, (0, int(self.height * 0.45)), (self.width, self.height), (25, 45, 30), -1)
            # Add synthetic IR noise
            noise = np.random.normal(0, 8, (self.height, self.width, 3)).astype(np.int16)
            img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        else:
            # Daylight tactical scene (arid / fence post landscape)
            img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            img[:int(self.height * 0.45), :] = (70, 50, 30)  # Dull sky
            img[int(self.height * 0.45):, :] = (40, 60, 50)  # Border ground/sand

        # Draw scene-specific landscape
        if self.scene == "gate":
            # Road
            pts = np.array([[int(self.width * 0.3), self.height], [int(self.width * 0.7), self.height],
                            [int(self.width * 0.55), int(self.height * 0.45)], [int(self.width * 0.45), int(self.height * 0.45)]], np.int32)
            cv2.fillPoly(img, [pts], (30, 35, 40) if not self.is_night else (20, 35, 25))
            # Barrier gate pole
            gate_color = (0, 180, 240) if not self.is_night else (80, 200, 120)
            cv2.line(img, (int(self.width * 0.35), int(self.height * 0.65)), (int(self.width * 0.65), int(self.height * 0.65)), gate_color, 4)
            # Check post booth
            cv2.rectangle(img, (int(self.width * 0.2), int(self.height * 0.4)), (int(self.width * 0.35), int(self.height * 0.7)), (60, 70, 80), -1)
            cv2.putText(img, "POST 02", (int(self.width * 0.22), int(self.height * 0.48)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        elif self.scene == "fence" or self.scene == "night":
            # Fence posts and barbed wire
            post_color = (80, 90, 100) if not self.is_night else (50, 100, 60)
            wire_color = (120, 130, 140) if not self.is_night else (80, 150, 90)
            for px in range(50, self.width, 90):
                cv2.line(img, (px, int(self.height * 0.4)), (px, int(self.height * 0.75)), post_color, 3)
            for wy in [0.45, 0.52, 0.60, 0.68]:
                cv2.line(img, (0, int(self.height * wy)), (self.width, int(self.height * wy)), wire_color, 1)

        # Draw virtual fence boundary line (red or cyan dashed)
        fence_y = int(self.height * 0.72)
        cv2.line(img, (0, fence_y), (self.width, fence_y), (0, 0, 220) if (int(t * 2) % 2 == 0) else (0, 180, 255), 2)
        cv2.putText(img, "VIRTUAL FENCE BOUNDARY (72%)", (10, fence_y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 220, 255), 1)

        # Dynamic patrol person (moves back and forth)
        self.person_x += int(1.5 * self.person_dir)
        if self.person_x > self.width - 150:
            self.person_dir = -1
        elif self.person_x < 80:
            self.person_dir = 1

        py = int(self.height * 0.52)
        pw, ph = 26, 68
        p_color = (0, 220, 180) if not self.is_night else (100, 255, 150)
        
        # Draw silhouette figure
        cv2.circle(img, (self.person_x + pw // 2, py + 10), 8, p_color, -1)
        cv2.rectangle(img, (self.person_x + 5, py + 18), (self.person_x + pw - 5, py + 48), p_color, -1)
        cv2.line(img, (self.person_x + 8, py + 48), (self.person_x + 5, py + ph), p_color, 3)
        cv2.line(img, (self.person_x + pw - 8, py + 48), (self.person_x + pw - 5, py + ph), p_color, 3)
        
        # Bounding box & tracking annotation
        cv2.rectangle(img, (self.person_x, py), (self.person_x + pw, py + ph), (0, 229, 184), 1)
        cv2.putText(img, "PERSON #204 0.93", (self.person_x, py - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 229, 184), 1)

        # Dynamic vehicle in gate scene
        if self.scene == "gate":
            if not self.vehicle_active and random.random() < 0.05:
                self.vehicle_active = True
                self.vehicle_x = -120

            if self.vehicle_active:
                self.vehicle_x += 3
                vx = self.vehicle_x
                vy = int(self.height * 0.62)
                vw, vh = 95, 42
                if vx < self.width + 100:
                    cv2.rectangle(img, (vx, vy), (vx + vw, vy + vh), (80, 80, 120), -1)
                    cv2.rectangle(img, (vx + 15, vy - 15), (vx + vw - 15, vy), (60, 60, 90), -1)
                    cv2.circle(img, (vx + 22, vy + vh), 8, (20, 20, 20), -1)
                    cv2.circle(img, (vx + vw - 22, vy + vh), 8, (20, 20, 20), -1)
                    # Plate
                    cv2.rectangle(img, (vx + 35, vy + vh - 14), (vx + 70, vy + vh - 4), (250, 250, 250), -1)
                    cv2.putText(img, "PB-11-AK", (vx + 36, vy + vh - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.25, (0, 0, 0), 1)
                    # Box & label
                    cv2.rectangle(img, (vx - 5, vy - 18), (vx + vw + 5, vy + vh + 5), (255, 165, 0), 1)
                    cv2.putText(img, "VEHICLE #311 (CAR) 0.91", (vx, vy - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 165, 0), 1)
                else:
                    self.vehicle_active = False

        # Vignette & tactical HUD overlay
        ts_str = time.strftime("%d/%m/%Y %H:%M:%S UTC")
        cv2.putText(img, f"{self.cam_id.upper()} · LIVE CCTV NVR", (14, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        cv2.putText(img, ts_str, (14, self.height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (200, 255, 200) if self.is_night else (220, 220, 220), 1)
        mode_label = "IR NIGHT MODE [ENHANCED]" if self.is_night else "OPTICAL HIGH-RES"
        cv2.putText(img, mode_label, (self.width - 200, self.height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 229, 184), 1)

        # Corner reticles
        ret_len = 12
        cv2.line(img, (10, 10), (10 + ret_len, 10), (0, 229, 184), 1)
        cv2.line(img, (10, 10), (10, 10 + ret_len), (0, 229, 184), 1)
        cv2.line(img, (self.width - 10, 10), (self.width - 10 - ret_len, 10), (0, 229, 184), 1)
        cv2.line(img, (self.width - 10, 10), (self.width - 10, 10 + ret_len), (0, 229, 184), 1)

        # Encode frame as JPEG
        success, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        return buffer.tobytes() if success else b""


# Stream registry
generators: dict[str, CameraStreamGenerator] = {
    "cam-2": CameraStreamGenerator("cam-2", scene="gate", is_night=False),
    "cam-3": CameraStreamGenerator("cam-3", scene="night", is_night=True),
    "cam-4": CameraStreamGenerator("cam-4", scene="fence", is_night=False),
}


def get_camera_frame(cam_id: str) -> bytes:
    if cam_id not in generators:
        generators[cam_id] = CameraStreamGenerator(cam_id)
    return generators[cam_id].generate_frame()


def stream_mjpeg(cam_id: str):
    """Generator yielding MJPEG multipart frames."""
    while True:
        frame_bytes = get_camera_frame(cam_id)
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.08)  # ~12 FPS
