"""Render the IBVAP technical workflow as a 1600 x 800 PNG/JPEG."""

import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon

WIDTH, HEIGHT = 16, 8
fig = plt.figure(figsize=(WIDTH, HEIGHT), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, WIDTH)
ax.set_ylim(0, HEIGHT)
ax.axis("off")
fig.patch.set_facecolor("#ffffff")
ax.set_facecolor("#ffffff")


def box(cx, cy, width, height, title, detail, fill="#f7fbff", edge="#17324d"):
    rect = patches.FancyBboxPatch(
    (cx - width / 2, cy - height / 2), width, height,
    boxstyle="round,pad=0.025,rounding_size=0.08",
    linewidth=1.3, edgecolor=edge, facecolor=fill, zorder=2,
    )
    ax.add_patch(rect)
    ax.text(cx, cy + 0.14, title, ha="center", va="center", fontsize=8.4,
        fontweight="bold", color="#102a43", zorder=3)
    ax.text(cx, cy - 0.13, detail, ha="center", va="center", fontsize=6.6,
        color="#334e68", zorder=3)


def diamond(cx, cy, width, height, title, detail, fill="#fffaf0"):
    shape = Polygon(
    [(cx, cy + height / 2), (cx + width / 2, cy),
     (cx, cy - height / 2), (cx - width / 2, cy)],
    closed=True, linewidth=1.3, edgecolor="#7c5a00", facecolor=fill, zorder=2,
    )
    ax.add_patch(shape)
    ax.text(cx, cy + 0.10, title, ha="center", va="center", fontsize=8.0,
        fontweight="bold", color="#5c4300", zorder=3)
    ax.text(cx, cy - 0.12, detail, ha="center", va="center", fontsize=6.2,
        color="#6b5b35", zorder=3)


def arrow(x1, y1, x2, y2, label=None, color="#52606d"):
    patch = FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=11,
        linewidth=1.25, color=color, connectionstyle="arc3,rad=0", zorder=1,
    )
    ax.add_patch(patch)
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.13, label,
                ha="center", va="center", fontsize=6.7,
                fontweight="bold", color=color, zorder=4,
                bbox=dict(facecolor="white", edgecolor="none", pad=0.7))


ax.text(0.55, 7.58, "IBVAP — TECHNICAL SURVEILLANCE & INTEGRITY WORKFLOW",
    fontsize=14, fontweight="bold", color="#102a43", va="center")
ax.text(15.45, 7.58, "1600 × 800 px  |  Prototype Architecture",
    fontsize=7.2, color="#627d98", ha="right", va="center")
ax.plot([0.55, 15.45], [7.38, 7.38], color="#bcccdc", linewidth=0.8)

# Primary processing pipeline.
main_y = 5.55
main_w, main_h = 1.72, 0.82
nodes = [
    (1.35, "CCTV / RTSP", "IP cameras + files"),
    (3.18, "Ingestion", "OpenCV decode"),
    (5.01, "Queue Buffer", "per-camera workers"),
    (6.84, "AI Inference", "YOLO + detector"),
    (8.67, "Tracking", "ByteTrack IDs"),
    (10.50, "Rule Engine", "fence / dwell / curfew"),
]
for index, (x, title, detail) in enumerate(nodes):
    box(x, main_y, main_w, main_h, title, detail)
    if index: arrow(nodes[index - 1][0] + main_w / 2, main_y, x - main_w / 2, main_y)

diamond(12.35, main_y, 1.75, 1.00, "Threat?", "intrusion / weapon / ANPR")
arrow(10.50 + main_w / 2, main_y, 11.48, main_y)
box(14.55, 6.45, 1.85, 0.72, "Normal Live Stream", "continue monitoring", fill="#f2fbf6", edge="#2f855a")
arrow(12.35, main_y + 0.50, 14.55, 6.09, "No", color="#2f855a")
box(12.35, 4.12, 2.08, 0.82, "Alert + Evidence", "snapshot + clip buffer", fill="#fff5f5", edge="#b42318")
arrow(12.35, main_y - 0.50, 12.35, 4.53, "Yes", color="#b42318")

