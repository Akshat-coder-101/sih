"""Render a polished IBVAP HLD/LLD architecture diagram at 1600x800."""

import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch


FIG_W, FIG_H = 16, 8
fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
fig.patch.set_facecolor("#f6f8fb")
ax.set_facecolor("#f6f8fb")

NAVY = "#12304a"
TEXT = "#1f3445"
MUTED = "#607487"
LINE = "#91a4b5"
BLUE = "#dcecf8"
BLUE_EDGE = "#3679a8"
TEAL = "#dcf4ef"
TEAL_EDGE = "#238477"
PURPLE = "#eee7fa"
PURPLE_EDGE = "#7650a8"
AMBER = "#fff1cf"
AMBER_EDGE = "#a87500"
RED = "#fde6e3"
RED_EDGE = "#bd3b32"
WHITE = "#ffffff"


def rounded_box(x, y, w, h, title, subtitle="", fill=WHITE, edge=LINE, title_size=7.2):
    patch = patches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.035,rounding_size=0.07",
        linewidth=1.0, facecolor=fill, edgecolor=edge, zorder=3,
    )
    ax.add_patch(patch)
    ax.text(x + 0.13, y + h - 0.22, title, fontsize=title_size,
            fontweight="bold", color=TEXT, va="top", zorder=4)
    if subtitle:
        ax.text(x + 0.13, y + 0.17, subtitle, fontsize=5.45,
                color=MUTED, va="bottom", zorder=4)


def store(x, y, w, h, title, subtitle="", fill=WHITE, edge=LINE):
    rounded_box(x, y, w, h, title, subtitle, fill, edge)
    ax.add_patch(patches.Ellipse((x + w / 2, y + h - 0.07), w - 0.08, 0.16,
                                 facecolor=fill, edgecolor=edge, linewidth=0.8, zorder=4))


def connector(x1, y1, x2, y2, label="", color=LINE, dashed=False):
    style = "-|>"
    patch = FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle=style, mutation_scale=9,
        linewidth=1.0, color=color, linestyle="--" if dashed else "-",
        connectionstyle="arc3,rad=0", zorder=2,
    )
    ax.add_patch(patch)
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.11, label,
                fontsize=5.1, color=color, ha="center", va="center",
                bbox=dict(facecolor="#f6f8fb", edgecolor="none", pad=0.8), zorder=5)


def boundary(x, y, w, h, label, color):
    ax.add_patch(patches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.1",
        facecolor="none", edgecolor=color, linewidth=1.0,
        linestyle=(0, (4, 3)), zorder=1,
    ))
    ax.text(x + 0.12, y + h - 0.12, label, fontsize=5.8,
            fontweight="bold", color=color, va="top", zorder=2)


# Header
ax.text(0.48, 7.60, "IBVAP | HIGH-LEVEL + LOW-LEVEL SYSTEM ARCHITECTURE",
        fontsize=14, fontweight="bold", color=NAVY, va="center")
ax.text(15.52, 7.60, "1600 × 800 px  |  v1.0 Prototype", fontsize=6.8,
        color=MUTED, ha="right", va="center")
ax.plot([0.48, 15.52], [7.37, 7.37], color="#cad5df", linewidth=0.8)

# HLD title and boundaries.
ax.text(0.55, 7.10, "HLD  /  PLATFORM VIEW", fontsize=7.2,
        fontweight="bold", color=BLUE_EDGE)
boundary(0.48, 4.55, 15.04, 2.36, "EDGE + PLATFORM TRUST BOUNDARY", BLUE_EDGE)

# HLD components.
hy = 5.43
rounded_box(0.78, hy, 1.55, 0.86, "CCTV / RTSP", "IP cameras · sample files", BLUE, BLUE_EDGE)
rounded_box(2.65, hy, 1.55, 0.86, "Edge Gateway", "TLS · OpenCV · workers", BLUE, BLUE_EDGE)
rounded_box(4.52, hy, 1.55, 0.86, "AI Services", "YOLO · ByteTrack", TEAL, TEAL_EDGE)
rounded_box(6.39, hy, 1.55, 0.86, "Rule Engine", "fence · dwell · ANPR", TEAL, TEAL_EDGE)
rounded_box(8.26, hy, 1.55, 0.86, "Alert Service", "WebSocket · RBAC", AMBER, AMBER_EDGE)
store(10.13, hy, 1.55, 0.86, "PostgreSQL", "alerts · audit · configs", WHITE, BLUE_EDGE)
rounded_box(12.00, hy, 1.55, 0.86, "React Console", "monitor · triage · proof", PURPLE, PURPLE_EDGE)
rounded_box(13.87, hy, 1.20, 0.86, "C2 / Ops", "response", RED, RED_EDGE)
for left, right in [(2.33, 2.65), (4.20, 4.52), (6.07, 6.39), (7.94, 8.26), (9.81, 10.13), (11.68, 12.00), (13.55, 13.87)]:
    connector(left, hy + 0.43, right, hy + 0.43, color=LINE)

