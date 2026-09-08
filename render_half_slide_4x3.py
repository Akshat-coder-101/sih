import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Polygon

# =========================================================================
# COMPACT 3-COLUMN HALF-SLIDE FLOWCHART
# Specially engineered to fill HALF of a PowerPoint slide
# Aspect Ratio: 4:3 (Width: 11.0, Height: 9.2 inches)
# =========================================================================
fig = plt.figure(figsize=(11.0, 9.2), dpi=160)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 11.0)
ax.set_ylim(0, 9.2)
ax.axis('off')

# Clean background
bg_color = '#F0F4F8'
fig.patch.set_facecolor(bg_color)
ax.set_facecolor(bg_color)

# Helper: Draw Card
def draw_card(cx, cy, w=2.95, h=0.82, title="", line2="", line3="", border="#CBD5E1", fill="#FFFFFF", tcol="#0F172A"):
    x = cx - w / 2
    y = cy - h / 2
    
    # Drop shadow
    shadow = FancyBboxPatch((x + 0.025, y - 0.025), w, h, boxstyle="round,pad=0.03,rounding_size=0.10",
                            facecolor="#000000", edgecolor="none", alpha=0.04)
    ax.add_patch(shadow)
    
    # Card
    card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.10",
                          facecolor=fill, edgecolor=border, linewidth=1.4)
    ax.add_patch(card)
    
    lines = [l for l in [title, line2, line3] if l]
    if len(lines) == 1:
        ax.text(cx, cy, lines[0], color=tcol, fontsize=10.0, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 2:
        ax.text(cx, cy + 0.13, lines[0], color=tcol, fontsize=9.8, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.13, lines[1], color=tcol, fontsize=9.4, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 3:
        ax.text(cx, cy + 0.20, lines[0], color=tcol, fontsize=9.6, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy, lines[1], color=tcol, fontsize=9.0, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.20, lines[2], color="#475569", fontsize=8.0, ha='center', va='center', fontfamily='sans-serif')

# Helper: Draw Diamond
def draw_diamond(cx, cy, dw=2.95, dh=0.92, title="", line2="", line3="", border="#334155", fill="#FFFFFF", tcol="#0F172A"):
    shadow = Polygon([[cx, cy + dh/2 - 0.025], [cx + dw/2 + 0.025, cy], [cx, cy - dh/2 - 0.025], [cx - dw/2 - 0.025, cy]],
                     closed=True, facecolor="#000000", edgecolor="none", alpha=0.04)
    ax.add_patch(shadow)
    
    diamond = Polygon([[cx, cy + dh/2], [cx + dw/2, cy], [cx, cy - dh/2], [cx - dw/2, cy]],
                      closed=True, facecolor=fill, edgecolor=border, linewidth=1.5)
    ax.add_patch(diamond)
    
    lines = [l for l in [title, line2, line3] if l]
    if len(lines) == 1:
        ax.text(cx, cy, lines[0], color=tcol, fontsize=9.8, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 2:
        ax.text(cx, cy + 0.11, lines[0], color=tcol, fontsize=9.6, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.11, lines[1], color="#475569", fontsize=8.5, ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 3:
        ax.text(cx, cy + 0.18, lines[0], color=tcol, fontsize=9.2, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy, lines[1], color=tcol, fontsize=8.8, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.18, lines[2], color="#475569", fontsize=7.8, ha='center', va='center', fontfamily='sans-serif')

def draw_arrow(x1, y1, x2, y2, color="#1E293B", lw=1.8):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=12, shrinkA=0, shrinkB=0))

def draw_corner_arrow(points, color="#1E293B", lw=1.8):
    for i in range(len(points) - 2):
        p1, p2 = points[i], points[i+1]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, lw=lw, solid_capstyle='round')
    p1, p2 = points[-2], points[-1]
    ax.annotate('', xy=(p2[0], p2[1]), xytext=(p1[0], p1[1]),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=12, shrinkA=0, shrinkB=0))