# Integrity lane.
lane_y = 2.62
ax.text(0.62, 3.32, "INTEGRITY & RESPONSE LANE", fontsize=8.2,
    fontweight="bold", color="#486581", va="center")
ax.plot([0.62, 15.38], [3.20, 3.20], color="#d9e2ec", linewidth=0.8)
integrity = [
    (2.10, "Encrypted Evidence", "AES-256-GCM at rest"),
    (4.35, "Local Hash Chain", "SHA-256 + ledger seq"),
    (6.60, "Merkle Commitment", "root + alert proof"),
    (8.85, "Model Provenance", "artifact + rule hashes"),
    (11.10, "2-of-3 Approval", "RBAC signatures"),
    (13.35, "Blockchain Anchor", "root + provenance only"),
]
for index, (x, title, detail) in enumerate(integrity):
    fill = "#f7fbff" if index < 4 else "#f8f5ff"
    edge = "#17324d" if index < 4 else "#5b3f8c"
    box(x, lane_y, 1.92, 0.78, title, detail, fill=fill, edge=edge)
    if index: arrow(integrity[index - 1][0] + 0.96, lane_y, x - 0.96, lane_y, color="#627d98")
arrow(12.35, 3.71, 2.10, 3.01, "persist + hash", color="#627d98")

# Dashboard and response lane.
box(3.05, 0.92, 2.32, 0.72, "Operator Dashboard", "WebSocket alert + status", fill="#f2fbf6", edge="#2f855a")
box(7.20, 0.92, 2.32, 0.72, "Verify Integrity", "chain + Merkle + anchor", fill="#fffaf0", edge="#7c5a00")
diamond(11.10, 0.92, 2.15, 0.86, "Action?", "operator review")
box(14.10, 0.92, 1.80, 0.72, "C2 Dispatch", "ground response", fill="#fff5f5", edge="#b42318")
arrow(4.35, lane_y - 0.39, 3.05, 1.28, "event feed")
arrow(6.60, lane_y - 0.39, 7.20, 1.28, "proof")
arrow(13.35, lane_y - 0.39, 7.20, 1.28, "verify")
arrow(4.21, 0.92, 6.04, 0.92, "review")
arrow(12.18, 0.92, 13.20, 0.92, "Yes", color="#b42318")
arrow(10.02, 0.92, 8.36, 0.92, "No", color="#2f855a")

ax.text(0.62, 0.25,
    "Privacy boundary: raw video, snapshots, GPS, faces, plates, credentials, and keys remain off-chain.",
    fontsize=7.0, color="#627d98", va="center")
ax.text(15.38, 0.25,
    "Blockchain proves commitment integrity — not alert truth.",
    fontsize=7.0, color="#7c5a00", ha="right", va="center")

plt.savefig("flowchart_decision_tree_ppt.png", dpi=100, facecolor="#ffffff", edgecolor="none")
plt.savefig("flowchart_decision_tree_ppt.jpg", dpi=100, facecolor="#ffffff", edgecolor="none")
print("Generated 1600 x 800 IBVAP technical workflow.")
raise SystemExit(0)
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, Polygon

# =========================================================================
# PURE BLACK & WHITE SYSTEM DESIGN FLOWCHART
# Formatted for Half-Slide in PowerPoint (Aspect Ratio ~ 3:4 / Portrait)
# Width: 8.0 inches, Height: 10.8 inches (2400 x 3240 at 300 dpi)
# Clean, crisp, textbook system design: pure white background, 1.2px black borders,
# clear typography, zero overlapping lines, perfect margins.
# =========================================================================

"""Render the IBVAP technical workflow as a 1600 x 800 PNG/JPEG."""

