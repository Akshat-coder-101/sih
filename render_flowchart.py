import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Polygon

# Standard 16:9 widescreen presentation slide (1920x1080 at 150 dpi)
fig = plt.figure(figsize=(16, 9), dpi=150)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis('off')

# Clean minimal presentation background matching reference
bg_color = '#F0F4F8'
fig.patch.set_facecolor(bg_color)
ax.set_facecolor(bg_color)

# Helper: Draw Card
def draw_card(cx, cy, w=2.30, h=1.00, title="", line2="", line3="", border="#CBD5E1", fill="#FFFFFF", tcol="#0F172A"):
    x = cx - w / 2
    y = cy - h / 2
    
    # Soft drop shadow
    shadow = FancyBboxPatch((x + 0.025, y - 0.025), w, h, boxstyle="round,pad=0.03,rounding_size=0.10",
                            facecolor="#000000", edgecolor="none", alpha=0.04)
    ax.add_patch(shadow)
    
    # Main white card
    card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.10",
                          facecolor=fill, edgecolor=border, linewidth=1.4)
    ax.add_patch(card)
    
    lines = [l for l in [title, line2, line3] if l]
    if len(lines) == 1:
        ax.text(cx, cy, lines[0], color=tcol, fontsize=10.0, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 2:
        ax.text(cx, cy + 0.15, lines[0], color=tcol, fontsize=9.8, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.15, lines[1], color=tcol, fontsize=9.4, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 3:
        ax.text(cx, cy + 0.24, lines[0], color=tcol, fontsize=9.5, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy, lines[1], color=tcol, fontsize=9.0, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.23, lines[2], color="#475569", fontsize=8.2, ha='center', va='center', fontfamily='sans-serif')

# Helper: Draw Diamond
def draw_diamond(cx, cy, dw=2.30, dh=1.12, title="", line2="", line3="", line4="", border="#475569", fill="#FFFFFF", tcol="#0F172A"):
    # Soft shadow
    shadow = Polygon([[cx, cy + dh/2 - 0.025], [cx + dw/2 + 0.025, cy], [cx, cy - dh/2 - 0.025], [cx - dw/2 - 0.025, cy]],
                     closed=True, facecolor="#000000", edgecolor="none", alpha=0.04)
    ax.add_patch(shadow)
    
    # Diamond
    diamond = Polygon([[cx, cy + dh/2], [cx + dw/2, cy], [cx, cy - dh/2], [cx - dw/2, cy]],
                      closed=True, facecolor=fill, edgecolor=border, linewidth=1.5)
    ax.add_patch(diamond)
    
    lines = [l for l in [title, line2, line3, line4] if l]
    if len(lines) == 1:
        ax.text(cx, cy, lines[0], color=tcol, fontsize=9.8, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 2:
        ax.text(cx, cy + 0.13, lines[0], color=tcol, fontsize=9.6, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.13, lines[1], color="#475569", fontsize=8.5, ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 3:
        ax.text(cx, cy + 0.20, lines[0], color=tcol, fontsize=9.2, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy, lines[1], color=tcol, fontsize=8.8, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.19, lines[2], color="#475569", fontsize=7.8, ha='center', va='center', fontfamily='sans-serif')
    elif len(lines) == 4:
        ax.text(cx, cy + 0.28, lines[0], color=tcol, fontsize=9.0, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy + 0.09, lines[1], color=tcol, fontsize=8.6, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.09, lines[2], color="#475569", fontsize=7.6, ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.26, lines[3], color="#475569", fontsize=7.4, ha='center', va='center', fontfamily='sans-serif')

# Helper: Draw Straight Arrow
def draw_arrow(x1, y1, x2, y2, color="#1E293B", lw=1.8):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=12, shrinkA=0, shrinkB=0))

# Helper: Draw Orthogonal Corner Arrow
def draw_corner_arrow(points, color="#1E293B", lw=1.8):
    for i in range(len(points) - 2):
        p1, p2 = points[i], points[i+1]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, lw=lw, solid_capstyle='round')
    p1, p2 = points[-2], points[-1]
    ax.annotate('', xy=(p2[0], p2[1]), xytext=(p1[0], p1[1]),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=12, shrinkA=0, shrinkB=0))