# LLD title and boundaries.
ax.text(0.55, 4.26, "LLD  /  ALERT INTEGRITY + BLOCKCHAIN ANCHOR PATH", fontsize=7.2,
        fontweight="bold", color=PURPLE_EDGE)
boundary(0.48, 0.67, 15.04, 3.32, "CRYPTOGRAPHIC INTEGRITY BOUNDARY", PURPLE_EDGE)
boundary(0.73, 1.07, 8.47, 2.47, "PRIVATE / OFF-CHAIN", TEAL_EDGE)
boundary(9.48, 1.07, 5.79, 2.47, "EXTERNAL TRUST / ON-CHAIN COMMITMENT", PURPLE_EDGE)

# LLD nodes.
ly = 2.68
rounded_box(0.95, ly, 1.45, 0.72, "Alert Event", "camera_id · ts · type", WHITE, BLUE_EDGE)
rounded_box(2.72, ly, 1.45, 0.72, "Canonicalizer", "stable JSON payload", BLUE, BLUE_EDGE)
rounded_box(4.49, ly, 1.45, 0.72, "SHA-256 Chain", "prev_hash → record_hash", TEAL, TEAL_EDGE)
rounded_box(6.26, ly, 1.45, 0.72, "Merkle Builder", "leaf → root + proof", TEAL, TEAL_EDGE)
rounded_box(8.03, ly, 1.45, 0.72, "Provenance", "model + rule hashes", AMBER, AMBER_EDGE)
for left, right in [(2.40, 2.72), (4.17, 4.49), (5.94, 6.26), (7.71, 8.03)]:
    connector(left, ly + 0.36, right, ly + 0.36, color=LINE)

rounded_box(9.82, ly, 1.45, 0.72, "Proposal", "root + range + nonce", PURPLE, PURPLE_EDGE)
rounded_box(11.59, ly, 1.45, 0.72, "2-of-3 Signatures", "Admin · Supervisor", PURPLE, PURPLE_EDGE)
rounded_box(13.36, ly, 1.45, 0.72, "Anchor Contract", "root only · no PII", PURPLE, PURPLE_EDGE)
for left, right in [(9.48, 9.82), (11.27, 11.59), (13.04, 13.36)]:
    connector(left, ly + 0.36, right, ly + 0.36, color=PURPLE_EDGE)

# Data stores and verification paths.
store(1.08, 1.30, 1.75, 0.66, "Encrypted Evidence", "AES-256-GCM", WHITE, TEAL_EDGE)
store(3.35, 1.30, 1.75, 0.66, "Ledger Records", "append-only DB rows", WHITE, BLUE_EDGE)
store(5.62, 1.30, 1.75, 0.66, "Proof Cache", "Merkle proofs", WHITE, TEAL_EDGE)
store(7.89, 1.30, 1.75, 0.66, "Model Registry", "artifact hashes", WHITE, AMBER_EDGE)
store(10.16, 1.30, 1.75, 0.66, "Anchor Registry", "tx hash · status", WHITE, PURPLE_EDGE)
store(12.43, 1.30, 1.75, 0.66, "Public Explorer", "independent proof", WHITE, PURPLE_EDGE)

connector(1.68, ly, 1.68, 1.96, "snapshot", color=TEAL_EDGE)
connector(4.05, ly, 4.05, 1.96, "persist", color=BLUE_EDGE)
connector(6.32, ly, 6.32, 1.96, "cache", color=TEAL_EDGE)
connector(8.73, ly, 8.73, 1.96, "lookup", color=AMBER_EDGE)
connector(10.54, ly, 10.54, 1.96, "status", color=PURPLE_EDGE)
connector(13.30, ly, 13.30, 1.96, "verify", color=PURPLE_EDGE, dashed=True)

# Cross-layer mapping: alert service feeds integrity path.
connector(9.03, 5.43, 1.68, 3.40, "event payload", color=AMBER_EDGE)
connector(10.90, 5.43, 4.05, 3.40, "ledger write", color=BLUE_EDGE)
connector(12.78, 5.43, 10.54, 3.40, "proof / status", color=PURPLE_EDGE, dashed=True)

# Footer legend.
ax.text(0.58, 0.30, "Solid = synchronous data path   Dashed = verification / trust path",
        fontsize=5.8, color=MUTED)
ax.text(15.42, 0.30, "Sensitive evidence stays off-chain; only commitments are anchored.",
        fontsize=5.8, color=PURPLE_EDGE, ha="right")

plt.savefig("flowchart_decision_tree_ppt.png", dpi=100, facecolor="#f6f8fb", edgecolor="none")
plt.savefig("flowchart_decision_tree_ppt.jpg", dpi=100, facecolor="#f6f8fb", edgecolor="none")
print("Generated polished 1600 x 800 IBVAP HLD/LLD architecture.")