WIDTH, HEIGHT = 16, 8
fig = plt.figure(figsize=(WIDTH, HEIGHT), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, WIDTH)
ax.set_ylim(0, HEIGHT)
ax.axis("off")
fig.patch.set_facecolor("#ffffff")
ax.set_facecolor("#ffffff")


def box(cx, cy, width, height, title, detail, fill="#f7fbff", edge="#17324d"):
    rect = patches.FancyBboxPatch(
    (cx - width / 2, cy - height / 2), width, height,
    boxstyle="round,pad=0.025,rounding_size=0.08",
    linewidth=1.3, edgecolor=edge, facecolor=fill, zorder=2,
    )
    ax.add_patch(rect)
    ax.text(cx, cy + 0.14, title, ha="center", va="center", fontsize=8.4,
        fontweight="bold", color="#102a43", zorder=3)
    ax.text(cx, cy - 0.13, detail, ha="center", va="center", fontsize=6.6,
        color="#334e68", zorder=3)


def diamond(cx, cy, width, height, title, detail, fill="#fffaf0"):
    shape = Polygon(
    [(cx, cy + height / 2), (cx + width / 2, cy),
     (cx, cy - height / 2), (cx - width / 2, cy)],
    closed=True, linewidth=1.3, edgecolor="#7c5a00", facecolor=fill, zorder=2,
    )
    ax.add_patch(shape)
    ax.text(cx, cy + 0.10, title, ha="center", va="center", fontsize=8.0,
        fontweight="bold", color="#5c4300", zorder=3)
    ax.text(cx, cy - 0.12, detail, ha="center", va="center", fontsize=6.2,
        color="#6b5b35", zorder=3)


def arrow(x1, y1, x2, y2, label=None, color="#52606d"):
    patch = FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=11,
        linewidth=1.25, color=color, connectionstyle="arc3,rad=0", zorder=1,
    )
    ax.add_patch(patch)
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.13, label,
                ha="center", va="center", fontsize=6.7,
                fontweight="bold", color=color, zorder=4,
                bbox=dict(facecolor="white", edgecolor="none", pad=0.7))


# Header
ax.text(0.55, 7.58, "IBVAP — TECHNICAL SURVEILLANCE & INTEGRITY WORKFLOW",
    fontsize=14, fontweight="bold", color="#102a43", va="center")
ax.text(15.45, 7.58, "1600 × 800 px  |  Prototype Architecture",
    fontsize=7.2, color="#627d98", ha="right", va="center")
ax.plot([0.55, 15.45], [7.38, 7.38], color="#bcccdc", linewidth=0.8)

# Main pipeline, left to right.
main_y = 5.55
main_w, main_h = 1.72, 0.82
nodes = [
    (1.35, "CCTV / RTSP", "IP cameras + files"),
    (3.18, "Ingestion", "OpenCV decode"),
    (5.01, "Queue Buffer", "per-camera workers"),
    (6.84, "AI Inference", "YOLO + detector"),
    (8.67, "Tracking", "ByteTrack IDs"),
    (10.50, "Rule Engine", "fence / dwell / curfew"),
]
for index, (x, title, detail) in enumerate(nodes):
    box(x, main_y, main_w, main_h, title, detail)
    if index:
        previous_x = nodes[index - 1][0]
        arrow(previous_x + main_w / 2, main_y, x - main_w / 2, main_y)

# Decision and live-stream branch.
diamond(12.35, main_y, 1.75, 1.00, "Threat?", "intrusion / weapon / ANPR")
arrow(10.50 + main_w / 2, main_y, 11.48, main_y)
box(14.55, 6.45, 1.85, 0.72, "Normal Live Stream", "continue monitoring", fill="#f2fbf6", edge="#2f855a")
arrow(12.35, main_y + 0.50, 14.55, 6.09, "No", color="#2f855a")

