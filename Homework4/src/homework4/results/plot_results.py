#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIGURES_DIR = os.path.join(RESULTS_DIR, "../../../report/figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────────
rect_df = pd.read_csv(os.path.join(RESULTS_DIR, "homework4_rect_results.csv"))
line_df = pd.read_csv(os.path.join(RESULTS_DIR, "homework4_line_results.csv"))
tp_df   = pd.read_csv(os.path.join(RESULTS_DIR, "homework4_tp_results.csv"))
rect_df["map_name"] = "rect_map"

df = pd.concat([rect_df, line_df, tp_df], ignore_index=True)

SPEEDS = [0.5, 1.0, 2.0]
# map_name values as they appear in the CSVs
MAPS = ["rect_map", "line_map", "x_map"]
MAP_LABELS = {"rect_map": "Rect Map", "line_map": "Line Map", "x_map": "TP Map"}
COLORS = {"basic": "#4878CF", "improved": "#D65F5F"}
WINDOW_COLORS = {4: "#6ACC65", 2: "#D65F5F"}
MAP_COLORS = {"rect_map": "#4878CF", "line_map": "#D65F5F", "x_map": "#6ACC65"}

x = np.arange(len(SPEEDS))
width = 0.35


# ── Plot 1: mean total_time by speed and nav_mode (one subplot per map) ────────
fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)

for ax, map_name in zip(axes, MAPS):
    for i, nav in enumerate(["basic", "improved"]):
        means = [
            df[(df["map_name"] == map_name) & (df["nav_mode"] == nav) &
               (df["linear_speed"] == s)]["total_time"].mean()
            for s in SPEEDS
        ]
        offset = (i - 0.5) * width
        bars = ax.bar(x + offset, means, width, label=nav.capitalize(),
                      color=COLORS[nav], alpha=0.85)
        ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=8)

    ax.set_title(MAP_LABELS[map_name])
    ax.set_xticks(x)
    ax.set_xticklabels([f"{s} m/s" for s in SPEEDS])
    ax.set_xlabel("Linear speed")
    ax.set_ylabel("Mean total time (s)")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.5)

fig.suptitle("Mean completion time: basic vs improved navigation")
fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "plot_nav_mode_vs_speed.png"), dpi=150)
plt.close(fig)
print("Saved plot_nav_mode_vs_speed.png")


# ── Plot 2: mean total_time by speed and mean_window ──────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)

for ax, map_name in zip(axes, MAPS):
    for i, window in enumerate([4, 2]):
        means = [
            df[(df["map_name"] == map_name) & (df["mean_window"] == window) &
               (df["linear_speed"] == s)]["total_time"].mean()
            for s in SPEEDS
        ]
        offset = (i - 0.5) * width
        bars = ax.bar(x + offset, means, width, label=f"window={window}",
                      color=WINDOW_COLORS[window], alpha=0.85)
        ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=8)

    ax.set_title(MAP_LABELS[map_name])
    ax.set_xticks(x)
    ax.set_xticklabels([f"{s} m/s" for s in SPEEDS])
    ax.set_xlabel("Linear speed")
    ax.set_ylabel("Mean total time (s)")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.5)

fig.suptitle("Mean completion time: laser window size effect")
fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "plot_window_vs_speed.png"), dpi=150)
plt.close(fig)
print("Saved plot_window_vs_speed.png")


# ── Plot 3: box plot of total_time by speed ────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)

for ax, map_name in zip(axes, MAPS):
    data_by_speed = [
        df[(df["map_name"] == map_name) &
           (df["linear_speed"] == s)]["total_time"].values
        for s in SPEEDS
    ]
    bp = ax.boxplot(data_by_speed, patch_artist=True, widths=0.5,
                    medianprops=dict(color="black", linewidth=2))
    for patch, color in zip(bp["boxes"], ["#4878CF", "#6ACC65", "#D65F5F"]):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)

    ax.set_title(MAP_LABELS[map_name])
    ax.set_xticks(range(1, len(SPEEDS) + 1))
    ax.set_xticklabels([f"{s} m/s" for s in SPEEDS])
    ax.set_xlabel("Linear speed")
    ax.set_ylabel("Total time (s)")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

fig.suptitle("Completion time distribution by speed")
fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "plot_boxplot_speed.png"), dpi=150)
plt.close(fig)
print("Saved plot_boxplot_speed.png")


# ── Plot 4: map comparison by speed ───────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 4))

n_maps = len(MAPS)
width_multi = 0.25
offsets = np.linspace(-(n_maps - 1) / 2, (n_maps - 1) / 2, n_maps) * width_multi

for offset, map_name in zip(offsets, MAPS):
    means = [
        df[(df["map_name"] == map_name) &
           (df["linear_speed"] == s)]["total_time"].mean()
        for s in SPEEDS
    ]
    bars = ax.bar(x + offset, means, width_multi,
                  label=MAP_LABELS[map_name],
                  color=MAP_COLORS[map_name], alpha=0.85)
    ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=8)

ax.set_xticks(x)
ax.set_xticklabels([f"{s} m/s" for s in SPEEDS])
ax.set_xlabel("Linear speed")
ax.set_ylabel("Mean total time (s)")
ax.set_title("Mean completion time: map comparison")
ax.legend()
ax.grid(axis="y", linestyle="--", alpha=0.5)

fig.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "plot_map_comparison.png"), dpi=150)
plt.close(fig)
print("Saved plot_map_comparison.png")


# ── LaTeX summary table ────────────────────────────────────────────────────────
summary = (
    df.groupby(["map_name", "nav_mode", "linear_speed", "mean_window"])["total_time"]
    .mean()
    .round(2)
    .reset_index()
)

table_path = os.path.join(FIGURES_DIR, "results_table.tex")
with open(table_path, "w") as f:
    for map_name in MAPS:
        label = MAP_LABELS[map_name]
        f.write("\\begin{table}[h]\n")
        f.write("    \\centering\n")
        f.write("    \\begin{tabular}{llcc}\n")
        f.write("        \\hline\n")
        f.write("        \\textbf{Nav mode} & \\textbf{Speed (m/s)} & "
                "\\textbf{Window} & \\textbf{Mean time (s)} \\\\\n")
        f.write("        \\hline\n")

        subset = summary[summary["map_name"] == map_name].sort_values(
            ["nav_mode", "linear_speed", "mean_window"]
        )
        prev_nav = None
        for _, row in subset.iterrows():
            nav = row["nav_mode"].capitalize()
            nav_cell = nav if nav != prev_nav else ""
            prev_nav = nav
            f.write(f"        {nav_cell} & {row['linear_speed']:.1f} & "
                    f"{int(row['mean_window'])} & {row['total_time']:.2f} \\\\\n")

        f.write("        \\hline\n")
        f.write("    \\end{tabular}\n")
        f.write(f"    \\caption{{Mean completion time per configuration --- {label}.}}\n")
        f.write(f"    \\label{{tab:{map_name}}}\n")
        f.write("\\end{table}\n\n")

print(f"Saved results_table.tex")
