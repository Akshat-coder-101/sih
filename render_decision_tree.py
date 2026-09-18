"""Render the IBVAP technical decision tree at 1600 x 800."""

import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon

fig = plt.figure(figsize=(16, 8), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 16)
ax.set_ylim(0, 8)
ax.axis("off")
fig.patch.set_facecolor("#ffffff")
ax.set_facecolor("#ffffff")

NAVY = "#111111"
TEXT = "#1f1f1f"
MUTED = "#5f5f5f"
LINE = "#333333"
NODE_FILL = "#ffffff"
DECISION_FILL = "#f2f2f2"
DECISION_EDGE = "#111111"


def node(x, y, w, h, title, detail, fill=NODE_FILL, edge=NAVY):
    ax.add_patch(patches.FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.03,rounding_size=0.08",
        facecolor=fill, edgecolor=edge, linewidth=1.2, zorder=2,
    ))
    ax.text(x, y + 0.12, title, ha="center", va="center", fontsize=8.5,
            fontweight="bold", color=TEXT, zorder=3)
    ax.text(x, y - 0.13, detail, ha="center", va="center", fontsize=6.6,
            color=MUTED, zorder=3)


def decision(x, y, w, h, title, detail):
    ax.add_patch(Polygon(
        [(x, y + h / 2), (x + w / 2, y),
         (x, y - h / 2), (x - w / 2, y)],
        closed=True, facecolor=DECISION_FILL, edgecolor=DECISION_EDGE,
        linewidth=1.2, zorder=2,
    ))
    ax.text(x, y + 0.10, title, ha="center", va="center", fontsize=8.2,
            fontweight="bold", color=TEXT, zorder=3)
    ax.text(x, y - 0.12, detail, ha="center", va="center", fontsize=6.4,
            color=MUTED, zorder=3)


def arrow(x1, y1, x2, y2, label="", color=LINE):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=11,
        linewidth=1.2, color=color, connectionstyle="arc3,rad=0", zorder=1,
    ))
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.14, label,
                ha="center", va="center", fontsize=7.0, fontweight="bold",
                color=TEXT, bbox=dict(facecolor="white", edgecolor="none", pad=1), zorder=4)


ax.text(0.55, 7.58, "IBVAP — TECHNICAL DECISION TREE", fontsize=15,
        fontweight="bold", color=NAVY, va="center")
ax.text(15.45, 7.58, "1600 × 800 px  |  HLD / LLD", fontsize=7.2,
        color=MUTED, ha="right", va="center")
ax.plot([0.55, 15.45], [7.36, 7.36], color="#cbd5df", linewidth=0.8)

# Main decision spine.
y = 5.55
w, h = 1.72, 0.82
main = [
        (1.25, "CCTV / RTSP", "IP cameras + files", NODE_FILL, NAVY),
        (3.15, "Ingest Frames", "OpenCV + TLS", NODE_FILL, NAVY),
        (5.05, "AI Detect", "YOLO person / vehicle", NODE_FILL, NAVY),
        (6.95, "Track Objects", "ByteTrack IDs", NODE_FILL, NAVY),
]
for index, item in enumerate(main):
    x, title, detail, fill, edge = item
    node(x, y, w, h, title, detail, fill, edge)
    if index:
        arrow(main[index - 1][0] + w / 2, y, x - w / 2, y)

decision(8.85, y, 1.75, 1.0, "Target detected?", "person / vehicle")
arrow(6.95 + w / 2, y, 7.98, y)
node(11.15, 6.42, 1.9, 0.72, "Continue Monitoring", "drop routine frame", NODE_FILL, NAVY)
arrow(8.85, y + 0.5, 11.15, 6.06, "No")

node(11.15, 4.55, 1.92, 0.82, "Rule Evaluation", "fence / dwell / curfew", NODE_FILL, NAVY)
arrow(8.85, y - 0.5, 11.15, 4.96, "Yes")

decision(13.35, 4.55, 1.75, 1.0, "Security breach?", "rule match")
arrow(11.15 + 1.92 / 2, 4.55, 12.48, 4.55)
node(15.0, 5.65, 1.55, 0.68, "Normal Stream", "no alert", NODE_FILL, NAVY)
arrow(13.35, 5.05, 15.0, 5.31, "No")

# Lower alert and integrity path.
node(13.35, 2.95, 2.08, 0.82, "Alert + Evidence", "snapshot + encrypted clip", NODE_FILL, NAVY)
arrow(13.35, 4.05, 13.35, 3.36, "Yes")

node(10.65, 1.45, 1.92, 0.76, "Local Ledger", "SHA-256 hash chain", NODE_FILL, NAVY)
node(8.25, 1.45, 1.92, 0.76, "Integrity Proof", "Merkle + model hash", NODE_FILL, NAVY)
node(5.85, 1.45, 1.92, 0.76, "Approval", "2-of-3 signatures", NODE_FILL, NAVY)
node(3.45, 1.45, 1.92, 0.76, "Blockchain Anchor", "root only; no PII", NODE_FILL, NAVY)
arrow(13.35, 2.54, 10.65 + 0.96, 1.83, "persist")
arrow(9.69, 1.45, 9.21, 1.45, "hash")
arrow(7.29, 1.45, 6.81, 1.45, "approve")
arrow(4.89, 1.45, 4.41, 1.45, "anchor")

# Final operator decision and branches.
decision(1.45, 1.45, 1.55, 0.88, "Action?", "operator review")
arrow(2.49, 1.45, 2.23, 1.45, "verify")
node(1.45, 0.45, 1.72, 0.56, "Archive Event", "audit record", NODE_FILL, NAVY)
node(3.95, 0.45, 1.72, 0.56, "C2 Dispatch", "response team", NODE_FILL, NAVY)
arrow(1.45, 1.01, 1.45, 0.73, "No")
arrow(1.95, 1.45, 3.95, 0.73, "Yes")

# Integration labels and legend.
ax.text(0.62, 3.35, "REAL-TIME DETECTION PATH", fontsize=7.2,
        fontweight="bold", color=NAVY)
ax.text(0.62, 0.04, "Sensitive video, snapshots, GPS, faces, plates, and keys remain off-chain.",
        fontsize=6.4, color=MUTED)
ax.text(15.38, 0.04, "Blockchain verifies commitment integrity, not alert truth.",
        fontsize=6.4, color=MUTED, ha="right")

plt.savefig("flowchart_decision_tree_ppt.png", dpi=100, facecolor="#ffffff", edgecolor="none")
plt.savefig("flowchart_decision_tree_ppt.jpg", dpi=100, facecolor="#ffffff", edgecolor="none")
print("Generated simple 1600 x 800 IBVAP decision tree.")