# Threat branch downward.
box(12.35, 4.12, 2.08, 0.82, "Alert + Evidence", "snapshot + clip buffer", fill="#fff5f5", edge="#b42318")
arrow(12.35, main_y - 0.50, 12.35, 4.53, "Yes", color="#b42318")

# Integrity lane.
lane_y = 2.62
ax.text(0.62, 3.32, "INTEGRITY & RESPONSE LANE", fontsize=8.2,
    fontweight="bold", color="#486581", va="center")
ax.plot([0.62, 15.38], [3.20, 3.20], color="#d9e2ec", linewidth=0.8)

integrity = [
    (2.10, "Encrypted Evidence", "AES-256-GCM at rest"),
    (4.35, "Local Hash Chain", "SHA-256 + ledger seq"),
    (6.60, "Merkle Commitment", "root + alert proof"),
    (8.85, "Model Provenance", "artifact + rule hashes"),
    (11.10, "2-of-3 Approval", "RBAC signatures"),
    (13.35, "Blockchain Anchor", "root + provenance only"),
]
for index, (x, title, detail) in enumerate(integrity):
    fill = "#f7fbff" if index < 4 else "#f8f5ff"
    edge = "#17324d" if index < 4 else "#5b3f8c"
    box(x, lane_y, 1.92, 0.78, title, detail, fill=fill, edge=edge)
    if index:
        previous_x = integrity[index - 1][0]
        arrow(previous_x + 0.96, lane_y, x - 0.96, lane_y, color="#627d98")

# Connect alert generation to integrity lane.
arrow(12.35, 3.71, 2.10, 3.01, "persist + hash", color="#627d98")

# Dashboard and response lane.
box(3.05, 0.92, 2.32, 0.72, "Operator Dashboard", "WebSocket alert + status", fill="#f2fbf6", edge="#2f855a")
box(7.20, 0.92, 2.32, 0.72, "Verify Integrity", "chain + Merkle + anchor", fill="#fffaf0", edge="#7c5a00")
diamond(11.10, 0.92, 2.15, 0.86, "Action?", "operator review")
box(14.10, 0.92, 1.80, 0.72, "C2 Dispatch", "ground response", fill="#fff5f5", edge="#b42318")

arrow(4.35, lane_y - 0.39, 3.05, 1.28, "event feed")
arrow(6.60, lane_y - 0.39, 7.20, 1.28, "proof")
arrow(13.35, lane_y - 0.39, 7.20, 1.28, "verify")
arrow(4.21, 0.92, 10.02, 0.92, "review")
arrow(12.18, 0.92, 13.20, 0.92, "Yes", color="#b42318")
arrow(10.02, 0.92, 8.36, 0.92, "No", color="#2f855a")

# Footer legend and claim boundary.
ax.text(0.62, 0.25,
    "Privacy boundary: raw video, snapshots, GPS, faces, plates, credentials, and keys remain off-chain.",
    fontsize=7.0, color="#627d98", va="center")
ax.text(15.38, 0.25,
    "Blockchain proves commitment integrity — not alert truth.",
    fontsize=7.0, color="#7c5a00", ha="right", va="center")

plt.savefig("flowchart_decision_tree_ppt.png", dpi=100, facecolor="#ffffff", edgecolor="none")
plt.savefig("flowchart_decision_tree_ppt.jpg", dpi=100, facecolor="#ffffff", edgecolor="none")
print("Generated 1600 x 800 IBVAP technical workflow.")
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 8.0)
ax.set_ylim(0, 10.8)
ax.axis('off')

# Pure white background
fig.patch.set_facecolor('#FFFFFF')
ax.set_facecolor('#FFFFFF')

