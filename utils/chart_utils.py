"""
Chart utilities for AgriSense – premium styled matplotlib charts.
Richer green palette, gradient fill under line, rounded bars, cleaner typography.
"""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image

# ── colour palette ─────────────────────────────────────────────────────────
GREEN       = "#4CAF50"
GREEN_DARK  = "#2E7D32"
GREEN_LIGHT = "#A5D6A7"
TEAL        = "#26A69A"
BG          = "#FAFAFA"
GRID        = "#EEEEEE"
GREY        = "#757575"
DARK        = "#212121"


def _style_axes(ax, title="", y_label=""):
    """Apply premium clean styling to matplotlib axes."""
    ax.set_facecolor(BG)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#E0E0E0")
    ax.spines["bottom"].set_color("#E0E0E0")
    ax.tick_params(colors=GREY, labelsize=8, length=3)
    ax.grid(axis="y", color=GRID, linewidth=0.7, linestyle="--")
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, fontsize=11, color=DARK, fontweight="bold", pad=8)
    if y_label:
        ax.set_ylabel(y_label, fontsize=9, color=GREY, labelpad=6)


def _fig_to_widget(fig):
    """Convert a matplotlib Figure → Kivy Image via PNG buffer."""
    buf = io.BytesIO()
    fig.savefig(
        buf, format="png", dpi=180,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    buf.seek(0)
    plt.close(fig)
    core_img = CoreImage(buf, ext="png")
    return Image(
        texture=core_img.texture,
        allow_stretch=True,
        keep_ratio=True,
        size_hint=(1, 1),
        pos_hint={"center_x": 0.5, "center_y": 0.5},
    )


def build_line_chart(dates, values, title="", y_label="LKR / kg"):
    """Premium line chart with gradient area fill."""
    fig, ax = plt.subplots(figsize=(5.4, 3.1), dpi=100)
    fig.patch.set_facecolor(BG)

    x = np.arange(len(dates))
    vals = np.array(values)

    # Gradient fill under the line
    ax.fill_between(x, vals, alpha=0.18, color=GREEN)
    ax.fill_between(x, vals, alpha=0.08, color=GREEN_DARK)

    # Line with markers
    ax.plot(x, vals, color=GREEN_DARK, linewidth=2.4,
            marker="o", markersize=4, markerfacecolor="white",
            markeredgecolor=GREEN_DARK, markeredgewidth=1.6, zorder=5)

    # Highlight min/max
    if len(vals) > 1:
        min_i = int(np.argmin(vals))
        max_i = int(np.argmax(vals))
        ax.scatter([x[max_i]], [vals[max_i]], color=GREEN_DARK, s=60, zorder=6)
        ax.scatter([x[min_i]], [vals[min_i]], color="#E53935", s=60, zorder=6)

    # x-axis ticks
    if len(dates) > 8:
        step = max(1, len(dates) // 6)
        ax.set_xticks(x[::step])
        ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)],
                           rotation=30, ha="right", fontsize=8)
    else:
        ax.set_xticks(x)
        ax.set_xticklabels(dates, rotation=30, ha="right", fontsize=8)

    _style_axes(ax, title=title, y_label=y_label)
    fig.tight_layout(pad=1.2)
    return _fig_to_widget(fig)


def build_bar_chart(labels, values, title="", y_label="kg"):
    """Premium bar chart with rounded tops and gradient colours."""
    fig, ax = plt.subplots(figsize=(5.4, 3.1), dpi=100)
    fig.patch.set_facecolor(BG)

    x = np.arange(len(labels))
    vals = np.array(values)

    # Colour bars by value (darker = higher)
    norm_vals = (vals - vals.min()) / ((vals.max() - vals.min()) + 1e-9)
    colours = [plt.cm.Greens(0.35 + 0.55 * v) for v in norm_vals]

    bars = ax.bar(x, vals, color=colours,
                  edgecolor=GREEN_DARK, linewidth=0.7,
                  width=0.65, zorder=3)

    # Value labels on top of each bar
    for bar, val in zip(bars, vals):
        if len(labels) <= 12:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + vals.max() * 0.01,
                f"{val:,.0f}",
                ha="center", va="bottom",
                fontsize=7, color=GREY,
            )

    if len(labels) > 8:
        step = max(1, len(labels) // 6)
        ax.set_xticks(x[::step])
        ax.set_xticklabels([labels[i] for i in range(0, len(labels), step)],
                           rotation=30, ha="right", fontsize=8)
    else:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)

    _style_axes(ax, title=title, y_label=y_label)
    fig.tight_layout(pad=1.2)
    return _fig_to_widget(fig)


def build_comparison_bar(labels, series_a, series_b,
                         label_a, label_b, title="", y_label=""):
    """Grouped bar chart: current season vs predicted."""
    fig, ax = plt.subplots(figsize=(5.4, 3.1), dpi=100)
    fig.patch.set_facecolor(BG)

    x = np.arange(len(labels))
    width = 0.35

    ax.bar(x - width / 2, series_a, width,
           label=label_a, color=GREEN_LIGHT, edgecolor=GREEN_DARK, linewidth=0.7)
    ax.bar(x + width / 2, series_b, width,
           label=label_b, color=GREEN_DARK, edgecolor=GREEN_DARK, linewidth=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
    ax.legend(fontsize=8, frameon=False, loc="upper right")

    _style_axes(ax, title=title, y_label=y_label)
    fig.tight_layout(pad=1.2)
    return _fig_to_widget(fig)
