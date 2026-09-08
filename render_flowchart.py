import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Polygon

# =========================================================================
# SYSTEM DESIGN & LOGIC DECISION FLOWCHART
# Engineered specifically for half-page placement in PowerPoint (Aspect Ratio 4:3)
# Clean, deterministic, mathematically aligned 3-column architecture
# =========================================================================
fig = plt.figure(figsize=(11.5, 9.2), dpi=160)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 11.5)
ax.set_ylim(0, 9.2)
ax.axis('off')

# Clean background matching presentation reference
bg_color = '#F1F5F9'
fig.patch.set_facecolor(bg_color)
ax.set_facecolor(bg_color)

# Helper: Draw Card
def draw_card(cx, cy, w=2.90, h=0.84, title="", line2="", line3="", border="#CBD5E1", fill="#FFFFFF", tcol="#0F172A"):
    x = cx - w / 2
    y = cy - h / 2
    
    # Subtle drop shadow
    shadow = FancyBboxPatch((x + 0.025, y - 0.025), w, h, boxstyle="round,pad=0.03,rounding_size=0.10",
                            facecolor="#000000", edgecolor="none", alpha=0.04)
    ax.add_patch(shadow)
    
    # White card
    card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.10",
                          facecolor=fill, edgecolor=border, linewidth=1.4)
    ax.add_patch(card)
    
    lines = [l for l in [title, line2, line3] if l]
    if len(lines) == 1:
        ax.text(cx, cy, lines[0], color=tcol, fontsize=10.0, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 2:
        ax.text(cx, cy + 0.13, lines[0], color=tcol, fontsize=9.8, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.13, lines[1], color=tcol, fontsize=9.2, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 3:
        ax.text(cx, cy + 0.20, lines[0], color=tcol, fontsize=9.5, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy, lines[1], color=tcol, fontsize=8.8, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.20, lines[2], color="#475569", fontsize=8.0, ha='center', va='center', fontfamily='sans-serif')

# Helper: Draw Diamond
def draw_diamond(cx, cy, dw=2.90, dh=0.94, title="", line2="", line3="", border="#334155", fill="#FFFFFF", tcol="#0F172A"):
    # Subtle drop shadow
    shadow = Polygon([[cx, cy + dh/2 - 0.025], [cx + dw/2 + 0.025, cy], [cx, cy - dh/2 - 0.025], [cx - dw/2 - 0.025, cy]],
                     closed=True, facecolor="#000000", edgecolor="none", alpha=0.04)
    ax.add_patch(shadow)
    
    # Diamond
    diamond = Polygon([[cx, cy + dh/2], [cx + dw/2, cy], [cx, cy - dh/2], [cx - dw/2, cy]],
                      closed=True, facecolor=fill, edgecolor=border, linewidth=1.5)
    ax.add_patch(diamond)
    
    lines = [l for l in [title, line2, line3] if l]
    if len(lines) == 1:
        ax.text(cx, cy, lines[0], color=tcol, fontsize=9.8, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 2:
        ax.text(cx, cy + 0.11, lines[0], color=tcol, fontsize=9.5, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.11, lines[1], color="#475569", fontsize=8.4, ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 3:
        ax.text(cx, cy + 0.18, lines[0], color=tcol, fontsize=9.2, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy, lines[1], color=tcol, fontsize=8.6, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.18, lines[2], color="#475569", fontsize=7.6, ha='center', va='center', fontfamily='sans-serif')

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
# EXACT 3-COLUMN × 5-ROW COORDINATE GRID
# =========================================================================
c1_x = 2.05
c2_x = 5.75
c3_x = 9.45

card_w = 2.90
card_h = 0.84
dw = 2.90
dh = 0.94

# Exact Horizontal Y-Alignments across all 3 columns
row1_y = 8.30
row2_y = 6.85
row3_y = 5.40
row4_y = 3.90
row5_y = 2.20

# ----------------- COLUMN 1: Ingestion & Target Filtering -----------------
draw_card(c1_x, row1_y, card_w, card_h, "Start: Existing", "CCTV Cameras")

draw_arrow(c1_x, row1_y - card_h/2, c1_x, row2_y + card_h/2)
draw_card(c1_x, row2_y, card_w, card_h, "RTSP Stream", "Ingestion & Decoding")

draw_arrow(c1_x, row2_y - card_h/2, c1_x, row3_y + card_h/2)
draw_card(c1_x, row3_y, card_w, card_h, "Multi-Camera", "Queue Buffer")

draw_arrow(c1_x, row3_y - card_h/2, c1_x, row4_y + dh/2)
draw_diamond(c1_x, row4_y, dw, dh, "Target Detected?", "(Person / Vehicle)")

# Branch No -> Log Routine Frame
draw_arrow(c1_x, row4_y - dh/2, c1_x, row5_y + card_h/2)
draw_label(c1_x + 0.30, (row4_y - dh/2 + row5_y + card_h/2)/2, "No")
draw_card(c1_x, row5_y, card_w, card_h, "Log Routine Frame", "& Continue Stream")

# Branch Yes -> Connects to Column 2 ByteTrack (Channel X = 3.90)
channel_12 = 3.90
draw_corner_arrow([
    (c1_x + dw/2, row4_y),
    (channel_12, row4_y),
    (channel_12, row1_y),
    (c2_x - card_w/2, row1_y)
])
draw_label(c1_x + dw/2 + 0.28, row4_y + 0.18, "Yes")


# ----------------- COLUMN 2: AI Pipeline & Intelligence -----------------
draw_card(c2_x, row1_y, card_w, card_h, "ByteTrack: Assign", "Track ID & Trajectory")

draw_arrow(c2_x, row1_y - card_h/2, c2_x, row2_y + dh/2)
draw_diamond(c2_x, row2_y, dw, dh, "Secondary Model", "Required? (Face/Plate)")

# Branch Yes -> Run RetinaFace & License Plate OCR
draw_arrow(c2_x, row2_y - dh/2, c2_x, row3_y + card_h/2)
draw_label(c2_x + 0.30, (row2_y - dh/2 + row3_y + card_h/2)/2, "Yes")
draw_card(c2_x, row3_y, card_w, card_h, "Run RetinaFace &", "License Plate OCR")

# Arrow from RetinaFace into Security Breach
draw_arrow(c2_x, row3_y - card_h/2, c2_x, row4_y + dh/2)

# Branch No (Bypass around RetinaFace on internal left channel X = 4.15)
draw_corner_arrow([
    (c2_x - dw/2, row2_y),
    (4.15, row2_y),
    (4.15, row4_y),
    (c2_x - dw/2, row4_y)
])
draw_label(4.15, (row2_y + row4_y)/2, "No")

# Diamond 3: Security Breach or Loitering?
draw_diamond(c2_x, row4_y, dw, dh, "Security Breach", "or Loitering?", "(Fence / Dwell > 4s)")

# Branch No -> Display Normal Live Feed
draw_arrow(c2_x, row4_y - dh/2, c2_x, row5_y + card_h/2)
draw_label(c2_x + 0.30, (row4_y - dh/2 + row5_y + card_h/2)/2, "No")
draw_card(c2_x, row5_y, card_w, card_h, "Display Normal Live", "Feed to Operator")

# Branch Yes -> Connects to Column 3 Alert (Channel X = 7.60)
channel_23 = 7.60
draw_corner_arrow([
    (c2_x + dw/2, row4_y),
    (channel_23, row4_y),
    (channel_23, row1_y),
    (c3_x - card_w/2, row1_y)
])
draw_label(c2_x + dw/2 + 0.28, row4_y + 0.18, "Yes")


# ----------------- COLUMN 3: Command Center & Response -----------------
draw_card(c3_x, row1_y, card_w, card_h, "Generate Alert &", "Capture Evidence", "Snapshot / Video Clip")

draw_arrow(c3_x, row1_y - card_h/2, c3_x, row2_y + card_h/2)
draw_card(c3_x, row2_y, card_w, card_h, "Store in PostgreSQL", "& Broadcast via WebSocket")

draw_arrow(c3_x, row2_y - card_h/2, c3_x, row3_y + card_h/2)
draw_card(c3_x, row3_y, card_w, card_h, "Display on Security", "Operator Dashboard")

draw_arrow(c3_x, row3_y - card_h/2, c3_x, row4_y + dh/2)
draw_diamond(c3_x, row4_y, dw, dh, "Operator Action", "Required?")

# Branch Yes -> Escalate & Dispatch Unit
draw_arrow(c3_x, row4_y - dh/2, c3_x, row5_y + card_h/2)
draw_label(c3_x + 0.30, (row4_y - dh/2 + row5_y + card_h/2)/2, "Yes")
draw_card(c3_x, row5_y, card_w, card_h, "Escalate & Dispatch", "Response Team", "Deploy Quick Response Team")

# Save master outputs
plt.savefig("flowchart_decision_tree_ppt.png", dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
plt.savefig("flowchart_decision_tree_ppt.jpg", dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
print("Successfully generated master half-slide flowchart!")