def draw_label(x, y, text, color="#0F172A"):
    ax.text(x, y, text, color=color, fontsize=9.2, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')


# =========================================================================
# 3 BALANCED COLUMNS
# =========================================================================
c1_x = 1.95
c2_x = 5.50
c3_x = 9.05

card_w = 2.95
card_h = 0.82
dw = 2.95
dh = 0.92

# ----------------- COLUMN 1: Ingestion & Filter -----------------
y1 = 8.35
draw_card(c1_x, y1, card_w, card_h, "Start: Existing", "CCTV Cameras")

y2 = 6.95
draw_arrow(c1_x, y1 - card_h/2, c1_x, y2 + card_h/2)
draw_card(c1_x, y2, card_w, card_h, "RTSP Stream", "Ingestion & Decoding")

y3 = 5.55
draw_arrow(c1_x, y2 - card_h/2, c1_x, y3 + card_h/2)
draw_card(c1_x, y3, card_w, card_h, "Multi-Camera", "Queue Buffer")

y4 = 3.90
draw_arrow(c1_x, y3 - card_h/2, c1_x, y4 + dh/2)
draw_diamond(c1_x, y4, dw, dh, "Target Detected?", "(Person / Vehicle)")

# Branch No -> Log Routine Frame (down)
y5 = 2.15
draw_arrow(c1_x, y4 - dh/2, c1_x, y5 + card_h/2)
draw_label(c1_x + 0.30, (y4 - dh/2 + y5 + card_h/2)/2, "No")
draw_card(c1_x, y5, card_w, card_h, "Log Routine Frame", "& Continue Stream")

# Branch Yes -> Connects to Column 2 ByteTrack (from right apex of diamond)
draw_corner_arrow([
    (c1_x + dw/2, y4),
    (3.72, y4),
    (3.72, y1),
    (c2_x - card_w/2, y1)
])
draw_label(c1_x + dw/2 + 0.30, y4 + 0.18, "Yes")


# ----------------- COLUMN 2: AI Pipeline & Intelligence -----------------
draw_card(c2_x, y1, card_w, card_h, "ByteTrack: Assign", "Track ID & Trajectory")

y2_c2 = 6.85
draw_arrow(c2_x, y1 - card_h/2, c2_x, y2_c2 + dh/2)
draw_diamond(c2_x, y2_c2, dw, dh, "Secondary Model", "Required? (Face/Plate)")

# Branch Yes -> Run RetinaFace
y3_c2 = 5.25
draw_arrow(c2_x, y2_c2 - dh/2, c2_x, y3_c2 + card_h/2)
draw_label(c2_x + 0.30, (y2_c2 - dh/2 + y3_c2 + card_h/2)/2, "Yes")
draw_card(c2_x, y3_c2, card_w, card_h, "Run RetinaFace &", "License Plate OCR")

# Security Breach Diamond:
y4_c2 = 3.65
draw_diamond(c2_x, y4_c2, dw, dh, "Security Breach or Loitering?", "(Fence / Dwell > 4s)")

# Arrow from RetinaFace into Security Breach:
draw_arrow(c2_x, y3_c2 - card_h/2, c2_x, y4_c2 + dh/2)

# Bypass arrow from Secondary Model (No) to Security Breach:
draw_corner_arrow([
    (c2_x - dw/2, y2_c2),
    (3.72, y2_c2),
    (3.72, y4_c2),
    (c2_x - dw/2, y4_c2)
])
draw_label(3.72, (y2_c2 + y4_c2)/2, "No")

# Security Breach Branch No -> Display Normal Live Feed (down)
draw_arrow(c2_x, y4_c2 - dh/2, c2_x, y5 + card_h/2)
draw_label(c2_x + 0.30, (y4_c2 - dh/2 + y5 + card_h/2)/2, "No")
draw_card(c2_x, y5, card_w, card_h, "Display Normal Live", "Feed to Operator")

# Security Breach Branch Yes -> Connects to Column 3 Alert (from right apex)
draw_corner_arrow([
    (c2_x + dw/2, y4_c2),
    (7.28, y4_c2),
    (7.28, y1),
    (c3_x - card_w/2, y1)
])
draw_label(c2_x + dw/2 + 0.30, y4_c2 + 0.18, "Yes")


# ----------------- COLUMN 3: Command Center & Response -----------------
draw_card(c3_x, y1, card_w, card_h, "Generate Alert &", "Capture Evidence", "Snapshot / Video Clip")

y2_c3 = 6.85
draw_arrow(c3_x, y1 - card_h/2, c3_x, y2_c3 + card_h/2)
draw_card(c3_x, y2_c3, card_w, card_h, "Store in PostgreSQL", "& Broadcast via WebSocket")

y3_c3 = 5.35
draw_arrow(c3_x, y2_c3 - card_h/2, c3_x, y3_c3 + card_h/2)
draw_card(c3_x, y3_c3, card_w, card_h, "Display on Security", "Operator Dashboard")

y4_c3 = 3.75
draw_arrow(c3_x, y3_c3 - card_h/2, c3_x, y4_c3 + dh/2)
draw_diamond(c3_x, y4_c3, dw, dh, "Operator Action", "Required?")

# Branch Yes -> Escalate & Dispatch
draw_arrow(c3_x, y4_c3 - dh/2, c3_x, y5 + card_h/2)
draw_label(c3_x + 0.30, (y4_c3 - dh/2 + y5 + card_h/2)/2, "Yes")
draw_card(c3_x, y5, card_w, card_h, "Escalate & Dispatch", "Response Team", "Deploy Quick Response Team")

# Overwrite flowchart_decision_tree_ppt so user can directly use it
plt.savefig("flowchart_decision_tree_ppt.png", dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
plt.savefig("flowchart_decision_tree_ppt.jpg", dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
plt.savefig("flowchart_half_slide_4x3.png", dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
print("Rendered pristine compact 3-column flowchart tailored for half-slide in PPT!")
