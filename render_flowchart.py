import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon

# =========================================================================
# PURE BLACK & WHITE SYSTEM DESIGN FLOWCHART
# Formatted for Half-Slide in PowerPoint (Aspect Ratio ~ 3:4 / Portrait)
# Width: 8.0 inches, Height: 10.8 inches (2400 x 3240 at 300 dpi)
# Clean, crisp, textbook system design: pure white background, 1.2px black borders,
# clear typography, zero overlapping lines, perfect margins.
# =========================================================================

fig = plt.figure(figsize=(8.0, 10.8), dpi=300)
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