# Helper: Plain Text Branch Label (matching reference without badge container)
def draw_label(x, y, text, color="#0F172A"):
    ax.text(x, y, text, color=color, fontsize=9.2, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')


# =========================================================================
# EXACT 5-COLUMN COORDINATES ACROSS 4 ROWS
# =========================================================================
x_col1 = 1.70
x_col2 = 4.85
x_col3 = 8.00
x_col4 = 11.15
x_col5 = 14.30

y_row1 = 7.70
y_row2 = 5.60
y_row3 = 3.50
y_row4 = 1.40

card_w = 2.30
card_h = 1.00
dw = 2.30
dh = 1.12

# ==========================================
# ROW 1
# ==========================================
draw_card(x_col1, y_row1, card_w, card_h, "Start: Existing", "CCTV Cameras")
draw_arrow(x_col1 + card_w/2, y_row1, x_col2 - card_w/2, y_row1)

draw_card(x_col2, y_row1, card_w, card_h, "RTSP Stream", "Ingestion & Decoding")
draw_arrow(x_col2 + card_w/2, y_row1, x_col3 - card_w/2, y_row1)

draw_card(x_col3, y_row1, card_w, card_h, "Multi-Camera", "Queue Buffer")

# Arrow from Row 1 Queue Buffer down and left to Row 2 Target Detected
y_mid12 = (y_row1 + y_row2) / 2
draw_corner_arrow([
    (x_col3, y_row1 - card_h/2),
    (x_col3, y_mid12),
    (x_col2, y_mid12),
    (x_col2, y_row2 + dh/2)
])


# ==========================================
# ROW 2
# ==========================================
# Diamond: Target Detected?
draw_diamond(x_col2, y_row2, dw, dh, "Target Detected?", "(Person/Vehicle)?")

# Branch No -> Log Routine Frame (Col 1)
draw_arrow(x_col2 - dw/2, y_row2, x_col1 + card_w/2, y_row2)
draw_label((x_col2 - dw/2 + x_col1 + card_w/2) / 2, y_row2 + 0.16, "No")
draw_card(x_col1, y_row2, card_w, card_h, "Log Routine Frame", "& Continue Stream")

# Branch Yes -> ByteTrack (Col 3)
draw_arrow(x_col2 + dw/2, y_row2, x_col3 - card_w/2, y_row2)
draw_label((x_col2 + dw/2 + x_col3 - card_w/2) / 2, y_row2 + 0.16, "Yes")
draw_card(x_col3, y_row2, card_w, card_h, "ByteTrack: Assign", "Track ID & Trajectory")

# Arrow to Secondary Model (Col 4)
draw_arrow(x_col3 + card_w/2, y_row2, x_col4 - dw/2, y_row2)
draw_diamond(x_col4, y_row2, dw, dh, "Secondary Model", "Required?")

# Branch Yes -> Run RetinaFace & License Plate OCR (Col 5)
draw_arrow(x_col4 + dw/2, y_row2, x_col5 - card_w/2, y_row2)
draw_label((x_col4 + dw/2 + x_col5 - card_w/2) / 2, y_row2 + 0.16, "Yes")
draw_card(x_col5, y_row2, card_w, card_h, "Run RetinaFace &", "License Plate OCR")

# Branch No -> Goes down and left to Row 3 Security Breach Diamond
y_mid23 = (y_row2 + y_row3) / 2
dh_r3 = 1.25
dw_r3 = 2.50
draw_corner_arrow([
    (x_col4, y_row2 - dh/2),
    (x_col4, y_mid23),
    (x_col1, y_mid23),
    (x_col1, y_row3 + dh_r3/2)
])
draw_label(x_col4 + 0.25, y_mid23 + 0.18, "No")


# ==========================================
# ROW 3
# ==========================================
# Diamond: Security Breach or Loitering?
draw_diamond(x_col1, y_row3, dw_r3, dh_r3, "Security Breach", "or Loitering?", "(Fence Crossing / Dwell", "> 4s / Night Curfew)")

# Branch No -> Display Normal Live Feed (Col 2)
draw_arrow(x_col1 + dw_r3/2, y_row3, x_col2 - card_w/2, y_row3)
draw_label((x_col1 + dw_r3/2 + x_col2 - card_w/2) / 2, y_row3 + 0.16, "No")
draw_card(x_col2, y_row3, card_w, card_h, "Display Normal Live", "Feed to Operator")

# Branch Yes -> Drops straight down to Row 4 (Col 1)
draw_arrow(x_col1, y_row3 - dh_r3/2, x_col1, y_row4 + card_h/2)
draw_label(x_col1 + 0.28, (y_row3 - dh_r3/2 + y_row4 + card_h/2) / 2, "Yes")


# ==========================================
# ROW 4
# ==========================================
draw_card(x_col1, y_row4, card_w, card_h, "Generate Alert &", "Capture Evidence", "Snapshot / Video Clip")
draw_arrow(x_col1 + card_w/2, y_row4, x_col2 - card_w/2, y_row4)

draw_card(x_col2, y_row4, card_w, card_h, "Store in PostgreSQL", "& Broadcast via", "WebSocket")
draw_arrow(x_col2 + card_w/2, y_row4, x_col3 - card_w/2, y_row4)

draw_card(x_col3, y_row4, card_w, card_h, "Display on Security", "Operator Dashboard")
draw_arrow(x_col3 + card_w/2, y_row4, x_col4 - dw/2, y_row4)

draw_diamond(x_col4, y_row4, dw, dh, "Operator Action", "Required?")

draw_arrow(x_col4 + dw/2, y_row4, x_col5 - card_w/2, y_row4)
draw_label((x_col4 + dw/2 + x_col5 - card_w/2) / 2, y_row4 + 0.16, "Yes")

draw_card(x_col5, y_row4, card_w, card_h, "Escalate & Dispatch", "Response Team")

# Save high-resolution outputs
plt.savefig("flowchart_decision_tree_ppt.jpg", dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
plt.savefig("flowchart_decision_tree_ppt.png", dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
print("Rendered exact matching flowchart with strict alignment!")
