import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon

# =========================================================================
# SIMPLE SYSTEM DESIGN FLOWCHART (No fancy decorations, pure clean architecture)
# Formatted for half-page placement in PowerPoint slides (Aspect ratio 4:3)
# =========================================================================
fig = plt.figure(figsize=(10.5, 8.5), dpi=160)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 10.5)
ax.set_ylim(0, 8.5)
ax.axis('off')

# Pure clean white background
fig.patch.set_facecolor('#FFFFFF')
ax.set_facecolor('#FFFFFF')

# Helper: Simple Rectangle Box (clean black border, pure white fill, no shadows)
def draw_box(cx, cy, w=2.80, h=0.82, title="", line2="", line3=""):
    x = cx - w / 2
    y = cy - h / 2
    rect = patches.Rectangle((x, y), w, h, linewidth=1.5, edgecolor='#000000', facecolor='#FFFFFF')
    ax.add_patch(rect)
    
    lines = [l for l in [title, line2, line3] if l]
    if len(lines) == 1:
        ax.text(cx, cy, lines[0], color='#000000', fontsize=10.0, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 2:
        ax.text(cx, cy + 0.13, lines[0], color='#000000', fontsize=9.8, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.13, lines[1], color='#000000', fontsize=9.2, ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 3:
        ax.text(cx, cy + 0.20, lines[0], color='#000000', fontsize=9.5, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy, lines[1], color='#000000', fontsize=9.0, ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.20, lines[2], color='#000000', fontsize=8.2, ha='center', va='center', fontfamily='sans-serif')

# Helper: Simple Diamond Box (clean black border, pure white fill, no shadows)
def draw_diamond(cx, cy, dw=2.80, dh=0.95, title="", line2="", line3=""):
    diamond = Polygon([[cx, cy + dh/2], [cx + dw/2, cy], [cx, cy - dh/2], [cx - dw/2, cy]],
                      closed=True, facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.5)
    ax.add_patch(diamond)
    
    lines = [l for l in [title, line2, line3] if l]
    if len(lines) == 1:
        ax.text(cx, cy, lines[0], color='#000000', fontsize=9.8, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 2:
        ax.text(cx, cy + 0.11, lines[0], color='#000000', fontsize=9.5, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.11, lines[1], color='#000000', fontsize=8.6, ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 3:
        ax.text(cx, cy + 0.18, lines[0], color='#000000', fontsize=9.2, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy, lines[1], color='#000000', fontsize=8.8, ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.18, lines[2], color='#000000', fontsize=7.8, ha='center', va='center', fontfamily='sans-serif')

# Helper: Simple Straight Black Arrow
def draw_arrow(x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color='#000000', lw=1.6, mutation_scale=12, shrinkA=0, shrinkB=0))

# Helper: Simple Corner Arrow
def draw_corner_arrow(points):
    for i in range(len(points) - 2):
        p1, p2 = points[i], points[i+1]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#000000', lw=1.6, solid_capstyle='round')
    p1, p2 = points[-2], points[-1]
    ax.annotate('', xy=(p2[0], p2[1]), xytext=(p1[0], p1[1]),
                arrowprops=dict(arrowstyle="-|>", color='#000000', lw=1.6, mutation_scale=12, shrinkA=0, shrinkB=0))

# Helper: Plain Text Branch Label
def draw_label(x, y, text):
    ax.text(x, y, text, color='#000000', fontsize=9.5, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')


# =========================================================================
# SIMPLE 3-COLUMN GRID
# =========================================================================
col1_x = 1.90
col2_x = 5.25
col3_x = 8.60

w_box = 2.80
h_box = 0.82
dw = 2.80
dh = 0.95

# 5 Balanced Horizontal Rows
y_r1 = 7.70
y_r2 = 6.30
y_r3 = 4.90
y_r4 = 3.45
y_r5 = 1.95

# ----------------- COLUMN 1: Ingestion & Frame Selection -----------------
draw_box(col1_x, y_r1, w_box, h_box, "Start: CCTV Cameras", "(RTSP Video Streams)")

draw_arrow(col1_x, y_r1 - h_box/2, col1_x, y_r2 + h_box/2)
draw_box(col1_x, y_r2, w_box, h_box, "RTSP Ingestion Engine", "Decode, Resize & Normalize")

draw_arrow(col1_x, y_r2 - h_box/2, col1_x, y_r3 + h_box/2)
draw_box(col1_x, y_r3, w_box, h_box, "Multi-Camera Buffer", "Queue Frames & Balance Load")

draw_arrow(col1_x, y_r3 - h_box/2, col1_x, y_r4 + dh/2)
draw_diamond(col1_x, y_r4, dw, dh, "Target Detected?", "(Person / Vehicle)")

# Branch No -> Discard Frame
draw_arrow(col1_x, y_r4 - dh/2, col1_x, y_r5 + h_box/2)
draw_label(col1_x + 0.28, (y_r4 - dh/2 + y_r5 + h_box/2)/2, "No")
draw_box(col1_x, y_r5, w_box, h_box, "Discard Routine Frame", "Continue Stream Ingestion")

# Branch Yes -> Connects to Column 2 AI Tracking
ch12_x = 3.55
draw_corner_arrow([
    (col1_x + dw/2, y_r4),
    (ch12_x, y_r4),
    (ch12_x, y_r1),
    (col2_x - w_box/2, y_r1)
])
draw_label(col1_x + dw/2 + 0.25, y_r4 + 0.18, "Yes")


# ----------------- COLUMN 2: AI Pipeline & Intelligence -----------------
draw_box(col2_x, y_r1, w_box, h_box, "ByteTrack Tracking", "Assign Track ID & Direction")

draw_arrow(col2_x, y_r1 - h_box/2, col2_x, y_r2 + dh/2)
draw_diamond(col2_x, y_r2, dw, dh, "Secondary Model", "Required? (Face/Plate)")

# Branch Yes -> Face & Plate Models
draw_arrow(col2_x, y_r2 - dh/2, col2_x, y_r3 + h_box/2)
draw_label(col2_x + 0.28, (y_r2 - dh/2 + y_r3 + h_box/2)/2, "Yes")
draw_box(col2_x, y_r3, w_box, h_box, "Run RetinaFace &", "PaddleOCR License Plate")

draw_arrow(col2_x, y_r3 - h_box/2, col2_x, y_r4 + dh/2)

# Branch No (Bypass around Face/Plate model to Security Breach)
ch2_bypass = 3.80
draw_corner_arrow([
    (col2_x - dw/2, y_r2),
    (ch2_bypass, y_r2),
    (ch2_bypass, y_r4),
    (col2_x - dw/2, y_r4)
])
draw_label(ch2_bypass - 0.05, (y_r2 + y_r4)/2, "No")

# Diamond: Security Breach or Loitering?
draw_diamond(col2_x, y_r4, dw, dh, "Security Breach", "or Loitering?", "(Fence / Dwell > 4s)")

# Branch No -> Display Normal Live Feed
draw_arrow(col2_x, y_r4 - dh/2, col2_x, y_r5 + h_box/2)
draw_label(col2_x + 0.28, (y_r4 - dh/2 + y_r5 + h_box/2)/2, "No")
draw_box(col2_x, y_r5, w_box, h_box, "Display Normal Feed", "Routine Live Monitoring")

# Branch Yes -> Connects to Column 3 Alert
ch23_x = 6.95
draw_corner_arrow([
    (col2_x + dw/2, y_r4),
    (ch23_x, y_r4),
    (ch23_x, y_r1),
    (col3_x - w_box/2, y_r1)
])
draw_label(col2_x + dw/2 + 0.25, y_r4 + 0.18, "Yes")


# ----------------- COLUMN 3: Alert & Command Dashboard -----------------
draw_box(col3_x, y_r1, w_box, h_box, "Generate Threat Alert", "& Capture Evidence Clip")

draw_arrow(col3_x, y_r1 - h_box/2, col3_x, y_r2 + h_box/2)
draw_box(col3_x, y_r2, w_box, h_box, "Store in PostgreSQL", "Broadcast via WebSocket")

draw_arrow(col3_x, y_r2 - h_box/2, col3_x, y_r3 + h_box/2)
draw_box(col3_x, y_r3, w_box, h_box, "Display on Dashboard", "Security Operator Terminal")

draw_arrow(col3_x, y_r3 - h_box/2, col3_x, y_r4 + dh/2)
draw_diamond(col3_x, y_r4, dw, dh, "Operator Action", "Required?")

# Branch Yes -> Dispatch Team
draw_arrow(col3_x, y_r4 - dh/2, col3_x, y_r5 + h_box/2)
draw_label(col3_x + 0.28, (y_r4 - dh/2 + y_r5 + h_box/2)/2, "Yes")
draw_box(col3_x, y_r5, w_box, h_box, "Dispatch Response Team", "Deploy Ground Patrol Unit")

# Save outputs
plt.savefig("flowchart_decision_tree_ppt.png", dpi=200, facecolor='#FFFFFF', edgecolor='none')
plt.savefig("flowchart_decision_tree_ppt.jpg", dpi=200, facecolor='#FFFFFF', edgecolor='none')
print("Successfully rendered simple system design flowchart!")
