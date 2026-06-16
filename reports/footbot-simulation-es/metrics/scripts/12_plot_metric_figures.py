#!/usr/bin/env python3
"""Generate report-ready figures for the FootBot Reach Goal simulation report.

Reads the CSV files produced by the metric builders (scripts 02-11) and renders
publication-quality figures (PNG @300 DPI + vector PDF) for inclusion in
``reports/footbot-simulation-es/main.tex``.

This script never runs the simulation and never modifies the source CSVs/bags.
It is best-effort: if one CSV is missing (e.g. ``01_loop_latency`` was not
recorded), the corresponding figure is skipped with a warning and the rest are
still produced.

Usage::

    python3 12_plot_metric_figures.py [--csv-dir DIR] [--output-dir DIR]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless, no GUI required
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CSV_DIR = (
    REPO_ROOT
    / "reports/footbot-simulation-es/metrics/csv/reach_goal_trials_20260616_154906"
)
DEFAULT_OUT_DIR = REPO_ROOT / "reports/footbot-simulation-es/figures/metrics"

# --------------------------------------------------------------------------- #
# Style
# --------------------------------------------------------------------------- #
UNET_BLUE = "#0B3D66"
ACCENT = "#1B98A0"
NEUTRAL = "#8C8C8C"

# Vertical top-down soccer-field palette (robot vs ball must contrast clearly).
FIELD_GREEN = "#3f9b46"
FIELD_LINE = "white"
ROBOT_COLOR = UNET_BLUE
BALL_COLOR = "#E8743B"
GOAL_GW = 0.30  # goal-mouth width (m) drawn at the top of the field

# One consistent colour per FSM state, shared by the state-time and timeline
# figures. Order also drives stacking / legend order.
STATE_COLORS = {
    "SEARCH_BALL": "#4C72B0",
    "APPROACH_BALL": "#DD8452",
    "CONTROL_BALL": "#55A868",
    "ALIGN_BALL_TO_GOAL": "#8172B3",
    "SEARCH_GOAL": "#64B5CD",
    "DRIBBLE_TO_GOAL": "#CCB974",
    "RECOVER_BALL": "#C44E52",
    "STOP_SAFE": "#9C9C9C",
    "GOAL_SCORED": "#DA9100",
}
STATE_ORDER = list(STATE_COLORS)

# Soccer field extents (metres); attacking goal is at the far +x end.
FIELD = dict(x_min=-0.1, x_max=1.7, y_min=-0.2, y_max=0.2)
GOAL_BAND = (1.6, FIELD["x_max"])  # indicative goal mouth (x range)

plt.rcParams.update(
    {
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.alpha": 0.3,
        "grid.linewidth": 0.6,
        "axes.edgecolor": "#333333",
        "axes.linewidth": 0.8,
        "legend.fontsize": 9,
        "legend.framealpha": 0.9,
    }
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def state_color(state: str) -> str:
    return STATE_COLORS.get(state, NEUTRAL)


def ep_label(episode: str) -> str:
    """'episode_001' -> 'Ep. 1'."""
    try:
        return f"Ep. {int(str(episode).split('_')[-1])}"
    except (ValueError, IndexError):
        return str(episode)


def sorted_episodes(values) -> list[str]:
    return sorted(set(values), key=lambda e: str(e))


def save(fig: plt.Figure, out_dir: Path, name: str) -> None:
    """Save a figure as both PNG (300 DPI) and vector PDF."""
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"{name}.{ext}")
    plt.close(fig)
    print(f"  [OK] {name}.png / {name}.pdf")


def draw_goal_band(ax, *, vertical: bool = True) -> None:
    """Shade the indicative goal mouth at the far +x end of the field."""
    if vertical:
        ax.axvspan(*GOAL_BAND, color=UNET_BLUE, alpha=0.10, zorder=0)
        ax.axvline(FIELD["x_max"], color=UNET_BLUE, lw=1.4, ls="--", alpha=0.7, zorder=1)


# --------------------------------------------------------------------------- #
# 1. Goal success rate
# --------------------------------------------------------------------------- #
def plot_goal_success_rate(csv_dir: Path, out_dir: Path) -> None:
    df = pd.read_csv(csv_dir / "05_goal_success_rate.csv")
    eps = df[df["row_type"] == "episode"].copy()
    eps["scored"] = eps["scored"].astype(str).str.lower().isin(["true", "1"])
    eps = eps.sort_values("episode")

    n_total = len(eps)
    n_ok = int(eps["scored"].sum())
    rate = 100.0 * n_ok / n_total if n_total else 0.0

    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = np.arange(n_total)
    colors = [ACCENT if s else NEUTRAL for s in eps["scored"]]
    ax.bar(x, eps["scored"].astype(int), color=colors, edgecolor="#333333", width=0.6)
    ax.axhline(n_ok / n_total, color=UNET_BLUE, ls="--", lw=1.6,
               label=f"Tasa de éxito = {rate:.0f}%")

    ax.set_xticks(x)
    ax.set_xticklabels([ep_label(e) for e in eps["episode"]])
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["No gol", "Gol"])
    ax.set_ylim(0, 1.25)
    ax.set_ylabel("Resultado del episodio")
    ax.set_title("Tasa de éxito de gol — comportamiento Llegar a la portería")
    ax.grid(axis="x", visible=False)
    ax.text(0.98, 0.92, f"{n_ok} / {n_total} episodios marcaron gol",
            transform=ax.transAxes, ha="right", va="top",
            bbox=dict(boxstyle="round", fc="white", ec=UNET_BLUE, alpha=0.9))
    ax.legend(loc="upper left")
    save(fig, out_dir, "goal_success_rate")


# --------------------------------------------------------------------------- #
# 2. Time to first ball control
# --------------------------------------------------------------------------- #
def plot_time_to_ball_control(csv_dir: Path, out_dir: Path) -> None:
    df = pd.read_csv(csv_dir / "03_time_to_ball_control_trials.csv").sort_values("episode")
    df = df.dropna(subset=["dt_s"])
    x = np.arange(len(df))
    vals = df["dt_s"].to_numpy()
    mean = vals.mean()

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(x, vals, color=ACCENT, edgecolor="#333333", width=0.6)
    ax.axhline(mean, color=UNET_BLUE, ls="--", lw=1.6, label=f"Media = {mean:.1f} s")
    for xi, v in zip(x, vals):
        ax.text(xi, v + 0.15, f"{v:.1f}", ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels([ep_label(e) for e in df["episode"]])
    ax.set_ylabel("Tiempo hasta el primer control (s)")
    ax.set_ylim(0, max(vals) * 1.18)
    ax.set_title("Tiempo hasta el primer control del balón")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right")
    save(fig, out_dir, "time_to_ball_control")


# --------------------------------------------------------------------------- #
# 3. Time to goal
# --------------------------------------------------------------------------- #
def plot_time_to_goal(csv_dir: Path, out_dir: Path) -> None:
    goal = pd.read_csv(csv_dir / "04_time_to_goal_trials.csv")
    succ = pd.read_csv(csv_dir / "05_goal_success_rate.csv")
    succ = succ[succ["row_type"] == "episode"][["episode", "duration_s"]]
    df = goal.merge(succ, on="episode", how="left").sort_values("episode")

    x = np.arange(len(df))
    fig, ax = plt.subplots(figsize=(8, 4.4))
    for xi, row in zip(x, df.itertuples()):
        scored = pd.notna(row.dt_s)
        if scored:
            ax.bar(xi, row.dt_s, color=ACCENT, edgecolor="#333333", width=0.6)
            ax.text(xi, row.dt_s + 3, f"{row.dt_s:.0f} s ✓",
                    ha="center", va="bottom", fontsize=9, color=UNET_BLUE)
        else:
            dur = row.duration_s if pd.notna(row.duration_s) else 0.0
            ax.bar(xi, dur, color="#E0E0E0", edgecolor=NEUTRAL, width=0.6, hatch="//")
            ax.text(xi, dur + 3, "sin gol", ha="center", va="bottom",
                    fontsize=9, color=NEUTRAL)

    ax.set_xticks(x)
    ax.set_xticklabels([ep_label(e) for e in df["episode"]])
    ax.set_ylabel("Tiempo (s)")
    ax.set_title("Tiempo hasta marcar gol por episodio")
    ax.grid(axis="x", visible=False)
    legend = [
        Patch(facecolor=ACCENT, edgecolor="#333333", label="Tiempo hasta el gol"),
        Patch(facecolor="#E0E0E0", edgecolor=NEUTRAL, hatch="//",
              label="Episodio sin gol (duración total del episodio)"),
    ]
    ax.legend(handles=legend, loc="upper left")
    ymax = max(df["duration_s"].max(), df["dt_s"].max())
    ax.set_ylim(0, ymax * 1.18)
    save(fig, out_dir, "time_to_goal")


# --------------------------------------------------------------------------- #
# 4. Time spent per FSM state (stacked)
# --------------------------------------------------------------------------- #
def plot_fsm_state_time(csv_dir: Path, out_dir: Path) -> None:
    df = pd.read_csv(csv_dir / "06_fsm_state_time_trials.csv")
    pivot = df.pivot_table(index="episode", columns="state",
                           values="total_time_s", aggfunc="sum").fillna(0.0)
    episodes = sorted_episodes(pivot.index)
    pivot = pivot.loc[episodes]
    cols = [s for s in STATE_ORDER if s in pivot.columns]
    cols += [s for s in pivot.columns if s not in cols]

    x = np.arange(len(episodes))
    bottom = np.zeros(len(episodes))
    fig, ax = plt.subplots(figsize=(9, 5))
    for state in cols:
        vals = pivot[state].to_numpy()
        ax.bar(x, vals, bottom=bottom, color=state_color(state),
               edgecolor="white", lw=0.4, label=state)
        bottom += vals

    ax.set_xticks(x)
    ax.set_xticklabels([ep_label(e) for e in episodes])
    ax.set_ylabel("Tiempo en el estado (s)")
    ax.set_title("Distribución del tiempo por estado de la FSM (Reach Goal)")
    ax.grid(axis="x", visible=False)
    ax.legend(title="Estado FSM", bbox_to_anchor=(1.02, 1), loc="upper left",
              borderaxespad=0)
    fig.subplots_adjust(right=0.74)
    save(fig, out_dir, "fsm_state_time")


# --------------------------------------------------------------------------- #
# 5. FSM timeline (state over time, one lane per episode)
# --------------------------------------------------------------------------- #
def _state_spans(times: np.ndarray, states: np.ndarray):
    """Run-length encode a state sequence into {state: [(start, width), ...]}."""
    spans: dict[str, list[tuple[float, float]]] = {}
    t0 = times[0]
    cur, start = states[0], times[0]
    for i in range(1, len(states)):
        if states[i] != cur:
            spans.setdefault(cur, []).append((start - t0, times[i] - start))
            cur, start = states[i], times[i]
    spans.setdefault(cur, []).append((start - t0, max(times[-1] - start, 0.05)))
    return spans


def plot_fsm_timeline(csv_dir: Path, out_dir: Path) -> None:
    df = pd.read_csv(csv_dir / "06_fsm_state_timeline_trials.csv")
    episodes = sorted_episodes(df["episode"])
    present_states: set[str] = set()

    fig, ax = plt.subplots(figsize=(11, 4.8))
    lane_h = 0.8
    for lane, ep in enumerate(episodes):
        sub = df[df["episode"] == ep].sort_values("t_s")
        spans = _state_spans(sub["t_s"].to_numpy(), sub["state"].to_numpy())
        for state, segs in spans.items():
            present_states.add(state)
            ax.broken_barh(segs, (lane - lane_h / 2, lane_h),
                           facecolors=state_color(state))

    ax.set_yticks(range(len(episodes)))
    ax.set_yticklabels([ep_label(e) for e in episodes])
    ax.set_ylim(-0.6, len(episodes) - 0.4)
    ax.invert_yaxis()
    ax.set_xlabel("Tiempo desde el inicio del episodio (s)")
    ax.set_title("Línea de tiempo de estados de la FSM por episodio")
    ax.grid(axis="y", visible=False)

    legend = [Patch(facecolor=state_color(s), label=s)
              for s in STATE_ORDER if s in present_states]
    ax.legend(handles=legend, title="Estado FSM", bbox_to_anchor=(1.01, 1),
              loc="upper left", borderaxespad=0)
    fig.subplots_adjust(right=0.78)
    save(fig, out_dir, "fsm_timeline")


# --------------------------------------------------------------------------- #
# 6. FSM event counts (RECOVER_BALL / COMMIT_TO_GOAL)
# --------------------------------------------------------------------------- #
def plot_fsm_event_counts(csv_dir: Path, out_dir: Path) -> None:
    df = pd.read_csv(csv_dir / "07_fsm_event_counts_trials.csv")
    pivot = df.pivot_table(index="episode", columns="event",
                           values="count", aggfunc="sum").fillna(0)
    episodes = sorted_episodes(pivot.index)
    pivot = pivot.loc[episodes]
    events = [e for e in ("RECOVER_BALL", "COMMIT_TO_GOAL") if e in pivot.columns]
    events += [e for e in pivot.columns if e not in events]

    x = np.arange(len(episodes))
    width = 0.8 / max(len(events), 1)
    palette = {"RECOVER_BALL": "#C44E52", "COMMIT_TO_GOAL": "#DA9100"}

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    for i, ev in enumerate(events):
        vals = pivot[ev].to_numpy()
        offset = (i - (len(events) - 1) / 2) * width
        bars = ax.bar(x + offset, vals, width, label=ev,
                      color=palette.get(ev, NEUTRAL), edgecolor="#333333")
        ax.bar_label(bars, fmt="%d", padding=2, fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels([ep_label(e) for e in episodes])
    ax.set_ylabel("Número de activaciones")
    ax.set_title("Activaciones de eventos de la FSM por episodio")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right")
    if "COMMIT_TO_GOAL" in pivot.columns and pivot["COMMIT_TO_GOAL"].sum() == 0:
        ax.text(0.02, 0.92, "COMMIT_TO_GOAL = 0 en todos los episodios",
                transform=ax.transAxes, fontsize=9, color=NEUTRAL,
                bbox=dict(boxstyle="round", fc="white", ec=NEUTRAL, alpha=0.9))
    ax.set_ylim(0, pivot.to_numpy().max() * 1.18)
    save(fig, out_dir, "fsm_event_counts")


# --------------------------------------------------------------------------- #
# 7. Topic frequency (mean Hz across episodes)
# --------------------------------------------------------------------------- #
def plot_topic_frequency(csv_dir: Path, out_dir: Path) -> None:
    df = pd.read_csv(csv_dir / "02_topic_hz_trials.csv")
    agg = (df.groupby("topic")["mean_hz"]
             .agg(["mean", "std", "count"])
             .sort_values("mean"))
    y = np.arange(len(agg))
    err = agg["std"].fillna(0.0).to_numpy()

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.barh(y, agg["mean"], xerr=err, color=UNET_BLUE, edgecolor="#333333",
            error_kw=dict(ecolor=NEUTRAL, capsize=3, lw=1))
    for yi, v in zip(y, agg["mean"]):
        ax.text(v + 0.6, yi, f"{v:.1f} Hz", va="center", fontsize=9)

    ax.set_yticks(y)
    ax.set_yticklabels(agg.index)
    ax.set_xlabel("Frecuencia media (Hz)")
    ax.set_title(f"Frecuencia de publicación por topic "
                 f"(media de {int(agg['count'].max())} episodios)")
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, agg["mean"].max() * 1.2)
    save(fig, out_dir, "topic_frequency")


# --------------------------------------------------------------------------- #
# 8. Trajectories (small multiples, one panel per episode)
# --------------------------------------------------------------------------- #
def plot_trajectory_xy(csv_dir: Path, out_dir: Path) -> None:
    files = sorted(csv_dir.glob("09_trajectory_xy_episode_*.csv"))
    if not files:
        raise FileNotFoundError("no 09_trajectory_xy_episode_*.csv files")

    ncols = 2
    nrows = int(np.ceil(len(files) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(11, 2.4 * nrows + 0.6),
                             sharex=True, sharey=True)
    axes = np.atleast_1d(axes).ravel()

    for ax, fpath in zip(axes, files):
        ep = fpath.stem.replace("09_trajectory_xy_", "")
        d = pd.read_csv(fpath)
        draw_goal_band(ax)
        ax.plot(d["robot_x"], d["robot_y"], color=UNET_BLUE, lw=1.3,
                label="Robot", rasterized=True)
        ball = d.dropna(subset=["ball_x", "ball_y"])
        ax.plot(ball["ball_x"], ball["ball_y"], color=ACCENT, lw=1.3,
                label="Balón", rasterized=True)
        # start / end markers
        ax.scatter(d["robot_x"].iloc[0], d["robot_y"].iloc[0], color=UNET_BLUE,
                   marker="o", s=35, zorder=5, edgecolor="white")
        if not ball.empty:
            ax.scatter(ball["ball_x"].iloc[-1], ball["ball_y"].iloc[-1],
                       color=ACCENT, marker="*", s=130, zorder=5,
                       edgecolor="white")
        scored = ep.endswith("005")  # only episode 5 scored in this run
        ax.set_title(f"{ep_label(ep)} {'— gol ✓' if scored else '— sin gol'}",
                     fontsize=11)
        ax.set_aspect("equal")
        ax.set_xlim(FIELD["x_min"] - 0.05, FIELD["x_max"] + 0.05)
        ax.set_ylim(FIELD["y_min"] - 0.05, FIELD["y_max"] + 0.05)

    for ax in axes[len(files):]:
        ax.axis("off")
    for ax in axes[len(files) - ncols:len(files)]:
        ax.set_xlabel("x (m)")
    for ax in axes[::ncols]:
        ax.set_ylabel("y (m)")

    handles = [
        plt.Line2D([], [], color=UNET_BLUE, lw=1.6, label="Robot"),
        plt.Line2D([], [], color=ACCENT, lw=1.6, label="Balón"),
        Patch(facecolor=UNET_BLUE, alpha=0.10, label="Zona de portería"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3,
               bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Trayectorias del robot y del balón en el campo (x, y)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    save(fig, out_dir, "trajectory_xy")


# --------------------------------------------------------------------------- #
# 9. Occupancy heatmaps (robot + ball)
# --------------------------------------------------------------------------- #
def _heatmap_grid(df_entity: pd.DataFrame):
    cell = float(df_entity["cell_size_m"].iloc[0])
    x_min, x_max = float(df_entity["x_min"].iloc[0]), float(df_entity["x_max"].iloc[0])
    y_min, y_max = float(df_entity["y_min"].iloc[0]), float(df_entity["y_max"].iloc[0])
    nx = int(round((x_max - x_min) / cell))
    ny = int(round((y_max - y_min) / cell))
    grid = np.zeros((ny, nx))
    for r in df_entity.itertuples():
        xb, yb = int(r.x_bin), int(r.y_bin)
        if 0 <= yb < ny and 0 <= xb < nx:
            grid[yb, xb] = r.dwell_time_s
    x_edges = x_min + np.arange(nx + 1) * cell
    y_edges = y_min + np.arange(ny + 1) * cell
    return grid, x_edges, y_edges


def plot_heatmaps(csv_dir: Path, out_dir: Path) -> None:
    df = pd.read_csv(csv_dir / "11_heatmap_xy_trials.csv")
    specs = {
        "robot": ("robot_heatmap", "Mapa de calor — permanencia del robot", "viridis"),
        "ball": ("ball_heatmap", "Mapa de calor — permanencia del balón", "magma"),
    }
    for entity, (name, title, cmap) in specs.items():
        sub = df[df["entity"] == entity]
        if sub.empty:
            print(f"  [skip] heatmap '{entity}': no rows")
            continue
        grid, xe, ye = _heatmap_grid(sub)
        fig, ax = plt.subplots(figsize=(10, 3.4))
        mesh = ax.pcolormesh(xe, ye, np.ma.masked_equal(grid, 0.0),
                             cmap=cmap, shading="flat")
        cbar = fig.colorbar(mesh, ax=ax, pad=0.02, fraction=0.05)
        cbar.set_label("Tiempo acumulado (s)")
        ax.axvline(FIELD["x_max"], color="white", lw=1.6, ls="--", alpha=0.8)
        ax.text(FIELD["x_max"], ye[-1], " portería", color="#333333",
                va="bottom", ha="right", fontsize=9)
        ax.set_aspect("equal")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        ax.set_title(title)
        ax.grid(False)
        save(fig, out_dir, name)


# --------------------------------------------------------------------------- #
# Vertical top-down field figures (portrait): goal at top, robot start at bottom
#
# Coordinate transform: the simulator uses +x as the forward direction (towards
# the goal) and y as the lateral offset. To draw a portrait field we map
#     horizontal axis (plot-x) = y   (lateral)
#     vertical   axis (plot-y) = x   (forward, increasing upward)
# so the robot starts near the bottom (x~0) and advances upward to the goal at
# x_max. Every plot/scatter below therefore passes (y, x) in that order.
# --------------------------------------------------------------------------- #
def _gaussian_blur(arr: np.ndarray, sigma: float) -> np.ndarray:
    """Gaussian smoothing; uses SciPy if present, else a separable NumPy fallback."""
    try:
        from scipy.ndimage import gaussian_filter

        return gaussian_filter(arr, sigma)
    except Exception:  # pragma: no cover - fallback path
        radius = int(max(1, round(3 * sigma)))
        x = np.arange(-radius, radius + 1)
        kernel = np.exp(-(x ** 2) / (2.0 * sigma ** 2))
        kernel /= kernel.sum()
        out = np.apply_along_axis(lambda m: np.convolve(m, kernel, mode="same"), 0, arr)
        out = np.apply_along_axis(lambda m: np.convolve(m, kernel, mode="same"), 1, out)
        return out


def _density_grid(y_vals, x_vals, sigma=5.0, bins_per_m=130):
    """Smoothed 2D occupancy density on the (y, x) field plane, normalised to [0, 1].

    Returns ``(density, extent)`` where ``density`` is indexed [iy, ix] and
    ``extent = (y_min, y_max, x_min, x_max)`` for plotting.
    """
    y0, y1 = FIELD["y_min"] - 0.05, FIELD["y_max"] + 0.05
    x0, x1 = FIELD["x_min"] - 0.05, FIELD["x_max"] + 0.05
    n_y = int(round((y1 - y0) * bins_per_m))
    n_x = int(round((x1 - x0) * bins_per_m))
    hist, _, _ = np.histogram2d(y_vals, x_vals, bins=[n_y, n_x],
                                range=[[y0, y1], [x0, x1]])
    hist = _gaussian_blur(hist, sigma)
    if hist.max() > 0:
        hist /= hist.max()
    return hist, (y0, y1, x0, x1)


def draw_field_vertical(ax, *, mark_start: bool = True) -> None:
    """Draw a clean portrait top-down soccer field (goal at top)."""
    x0, x1 = FIELD["x_min"], FIELD["x_max"]
    y0, y1 = FIELD["y_min"], FIELD["y_max"]
    gdepth = 0.12  # drawn depth of the goal structure above the goal line

    # green pitch
    ax.add_patch(Rectangle((y0, x0), y1 - y0, x1 - x0,
                           facecolor=FIELD_GREEN, edgecolor="none", zorder=0))
    # penalty-area-style box near the goal
    pb_w, pb_d = GOAL_GW + 0.06, 0.35
    ax.add_patch(Rectangle((-pb_w / 2, x1 - pb_d), pb_w, pb_d, fill=False,
                           edgecolor=FIELD_LINE, lw=1.2, alpha=0.7, zorder=3))
    # touchline boundary
    ax.add_patch(Rectangle((y0, x0), y1 - y0, x1 - x0, fill=False,
                           edgecolor=FIELD_LINE, lw=2.0, zorder=3))
    # central path line (robot start -> goal)
    ax.plot([0, 0], [x0, x1], color=FIELD_LINE, lw=1.0, ls="--", alpha=0.55, zorder=3)
    # goal line + goal structure (net) at the top
    ax.plot([y0, y1], [x1, x1], color=FIELD_LINE, lw=2.5, zorder=3)
    ax.add_patch(Rectangle((-GOAL_GW / 2, x1), GOAL_GW, gdepth,
                           facecolor="0.82", edgecolor="0.35", lw=1.6, zorder=3))
    for yy in np.linspace(-GOAL_GW / 2, GOAL_GW / 2, 6):
        ax.plot([yy, yy], [x1, x1 + gdepth], color="0.6", lw=0.6, zorder=4)
    ax.text(0, x1 + gdepth + 0.03, "Portería", ha="center", va="bottom",
            fontsize=9, fontweight="bold", color="0.15", zorder=5)

    if mark_start:
        ax.scatter(0, 0, marker="s", s=55, facecolor="white",
                   edgecolor=ROBOT_COLOR, lw=1.5, zorder=6)
        ax.text(0, x0 - 0.03, "Inicio robot", ha="center", va="top",
                fontsize=8, color="0.2", zorder=6)

    ax.set_xlim(y0 - 0.07, y1 + 0.07)
    ax.set_ylim(x0 - 0.12, x1 + gdepth + 0.08)
    ax.set_aspect("equal")
    ax.set_xlabel("y — desplazamiento lateral (m)")
    ax.set_ylabel("x — avance hacia la portería (m)")
    ax.grid(False)


def plot_trajectory_xy_vertical(csv_dir: Path, out_dir: Path) -> None:
    files = sorted(csv_dir.glob("09_trajectory_xy_episode_*.csv"))
    if not files:
        trials = csv_dir / "09_trajectory_xy_trials.csv"
        if not trials.exists():
            raise FileNotFoundError("no trajectory CSVs found")
        files = [trials]

    fig, ax = plt.subplots(figsize=(4.6, 9.4))
    draw_field_vertical(ax)
    for fpath in files:
        d = pd.read_csv(fpath)
        scored = fpath.stem.endswith("005")
        ax.plot(d["robot_y"], d["robot_x"], color=ROBOT_COLOR, lw=1.2, alpha=0.45,
                solid_capstyle="round", zorder=4, rasterized=True)
        ball = d.dropna(subset=["ball_x", "ball_y"])
        ax.plot(ball["ball_y"], ball["ball_x"], color=BALL_COLOR, lw=1.2, alpha=0.5,
                solid_capstyle="round", zorder=5, rasterized=True)
        if not ball.empty:
            if scored:
                ax.scatter(ball["ball_y"].iloc[-1], ball["ball_x"].iloc[-1],
                           marker="*", s=260, color="#FFC400", edgecolor="0.2",
                           lw=0.8, zorder=7)
            else:
                ax.scatter(ball["ball_y"].iloc[-1], ball["ball_x"].iloc[-1],
                           marker="o", s=26, color=BALL_COLOR, edgecolor="white",
                           lw=0.6, zorder=6)
    # common ball start (~ x=0.62, y=0)
    ax.scatter(0.0, 0.62, marker="o", s=70, color=BALL_COLOR, edgecolor="white",
               lw=1.2, zorder=7)

    handles = [
        Line2D([], [], color=ROBOT_COLOR, lw=2.2, label="Trayectoria robot"),
        Line2D([], [], color=BALL_COLOR, lw=2.2, label="Trayectoria balón"),
        Line2D([], [], marker="*", linestyle="none", markerfacecolor="#FFC400",
               markeredgecolor="0.2", markersize=16, label="Gol (Ep. 5)"),
        Line2D([], [], marker="s", linestyle="none", markerfacecolor="white",
               markeredgecolor=ROBOT_COLOR, markersize=9, label="Inicio robot"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.07),
              ncol=2, fontsize=8.5, framealpha=0.95)
    ax.set_title("Trayectorias del robot y del balón\n(vista cenital · 5 episodios)",
                 fontsize=12)
    fig.tight_layout()
    save(fig, out_dir, "trajectory_xy_vertical")


def plot_heatmaps_vertical(csv_dir: Path, out_dir: Path) -> None:
    df = pd.read_csv(csv_dir / "09_trajectory_xy_trials.csv")
    specs = {
        "robot": ("robot_heatmap_vertical",
                  "Densidad de posición del robot\n(vista cenital · 5 episodios)",
                  ("robot_x", "robot_y")),
        "ball": ("ball_heatmap_vertical",
                 "Densidad de posición del balón\n(vista cenital · 5 episodios)",
                 ("ball_x", "ball_y")),
    }
    cmap = plt.cm.inferno
    for entity, (name, title, (cx, cy)) in specs.items():
        d = df.dropna(subset=[cx, cy])
        if d.empty:
            print(f"  [skip] heatmap '{entity}': no points")
            continue
        dens, (y0, y1, x0, x1) = _density_grid(d[cy].to_numpy(), d[cx].to_numpy(),
                                                sigma=5.0)
        fig, ax = plt.subplots(figsize=(4.6, 9.4))
        draw_field_vertical(ax, mark_start=(entity == "robot"))

        img = dens.T  # -> [ix, iy] so vertical axis is x
        rgba = cmap(img)
        alpha = np.clip(img * 1.5, 0.0, 1.0)
        alpha[img < 0.02] = 0.0  # transparent where ~no occupancy -> field shows
        rgba[..., 3] = alpha
        ax.imshow(rgba, origin="lower", extent=(y0, y1, x0, x1), aspect="equal",
                  interpolation="bilinear", zorder=2)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=Normalize(0, 1))
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("Densidad de permanencia (norm.)")
        ax.set_title(title, fontsize=12)
        fig.tight_layout()
        save(fig, out_dir, name)


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
PLOTS = [
    ("goal_success_rate", plot_goal_success_rate),
    ("time_to_ball_control", plot_time_to_ball_control),
    ("time_to_goal", plot_time_to_goal),
    ("fsm_state_time", plot_fsm_state_time),
    ("fsm_timeline", plot_fsm_timeline),
    ("fsm_event_counts", plot_fsm_event_counts),
    ("topic_frequency", plot_topic_frequency),
    ("trajectory_xy", plot_trajectory_xy),
    ("heatmaps", plot_heatmaps),
    ("trajectory_xy_vertical", plot_trajectory_xy_vertical),
    ("heatmaps_vertical", plot_heatmaps_vertical),
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv-dir", type=Path, default=DEFAULT_CSV_DIR,
                        help="directory with the metric CSV files")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR,
                        help="directory where figures are written")
    args = parser.parse_args(argv)

    csv_dir: Path = args.csv_dir
    out_dir: Path = args.output_dir
    if not csv_dir.is_dir():
        parser.error(f"csv-dir does not exist: {csv_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"csv-dir : {csv_dir}")
    print(f"out-dir : {out_dir}\n")

    ok = 0
    for name, fn in PLOTS:
        print(f"-> {name}")
        try:
            fn(csv_dir, out_dir)
            ok += 1
        except FileNotFoundError as exc:
            print(f"  [skip] missing input: {exc}")
        except Exception as exc:  # noqa: BLE001 - best effort, keep going
            print(f"  [FAIL] {name}: {exc}")

    print(f"\nDone: {ok}/{len(PLOTS)} plot groups succeeded -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
