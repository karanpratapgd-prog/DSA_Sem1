"""
Generates the visualization charts for the FIFO tie-breaking scheduler.

Run:  python visualize.py
Output (in ./charts, plus print-size copies in ./charts/report):
    1_queue_snapshots.png   queue order after each event (insert / remove / arrival)
    2_execution_timeline.png final run order, by priority lane, with arrival events
    3_fifo_vs_plain_heap.png  why the FIFO tie-break is needed
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

from scheduler import FIFOPriorityScheduler  # noqa: E402

OUT_DIR = "charts"

# Palette: one blue hue, dark = more urgent (priority is ordered, so sequential).
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
PRIO_COLOR = {1: "#0f4a94", 2: "#2a78d6", 3: "#7fb0ec", 4: "#c4dcf7"}
PRIO_TEXT = {1: "#ffffff", 2: "#ffffff", 3: "#0b0b0b", 4: "#0b0b0b"}
ACCENT = "#eb6834"   # used only to flag "moved out of arrival order"

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "text.color": INK,
    "axes.edgecolor": GRID,
    "font.family": "DejaVu Sans",
})

INITIAL = [
    ("Backup Files", 3), ("Antivirus Scan", 2), ("Disk Cleanup", 4),
    ("Email Sync", 2), ("Software Update", 3), ("Print Document", 2),
]


def replay():
    """Replay the demo scenario and record the queue after every event."""
    s = FIFOPriorityScheduler()
    snaps, run_order = [], []

    for name, p in INITIAL:
        s.insert(name, p)
    snaps.append(("1. After inserting\n6 tasks", s.snapshot(), None))

    first = s.extract_next()
    run_order.append(first)
    snaps.append((f"2. After running\n{first.name}", s.snapshot(), None))

    urgent = s.insert("Security Alert", 1)
    snaps.append(("3. High-priority\ntask arrives", s.snapshot(), urgent.name))

    late = s.insert("Cloud Upload", 2)
    snaps.append(("4. Another priority-2\ntask arrives", s.snapshot(), late.name))

    arrivals = {"Security Alert": len(run_order), "Cloud Upload": len(run_order)}
    while not s.is_empty():
        run_order.append(s.extract_next())
    return snaps, run_order, arrivals


def chart_snapshots(snaps, report=False):
    if report:   # print size: 2x2 grid, 6.5in wide, no title (caption goes in the document)
        fig, axes = plt.subplots(2, 2, figsize=(6.5, 6.7), sharey=True)
        axes = axes.flatten()
        f_title, f_name, f_sub, f_rank, f_leg = 8.5, 8.2, 6.6, 7.5, 6.6
    else:
        fig, axes = plt.subplots(1, 4, figsize=(17, 6.2), sharey=True)
        f_title, f_name, f_sub, f_rank, f_leg = 11.5, 10.5, 8.5, 10, 10
    max_rows = max(len(t) for _, t, _ in snaps)
    for ax, (title, tasks, new_name) in zip(axes, snaps):
        ax.set_xlim(0, 1)
        ax.set_ylim(max_rows + 0.4, -1.1)
        ax.axis("off")
        ax.text(0.5, -0.75, title, ha="center", va="center",
                fontsize=f_title, fontweight="bold", color=INK)
        for rank, t in enumerate(tasks):
            y = rank
            is_new = t.name == new_name
            ax.add_patch(FancyBboxPatch(
                (0.03, y - 0.38), 0.94, 0.76,
                boxstyle="round,pad=0,rounding_size=0.08",
                facecolor=PRIO_COLOR[t.priority],
                edgecolor=ACCENT if is_new else SURFACE,
                linewidth=3 if is_new else 2))
            ax.text(0.07, y, f"{rank + 1}", va="center", ha="left", fontsize=f_rank,
                    color=PRIO_TEXT[t.priority], fontweight="bold")
            ax.text(0.15, y - 0.08, t.name, va="center", ha="left", fontsize=f_name,
                    color=PRIO_TEXT[t.priority], fontweight="bold")
            ax.text(0.15, y + 0.19, f"priority {t.priority}  |  arrived #{t.arrival_seq}",
                    va="center", ha="left", fontsize=f_sub, color=PRIO_TEXT[t.priority])
    # Legend (priority -> colour) in a single row under the panels
    handles = [Rectangle((0, 0), 1, 1, color=PRIO_COLOR[p]) for p in (1, 2, 3, 4)]
    handles.append(Rectangle((0, 0), 1, 1, facecolor=SURFACE, edgecolor=ACCENT, linewidth=2.5))
    labels = ["Priority 1 (highest)", "Priority 2", "Priority 3", "Priority 4 (lowest)",
              "Just arrived"]
    fig.legend(handles, labels, loc="lower center", ncol=5, frameon=False, fontsize=f_leg,
               labelcolor=INK2, columnspacing=1.0, handlelength=1.4)
    if not report:
        fig.suptitle("Queue order after each event (rank 1 runs next)",
                     fontsize=15, fontweight="bold", y=0.98)
        fig.text(0.5, 0.925,
                 "Within the same priority, the task with the smaller arrival number is always ahead (FIFO).",
                 ha="center", fontsize=10.5, color=INK2)
    fig.tight_layout(rect=(0, 0.05, 1, 1 if report else 0.91))
    path = os.path.join(OUT_DIR, "report" if report else "", "1_queue_snapshots.png")
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path


def chart_timeline(run_order, arrivals, report=False):
    n = len(run_order)
    fig, ax = plt.subplots(figsize=(6.5, 3.5) if report else (14, 5.2))
    f_name, f_sub, f_run, f_ann, f_tick = ((7.2, 7, 7.2, 7.2, 8) if report
                                           else (8.8, 8.5, 9, 9.3, 10))
    for slot, t in enumerate(run_order):
        ax.add_patch(Rectangle((slot + 0.04, t.priority - 0.36), 0.92, 0.72,
                               facecolor=PRIO_COLOR[t.priority], edgecolor=SURFACE,
                               linewidth=2))
        label = t.name.replace(" ", "\n") if report else t.name
        ax.text(slot + 0.5, t.priority - (0.1 if report else 0.08), label, ha="center",
                va="center", fontsize=f_name, fontweight="bold",
                color=PRIO_TEXT[t.priority], linespacing=1.0)
        ax.text(slot + 0.5, t.priority + (0.25 if report else 0.17), f"#{t.arrival_seq}",
                ha="center", va="center", fontsize=f_sub, color=PRIO_TEXT[t.priority])
        ax.text(slot + 0.5, 4.75, f"run {slot + 1}", ha="center", va="center",
                fontsize=f_run, color=INK2)
    # Arrival marker (both new tasks arrived after run 1)
    boundary = arrivals["Security Alert"]
    ax.axvline(boundary, color=ACCENT, linestyle=(0, (4, 3)), linewidth=1.8)
    ax.text(boundary + 0.08, 0.28, "Security Alert (p1) and Cloud Upload (p2)\narrive here",
            color=INK, fontsize=f_ann, va="center", ha="left")
    ax.set_xlim(0, n)
    ax.set_ylim(4.95, 0.1)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(["Priority 1", "Priority 2", "Priority 3", "Priority 4"],
                       color=INK2, fontsize=f_tick)
    ax.set_xticks([])
    ax.grid(axis="y", color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    if not report:
        ax.set_title("Execution timeline: tasks run left to right, grouped by priority lane",
                     fontsize=14, fontweight="bold", loc="left", pad=14)
        fig.text(0.01, 0.01, "Number inside each block = arrival number (#). "
                 "Equal-priority tasks run in arrival order.", fontsize=9.5, color=INK2)
    fig.tight_layout(rect=(0, 0.0 if report else 0.04, 1, 1))
    path = os.path.join(OUT_DIR, "report" if report else "", "2_execution_timeline.png")
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path


def run_equal(use_fifo):
    s = FIFOPriorityScheduler(use_fifo=use_fifo)
    for c in "ABCDEFG":
        s.insert(f"Task {c}", 2)
    out = []
    while not s.is_empty():
        out.append(s.extract_next().name[-1])
    return out


def chart_fifo_vs_plain(report=False):
    arrival = list("ABCDEFG")
    rows = [
        ("Arrival order", arrival),
        ("Heap WITHOUT FIFO key", run_equal(False)),
        ("Heap WITH FIFO key", run_equal(True)),
    ]
    fig, ax = plt.subplots(figsize=(6.5, 2.7) if report else (12, 4.6))
    f_row, f_let, f_note = (7.8, 11, 6.8) if report else (11, 15, 10)
    ax.set_xlim(-3.4, 7.2)
    ax.set_ylim(3.35, -0.55)
    ax.axis("off")
    for r, (label, order) in enumerate(rows):
        ax.text(-3.3, r + 0.5, label, ha="left", va="center", fontsize=f_row,
                fontweight="bold", color=INK)
        for i, ch in enumerate(order):
            moved = ch != arrival[i]
            ax.add_patch(FancyBboxPatch(
                (i + 0.06, r + 0.1), 0.88, 0.8,
                boxstyle="round,pad=0,rounding_size=0.1",
                facecolor=PRIO_COLOR[2],
                edgecolor=ACCENT if moved else SURFACE,
                linewidth=3.2 if moved else 2))
            ax.text(i + 0.5, r + 0.5, ch, ha="center", va="center", fontsize=f_let,
                    fontweight="bold", color=PRIO_TEXT[2])
    ax.text(3.5, 3.15,
            "All seven tasks have priority 2. Orange outline = task is not in its arrival position.",
            ha="center", va="center", fontsize=f_note, color=INK2)
    if not report:
        ax.set_title("Why FIFO tie-breaking is needed",
                     fontsize=14, fontweight="bold", loc="left", pad=8, x=0.0)
    fig.tight_layout()
    path = os.path.join(OUT_DIR, "report" if report else "", "3_fifo_vs_plain_heap.png")
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path


def main():
    os.makedirs(os.path.join(OUT_DIR, "report"), exist_ok=True)
    snaps, run_order, arrivals = replay()
    for report in (False, True):           # False = slides size, True = print size
        for p in (chart_snapshots(snaps, report), chart_timeline(run_order, arrivals, report),
                  chart_fifo_vs_plain(report)):
            print("saved", p)


if __name__ == "__main__":
    main()
