"""
Deterministic test fixture generator for IBVAP (PRD v3 FR-1.6).
Creates a 4-second 640x360 MP4 video where an entity moves across the screen
crossing the virtual tripwire at 70% Y-axis height.
"""
import os
import cv2
import numpy as np


def generate_tripwire_crossing_video(output_path: str = "fixtures/test_crossing.mp4") -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    width, height = 640, 360
    fps = 30
    total_frames = 90  # 3 seconds

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    tripwire_y = int(height * 0.70)

    for i in range(total_frames):
        img = np.zeros((height, width, 3), dtype=np.uint8)
        img[:int(height * 0.45), :] = (30, 30, 35)
        img[int(height * 0.45):, :] = (45, 45, 50)

        # Draw tripwire reference line
        cv2.line(img, (0, tripwire_y), (width, tripwire_y), (0, 0, 220), 2)
        cv2.putText(img, "TRIPWIRE (70%)", (10, tripwire_y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        # Moving object: starts at Y = 80 (22%), moves down to Y = 280 (77%), crossing tripwire at Y = 222 (centroid Y=70%) around frame 40
        progress = i / float(total_frames - 1)
        obj_y = int(80 + progress * 200)
        obj_x = int(280 + np.sin(progress * np.pi) * 20)

        pw, ph = 36, 64
        # Draw entity in bright green (0, 255, 0) for reliable detector/fixture mask segmentation
        cv2.rectangle(img, (obj_x, obj_y), (obj_x + pw, obj_y + ph), (0, 255, 0), -1)
        cv2.circle(img, (obj_x + pw // 2, max(12, obj_y - 12)), 12, (0, 255, 0), -1)

        # Frame counter text
        cv2.putText(img, f"FIXTURE FRAME {i:03d} - Y={obj_y}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        out.write(img)

    out.release()
    return output_path


if __name__ == "__main__":
    path = generate_tripwire_crossing_video()
    print(f"Generated deterministic test fixture at {path}")
