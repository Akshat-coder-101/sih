import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Polygon
import numpy as np

# Set figure for 16:9 widescreen presentation slide (1920x1080 at 120 dpi = 16 x 9 inches)
fig = plt.figure(figsize=(16, 9), dpi=130)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis('off')

# Background
fig.patch.set_facecolor('#F8FAFC')
ax.set_facecolor('#F8FAFC')

# ----------------- HEADER -----------------
# Header banner
header_bg = FancyBboxPatch((0, 8.05), 16, 0.95, boxstyle="square,pad=0", 
                           facecolor="#FFFFFF", edgecolor="#E2E8F0", linewidth=1.5)
ax.add_patch(header_bg)

# Team / SIH Badges
perceptrons_badge = FancyBboxPatch((0.6, 8.32), 2.1, 0.42, boxstyle="round,pad=0.08,rounding_size=0.2",
                                   facecolor="#F1F5F9", edgecolor="#CBD5E1", linewidth=1)
ax.add_patch(perceptrons_badge)
ax.text(1.65, 8.53, "● PERCEPTRONS", color="#0369A1", fontsize=9.5, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')

sih_badge = FancyBboxPatch((2.9, 8.32), 2.8, 0.42, boxstyle="round,pad=0.08,rounding_size=0.2",
                           facecolor="#EFF6FF", edgecolor="#BFDBFE", linewidth=1)
ax.add_patch(sih_badge)
ax.text(4.3, 8.53, "SMART INDIA HACKATHON 2026", color="#1D4ED8", fontsize=9.5, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')

# Main Title & Subtitle
ax.text(9.4, 8.62, "SYSTEM LOGIC & DECISION FLOWCHART", color="#0F172A", fontsize=15, fontweight='black', ha='center', va='center', fontfamily='sans-serif')
ax.text(9.4, 8.28, "IBVAP: Intelligent Border Video Analytics Platform — Edge AI Pipeline & Tactical Response", color="#64748B", fontsize=9.5, ha='center', va='center', fontfamily='sans-serif')

# ----------------- COLUMN CONTAINERS & HEADERS -----------------
cols_x = [0.6, 4.4, 8.2, 12.0]
col_w = 3.4
col_h = 6.6
col_bottom = 1.25

col_meta = [
    ("1. RTSP Ingestion & Buffer", "#E0F2FE", "#BAE6FD", "#0284C7"),
    ("2. AI Analysis & Tracking", "#F3E8FF", "#E9D5FF", "#7C3AED"),
    ("3. Threat Intelligence Rules", "#FEF3C7", "#FDE68A", "#D97706"),
    ("4. Command Center & Response", "#FFE4E6", "#FECDD3", "#E11D48"),
]

for idx, (cx, (title, bg, border, text_col)) in enumerate(zip(cols_x, col_meta)):
    # Subtle Column Card
    col_rect = FancyBboxPatch((cx, col_bottom), col_w, col_h, boxstyle="round,pad=0.05,rounding_size=0.15",
                              facecolor="#FFFFFF", edgecolor="#E2E8F0", linewidth=1.2, alpha=0.85)
    ax.add_patch(col_rect)
    
    # Column Header Pill
    hdr_pill = FancyBboxPatch((cx + 0.25, 7.35), col_w - 0.5, 0.38, boxstyle="round,pad=0.05,rounding_size=0.1",
                              facecolor=bg, edgecolor=border, linewidth=1)
    ax.add_patch(hdr_pill)
    ax.text(cx + col_w / 2, 7.54, title, color=text_col, fontsize=10, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')

# Helper function to draw cards
def draw_card(x, y, w, h, title, subtitle="", sub2="", border="#CBD5E1", fill="#FFFFFF", tcol="#0F172A", alert=False):
    shadow = FancyBboxPatch((x + 0.02, y - 0.02), w, h, boxstyle="round,pad=0.04,rounding_size=0.12",
                            facecolor="#000000", edgecolor="none", alpha=0.04)
    ax.add_patch(shadow)
    card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12",
                          facecolor=fill, edgecolor=border, linewidth=2.0 if alert else 1.5)
    ax.add_patch(card)
    
    if subtitle and sub2:
        ax.text(x + w/2, y + h*0.68, title, color=tcol, fontsize=9.5, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(x + w/2, y + h*0.42, subtitle, color="#64748B", fontsize=8.2, ha='center', va='center', fontfamily='sans-serif')
        ax.text(x + w/2, y + h*0.19, sub2, color="#334155", fontsize=8.0, fontweight='semibold', ha='center', va='center', fontfamily='sans-serif')
    elif subtitle:
        ax.text(x + w/2, y + h*0.62, title, color=tcol, fontsize=9.5, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(x + w/2, y + h*0.30, subtitle, color="#64748B", fontsize=8.2, ha='center', va='center', fontfamily='sans-serif')
    else:
        ax.text(x + w/2, y + h*0.5, title, color=tcol, fontsize=9.5, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')

# Helper function to draw diamond decision nodes
def draw_diamond(cx, cy, dw, dh, title, subtitle="", border="#475569", fill="#FFFFFF", tcol="#0F172A"):
    # Shadow
    shadow = Polygon([[cx, cy + dh/2 - 0.02], [cx + dw/2 + 0.02, cy], [cx, cy - dh/2 - 0.02], [cx - dw/2 - 0.02, cy]],
                     closed=True, facecolor="#000000", edgecolor="none", alpha=0.04)
    ax.add_patch(shadow)
    
    # Diamond shape
    diamond = Polygon([[cx, cy + dh/2], [cx + dw/2, cy], [cx, cy - dh/2], [cx - dw/2, cy]],
                      closed=True, facecolor=fill, edgecolor=border, linewidth=1.8)
    ax.add_patch(diamond)
    
    if subtitle:
        ax.text(cx, cy + 0.10, title, color=tcol, fontsize=9.2, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax.text(cx, cy - 0.12, subtitle, color="#64748B", fontsize=7.6, ha='center', va='center', fontfamily='sans-serif')
    else:
        ax.text(cx, cy, title, color=tcol, fontsize=9.2, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')

# Helper for orthogonal arrows
def draw_arrow(x1, y1, x2, y2, color="#475569", lw=1.6):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=11, 
                                shrinkA=0, shrinkB=0))

def draw_corner_arrow(points, color="#475569", lw=1.6):
    for i in range(len(points) - 2):
        p1, p2 = points[i], points[i+1]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, lw=lw, solid_capstyle='round')
    # Final segment with arrow
    p1, p2 = points[-2], points[-1]
    ax.annotate('', xy=(p2[0], p2[1]), xytext=(p1[0], p1[1]),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=11, 
                                shrinkA=0, shrinkB=0))

def draw_label(x, y, text, color="#16A34A", bg="#DCFCE7"):
    bbox_props = dict(boxstyle="round,pad=0.2,rounding_size=0.1", fc=bg, ec="none")
    ax.text(x, y, text, color=color, fontsize=8.0, fontweight='bold', ha='center', va='center', bbox=bbox_props)


# ==========================================
# COLUMN 1: Ingestion & Buffer
# ==========================================
c1_x = 0.85
c1_w = 2.9
draw_card(c1_x, 6.35, c1_w, 0.75, "Start: Existing CCTV Cameras", "IP Cameras (CAM-01, 02, 03)", "RTSP H.264 / H.265 Streams")
draw_arrow(c1_x + c1_w/2, 6.35, c1_x + c1_w/2, 5.85)

draw_card(c1_x, 5.05, c1_w, 0.80, "RTSP Stream Ingestion", "Hardware Decode • Resize • Normalize", "Dynamic Keyframe Throttling & UTC Tag")
draw_arrow(c1_x + c1_w/2, 5.05, c1_x + c1_w/2, 4.55)

draw_card(c1_x, 3.75, c1_w, 0.80, "Multi-Camera Queue Buffer", "Dedicated Worker Queues (1 to N)", "Buffer Frames & Balance GPU Load")
draw_arrow(c1_x + c1_w/2, 3.75, c1_x + c1_w/2, 3.22)

draw_diamond(c1_x + c1_w/2, 2.65, 2.35, 1.12, "Target Detected?", "(Person / Vehicle YOLOv8)")

# Col 1 Branch No -> Discard
draw_corner_arrow([(c1_x + c1_w/2 - 1.18, 2.65), (c1_x + 0.35, 2.65), (c1_x + 0.35, 1.95)])
draw_label(c1_x + 0.35, 2.80, "No", color="#64748B", bg="#F1F5F9")
draw_card(c1_x + 0.05, 1.40, 1.8, 0.55, "Routine Frame", "Drop & Log Telemetry", fill="#F8FAFC", border="#CBD5E1")

# Col 1 Branch Yes -> to Column 2 ByteTrack
draw_corner_arrow([(c1_x + c1_w/2 + 1.18, 2.65), (4.05, 2.65), (4.05, 6.75), (4.65, 6.75)], color="#16A34A")
draw_label(3.65, 2.80, "Yes", color="#16A34A", bg="#DCFCE7")


# ==========================================
# COLUMN 2: AI Pipeline & Tracking
# ==========================================
c2_x = 4.65
c2_w = 2.9
draw_card(c2_x, 6.35, c2_w, 0.80, "ByteTrack Tracking Engine", "Kalman Filter Multi-Object Association", "Assigns Persistent ID, Box & Velocity")
draw_arrow(c2_x + c2_w/2, 6.35, c2_x + c2_w/2, 5.62)

draw_diamond(c2_x + c2_w/2, 5.05, 2.35, 1.12, "Secondary Model?", "(Biometric / Plate OCR)")

# Diamond 2 Branch Yes -> Deep Feature Extraction
draw_arrow(c2_x + c2_w/2, 4.49, c2_x + c2_w/2, 3.90, color="#16A34A")
draw_label(c2_x + c2_w/2 + 0.30, 4.25, "Yes", color="#16A34A", bg="#DCFCE7")

draw_card(c2_x, 3.05, c2_w, 0.80, "Deep Feature Extraction", "• RetinaFace + ArcFace (Biometrics)", "• PaddleOCR (License Plate Recognition)")

# Box 2.2 -> Rules Engine
draw_arrow(c2_x + c2_w/2, 3.05, c2_x + c2_w/2, 2.45)

# Diamond 2 Branch No -> Bypass to Rules Engine
draw_corner_arrow([(c2_x + c2_w/2 + 1.18, 5.05), (c2_x + c2_w - 0.05, 5.05), (c2_x + c2_w - 0.05, 2.05), (c2_x + c2_w/2 + 1.45, 2.05)])
draw_label(c2_x + c2_w + 0.15, 5.05, "No", color="#64748B", bg="#F1F5F9")

draw_card(c2_x, 1.65, c2_w, 0.80, "Spatial-Temporal Rules Engine", "• Virtual Fence (Ray-Casting Polygon)", "• Dwell Time Analytics (Timer > 4.0s)", border="#7C3AED")

# Col 2 to Col 3 (Rules Engine -> Security Breach Decision)
draw_corner_arrow([(c2_x + c2_w, 2.05), (7.85, 2.05), (7.85, 6.75), (8.45, 6.75)])


# ==========================================
# COLUMN 3: Threat Intelligence
# ==========================================
c3_x = 8.45
c3_w = 2.9

draw_diamond(c3_x + c3_w/2, 6.75, 2.45, 1.18, "Security Breach?", "(Fence Cross / Curfew / Loiter)", border="#D97706")

# Breach No -> Authorized Activity
draw_arrow(c3_x + c3_w/2, 6.16, c3_x + c3_w/2, 5.55)
draw_label(c3_x + c3_w/2 + 0.30, 5.85, "No", color="#64748B", bg="#F1F5F9")
draw_card(c3_x, 4.80, c3_w, 0.70, "Authorized Activity", "Stream Routine Live Feed to Console", "No Alarm Triggered")

# Breach Yes -> Threat Event Triggered
draw_corner_arrow([(c3_x + c3_w/2 + 1.23, 6.75), (c3_x + c3_w + 0.15, 6.75), (c3_x + c3_w + 0.15, 3.85), (c3_x + c3_w, 3.85)], color="#DC2626")
draw_label(c3_x + c3_w - 0.10, 6.95, "Yes", color="#DC2626", bg="#FEE2E2")

draw_card(c3_x, 3.45, c3_w, 0.80, "Threat Event Triggered (CRITICAL)", "Risk & Priority Score Calculation", "Instant Notification Engine", border="#F43F5E", fill="#FFF1F2", tcol="#BE123C", alert=True)
draw_arrow(c3_x + c3_w/2, 3.45, c3_w/2 + c3_x, 2.85, color="#DC2626")

draw_card(c3_x, 1.95, c3_w, 0.85, "Forensic Evidence Vault", "• Auto HD Snapshot (JPEG with BBox)", "• 10-sec Pre/Post Video Clip (MP4)", border="#CBD5E1")

# Col 3 to Col 4 (Evidence -> Gateway)
draw_corner_arrow([(c3_x + c3_w, 2.37), (11.65, 2.37), (11.65, 6.75), (12.25, 6.75)])


# ==========================================
# COLUMN 4: Command Center & Response
# ==========================================
c4_x = 12.25
c4_w = 2.9
draw_card(c4_x, 6.35, c4_w, 0.80, "FastAPI & PostgreSQL Gateway", "Persist Audit Logs, Geotags & Timestamps", "Broadcast Real-Time WebSocket (<200ms)")
draw_arrow(c4_x + c4_w/2, 6.35, c4_x + c4_w/2, 5.75)

draw_card(c4_x, 4.95, c4_w, 0.80, "React Command Dashboard", "• Multi-Camera Live Matrix & Viewport", "• Priority Alert Feed & Audio Alarm", border="#0284C7")
draw_arrow(c4_x + c4_w/2, 4.95, c4_x + c4_w/2, 4.32)

draw_diamond(c4_x + c4_w/2, 3.75, 2.35, 1.12, "Operator Action?", "(Verify & Escalate)")

# Action Required -> Escalate
draw_arrow(c4_x + c4_w/2, 3.19, c4_x + c4_w/2, 2.65, color="#DC2626")
draw_label(c4_x + c4_w/2 + 0.42, 2.98, "Action", color="#DC2626", bg="#FEE2E2")

draw_card(c4_x, 1.85, c4_w, 0.80, "Escalate & Dispatch Unit", "Deploy On-Ground Quick Response Team (QRT)", "Trigger Field Patrol Alert Protocol", border="#DC2626", fill="#FEF2F2", tcol="#991B1B", alert=True)

# Routine -> Archive
draw_corner_arrow([(c4_x + c4_w/2 + 1.18, 3.75), (c4_x + c4_w + 0.15, 3.75), (c4_x + c4_w + 0.15, 1.45), (c4_x + c4_w - 0.2, 1.45)])
draw_label(c4_x + c4_w + 0.15, 3.95, "Routine", color="#64748B", bg="#F1F5F9")
draw_card(c4_x + 0.5, 1.25, 2.2, 0.45, "Acknowledge & Archive", "Audit Log Record Stored", fill="#F8FAFC", border="#CBD5E1")


# ==========================================
# BOTTOM TECH STACK FOOTER
# ==========================================
footer_bg = FancyBboxPatch((0.6, 0.22), 14.8, 0.72, boxstyle="round,pad=0.06,rounding_size=0.15",
                           facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.2)
ax.add_patch(footer_bg)

ax.text(1.7, 0.58, "TECH STACK", color="#0F172A", fontsize=11, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
ax.plot([2.6, 2.6], [0.35, 0.80], color="#E2E8F0", lw=1.5)

tech_items = [
    ("RTSP Streaming", 3.4),
    ("Python 3.12+", 4.8),
    ("OpenCV Video", 6.2),
    ("YOLOv8 AI", 7.6),
    ("ByteTrack MOT", 9.1),
    ("PaddleOCR ANPR", 10.6),
    ("FastAPI Async", 12.0),
    ("PostgreSQL DB", 13.4),
    ("React Dashboard", 14.7),
]

for name, tx in tech_items:
    pill = FancyBboxPatch((tx - 0.58, 0.38), 1.16, 0.38, boxstyle="round,pad=0.04,rounding_size=0.1",
                          facecolor="#F8FAFC", edgecolor="#E2E8F0", linewidth=1)
    ax.add_patch(pill)
    ax.text(tx, 0.57, name, color="#1E293B", fontsize=8.2, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')

# Save outputs
plt.savefig("flowchart_decision_tree_ppt.jpg", dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
plt.savefig("flowchart_decision_tree_ppt.png", dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
print("Successfully rendered flowchart_decision_tree_ppt.jpg and .png with pixel-perfect alignment!")