# Helper: Simple White Box with 1.2px Black Border
def draw_box(cx, cy, w=2.80, h=0.48, line1="", line2=""):
    x = cx - w / 2
    y = cy - h / 2
    rect = patches.Rectangle((x, y), w, h, linewidth=1.2, edgecolor='#000000', facecolor='#FFFFFF', zorder=2)
    ax.add_patch(rect)
    
    if line1 and line2:
        ax.text(cx, cy + 0.085, line1, color='#000000', fontsize=9.0, fontweight='bold', ha='center', va='center', fontfamily='sans-serif', zorder=3)
        ax.text(cx, cy - 0.085, line2, color='#000000', fontsize=7.8, ha='center', va='center', fontfamily='sans-serif', zorder=3)
    elif line1:
        ax.text(cx, cy, line1, color='#000000', fontsize=9.0, fontweight='bold', ha='center', va='center', fontfamily='sans-serif', zorder=3)

# Helper: Simple White Diamond with 1.2px Black Border
def draw_diamond(cx, cy, dw=2.60, dh=0.68, line1="", line2=""):
    diamond = Polygon([[cx, cy + dh/2], [cx + dw/2, cy], [cx, cy - dh/2], [cx - dw/2, cy]],
                      closed=True, facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.2, zorder=2)
    ax.add_patch(diamond)
    
    if line1 and line2:
        ax.text(cx, cy + 0.08, line1, color='#000000', fontsize=8.6, fontweight='bold', ha='center', va='center', fontfamily='sans-serif', zorder=3)
        ax.text(cx, cy - 0.08, line2, color='#000000', fontsize=7.4, ha='center', va='center', fontfamily='sans-serif', zorder=3)
    elif line1:
        ax.text(cx, cy, line1, color='#000000', fontsize=8.6, fontweight='bold', ha='center', va='center', fontfamily='sans-serif', zorder=3)

# Helper: Simple Black Arrow
def draw_arrow(x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color='#000000', lw=1.2, mutation_scale=11, shrinkA=0, shrinkB=0),
                zorder=1)

# Helper: Simple Text Label (Yes / No)
def draw_label(x, y, text):
    ax.text(x, y, text, color='#000000', fontsize=8.5, fontweight='bold', ha='center', va='center', fontfamily='sans-serif', zorder=4)


# =========================================================================
# COORDINATES (CENTRAL SPINE WITH CLEAR HORIZONTAL LEAF BRANCHES)
# =========================================================================
cx = 4.00        # Center line
lx = 1.20        # Left branch box center (width 1.80 -> span [0.30, 2.10])
rx = 6.80        # Right branch box center (width 1.80 -> span [5.90, 7.70])

w_main = 2.80
h_main = 0.48

w_side = 1.80
h_side = 0.44

dw = 2.60        # Diamond span [cx - 1.30, cx + 1.30] = [2.70, 5.30]
dh = 0.68

# Vertical coordinates (11 distinct levels from top to bottom)
y1  = 10.20
y2  = 9.24
y3  = 8.28
y4  = 7.32
y5  = 6.36
y6  = 5.40
y7  = 4.44
y8  = 3.48
y9  = 2.52
y10 = 1.56
y11 = 0.60

# 1. Start CCTV
draw_box(cx, y1, w_main, h_main, "Start: CCTV Video Stream", "(IP Cameras CAM-01, 02, 03)")

# 2. RTSP Ingestion
draw_arrow(cx, y1 - h_main/2, cx, y2 + h_main/2)
draw_box(cx, y2, w_main, h_main, "RTSP Ingestion & Decoding", "(OpenCV Frame Extraction)")

# 3. Queue Buffer
draw_arrow(cx, y2 - h_main/2, cx, y3 + h_main/2)
draw_box(cx, y3, w_main, h_main, "Multi-Camera Queue Buffer", "(Frame Buffering & Load Balance)")

# 4. AI Detection
draw_arrow(cx, y3 - h_main/2, cx, y4 + h_main/2)
draw_box(cx, y4, w_main, h_main, "AI Detection Engine", "(YOLOv8 Object Detection)")

