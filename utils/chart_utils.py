"""
Chart helpers — build small matplotlib figures styled to match the
white / light-green AgriSense theme, wrapped for use inside KivyMD screens.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

GREEN = "#66BB6A"
GREEN_DARK = "#4C9950"
GREY = "#6B6B6B"


def _style_axes(ax):
    ax.set_facecolor("#FFFFFF")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#E0E0E0")
    ax.spines["bottom"].set_color("#E0E0E0")
    ax.tick_params(colors=GREY, labelsize=8)
    ax.grid(axis="y", color="#EEEEEE", linewidth=0.8)


def build_line_chart(dates, values, title="", y_label="LKR / kg"):
    """dates: list of date/str labels, values: list of numbers."""
    fig, ax = plt.subplots(figsize=(5.2, 3), dpi=100)
    fig.patch.set_facecolor("#FFFFFF")
    ax.plot(dates, values, color=GREEN_DARK, linewidth=2.2, marker="o", markersize=3)
    ax.fill_between(range(len(dates)), values, color=GREEN, alpha=0.15)
    ax.set_title(title, fontsize=11, color="#1B1B1B", fontweight="bold")
    ax.set_ylabel(y_label, fontsize=9, color=GREY)
    if len(dates) > 8:
        step = max(1, len(dates) // 6)
        ax.set_xticks(range(0, len(dates), step))
        ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)], rotation=30, ha="right")
    _style_axes(ax)
    fig.tight_layout()
    return FigureCanvasKivyAgg(fig)


def build_bar_chart(labels, values, title="", y_label="kg"):
    fig, ax = plt.subplots(figsize=(5.2, 3), dpi=100)
    fig.patch.set_facecolor("#FFFFFF")
    ax.bar(labels, values, color=GREEN, edgecolor=GREEN_DARK, linewidth=1)
    ax.set_title(title, fontsize=11, color="#1B1B1B", fontweight="bold")
    ax.set_ylabel(y_label, fontsize=9, color=GREY)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    _style_axes(ax)
    fig.tight_layout()
    return FigureCanvasKivyAgg(fig)


def build_comparison_bar(labels, series_a, series_b, label_a, label_b, title="", y_label=""):
    """Grouped bar chart, e.g. current season vs predicted."""
    import numpy as np
    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(5.2, 3), dpi=100)
    fig.patch.set_facecolor("#FFFFFF")
    ax.bar(x - width / 2, series_a, width, label=label_a, color="#A5D6A7", edgecolor=GREEN_DARK)
    ax.bar(x + width / 2, series_b, width, label=label_b, color=GREEN_DARK)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_title(title, fontsize=11, color="#1B1B1B", fontweight="bold")
    ax.set_ylabel(y_label, fontsize=9, color=GREY)
    ax.legend(fontsize=8, frameon=False)
    _style_axes(ax)
    fig.tight_layout()
    return FigureCanvasKivyAgg(fig)