# 5. Decision: Target Detected?
draw_arrow(cx, y4 - h_main/2, cx, y5 + dh/2)
draw_diamond(cx, y5, dw, dh, "Target Detected?", "(Person / Vehicle)")

# Branch 5 No -> Left to Drop Frame
# Diamond left tip is at cx - dw/2 = 2.70; Left box right edge is at lx + w_side/2 = 2.10 (Gap = 0.60)
draw_arrow(cx - dw/2, y5, lx + w_side/2, y5)
draw_label((cx - dw/2 + lx + w_side/2) / 2, y5 + 0.13, "No")
draw_box(lx, y5, w_side, h_side, "Drop Routine Frame", "(Continue Monitoring)")

# 6. Branch 5 Yes -> Down to Object Tracking
draw_arrow(cx, y5 - dh/2, cx, y6 + h_main/2)
draw_label(cx + 0.22, (y5 - dh/2 + y6 + h_main/2) / 2, "Yes")
draw_box(cx, y6, w_main, h_main, "Object Tracking (ByteTrack)", "(Trajectory & Unique Track ID)")

# 7. Decision: Security Breach?
draw_arrow(cx, y6 - h_main/2, cx, y7 + dh/2)
draw_diamond(cx, y7, dw, dh, "Security Breach?", "(Fence / Dwell / Curfew)")

# Branch 7 No -> Left to Normal Live Stream
draw_arrow(cx - dw/2, y7, lx + w_side/2, y7)
draw_label((cx - dw/2 + lx + w_side/2) / 2, y7 + 0.13, "No")
draw_box(lx, y7, w_side, h_side, "Normal Live Stream", "(No Threat Detected)")

# 8. Branch 7 Yes -> Down to Generate Alert
draw_arrow(cx, y7 - dh/2, cx, y8 + h_main/2)
draw_label(cx + 0.22, (y7 - dh/2 + y8 + h_main/2) / 2, "Yes")
draw_box(cx, y8, w_main, h_main, "Generate Alert & Evidence", "(Snapshot + Video Clip Buffer)")

# 9. Store in Database
draw_arrow(cx, y8 - h_main/2, cx, y9 + h_main/2)
draw_box(cx, y9, w_main, h_main, "Store in PostgreSQL Database", "(Audit Log & Geotag Metadata)")

# 10. Display on Dashboard
draw_arrow(cx, y9 - h_main/2, cx, y10 + h_main/2)
draw_box(cx, y10, w_main, h_main, "Security Operator Dashboard", "(Real-Time WebSocket Feed)")

# 11. Decision: Action Required?
draw_arrow(cx, y10 - h_main/2, cx, y11 + dh/2)
draw_diamond(cx, y11, dw, dh, "Action Required?", "(Operator Review)")

# Branch 11 No -> Left to Archive Event
draw_arrow(cx - dw/2, y11, lx + w_side/2, y11)
draw_label((cx - dw/2 + lx + w_side/2) / 2, y11 + 0.13, "No")
draw_box(lx, y11, w_side, h_side, "Archive Event Log", "(Save Audit Record)")

# Branch 11 Yes -> Right to Dispatch Response Team
# Diamond right tip is at cx + dw/2 = 5.30; Right box left edge is at rx - w_side/2 = 5.90 (Gap = 0.60)
draw_arrow(cx + dw/2, y11, rx - w_side/2, y11)
draw_label((cx + dw/2 + rx - w_side/2) / 2, y11 + 0.13, "Yes")
draw_box(rx, y11, w_side, h_side, "Dispatch Response Team", "(Deploy Ground Patrol)")

# Save simple black & white outputs
plt.savefig("flowchart_decision_tree_ppt.png", dpi=300, facecolor='#FFFFFF', edgecolor='none')
plt.savefig("flowchart_decision_tree_ppt.jpg", dpi=300, facecolor='#FFFFFF', edgecolor='none')
print("Successfully generated simple black-and-white system design flowchart!")
