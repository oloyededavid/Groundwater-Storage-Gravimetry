from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon


def set_publication_style() -> None:
    """Configure matplotlib to match peer-reviewed hydrological journal typography."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Times New Roman", "Georgia"],
        "axes.edgecolor": "#1a1a1a",
        "axes.linewidth": 0.9,
        "grid.color": "#cccccc",
        "grid.linestyle": "--",
        "grid.linewidth": 0.5,
        "grid.alpha": 0.6,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


def _add_north_arrow_and_scale(
    ax: plt.Axes, lon_min: float, lon_max: float, lat_min: float, lat_max: float
) -> None:
    """Add cartographic North arrow and 100 km scale bar to spatial maps."""
    nx = lon_min + 0.08 * (lon_max - lon_min)
    ny_base = lat_max - 0.16 * (lat_max - lat_min)
    ny_tip = lat_max - 0.06 * (lat_max - lat_min)
    ax.annotate(
        "",
        xy=(nx, ny_tip),
        xytext=(nx, ny_base),
        arrowprops=dict(facecolor="black", width=2.5, headwidth=8, headlength=8),
        zorder=15,
    )
    ax.text(
        nx,
        ny_tip + 0.02 * (lat_max - lat_min),
        "N",
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold",
        zorder=15,
    )

    # 100 km Scale Bar (Bottom Left: ~0.92 deg at 13N)
    sx0 = lon_min + 0.08 * (lon_max - lon_min)
    sx1 = sx0 + 0.92
    sy = lat_min + 0.08 * (lat_max - lat_min)
    ax.plot([sx0, sx1], [sy, sy], color="black", lw=2.0, zorder=15)
    ax.plot([sx0, sx0], [sy - 0.06, sy + 0.06], color="black", lw=1.8, zorder=15)
    ax.plot([sx1, sx1], [sy - 0.06, sy + 0.06], color="black", lw=1.8, zorder=15)
    ax.text(
        (sx0 + sx1) / 2,
        sy + 0.08,
        "100 km",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        zorder=15,
    )


def _format_lat_lon_axes(
    ax: plt.Axes, lon_min: float, lon_max: float, lat_min: float, lat_max: float
) -> None:
    """Format map axes with degree symbols and gridlines."""
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)
    xticks = np.arange(np.ceil(lon_min), np.floor(lon_max) + 1, 1.0)
    yticks = np.arange(np.ceil(lat_min), np.floor(lat_max) + 1, 1.0)
    ax.set_xticks(xticks)
    ax.set_yticks(yticks)
    ax.set_xticklabels([f"{int(x)}°E" for x in xticks], fontsize=9)
    ax.set_yticklabels([f"{int(y)}°N" for y in yticks], fontsize=9)
    ax.grid(True, zorder=1)
    ax.set_aspect("equal", adjustable="box")


def plot_spatial_basin_grid(
    lon_grid: np.ndarray,
    lat_grid: np.ndarray,
    data_grid: np.ndarray,
    basin_coords: np.ndarray,
    title: str,
    subtitle: str,
    cbar_label: str,
    cmap: str = "terrain",
    vmin: float | None = None,
    vmax: float | None = None,
    border_coords: np.ndarray | None = None,
    stream_lines: list[np.ndarray] | None = None,
    out_path: str | None = None,
) -> plt.Figure:
    """Render a publication-grade clipped spatial raster map of the aquifer basin."""
    set_publication_style()
    fig, ax = plt.subplots(figsize=(8.5, 7.2))

    lon_min, lon_max = float(lon_grid.min()), float(lon_grid.max())
    lat_min, lat_max = float(lat_grid.min()), float(lat_grid.max())

    poly_patch = Polygon(
        basin_coords,
        closed=True,
        facecolor="none",
        edgecolor="black",
        linewidth=2.0,
        zorder=10,
    )
    ax.add_patch(poly_patch)

    mesh = ax.pcolormesh(
        lon_grid,
        lat_grid,
        data_grid,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        shading="auto",
        zorder=3,
    )
    mesh.set_clip_path(poly_patch)

    if border_coords is not None:
        ax.plot(
            border_coords[:, 0],
            border_coords[:, 1],
            color="#555555",
            linestyle="-.",
            linewidth=1.1,
            label="International Border",
            zorder=8,
        )

    if stream_lines is not None:
        for idx, sline in enumerate(stream_lines):
            lbl = "HydroSHEDS Ephemeral/Perennial Routing" if idx == 0 else None
            ax.plot(
                sline[:, 0],
                sline[:, 1],
                color="#1f618d",
                linewidth=1.2,
                alpha=0.85,
                label=lbl,
                zorder=9,
            )

    ax.plot([], [], color="black", linewidth=2.0, label="Aquifer Catchment Boundary")

    ax.text(
        lon_min + 0.18 * (lon_max - lon_min),
        lat_max - 0.10 * (lat_max - lat_min),
        "N I G E R",
        fontsize=12,
        fontweight="bold",
        color="#666666",
        zorder=6,
    )
    ax.text(
        lon_min + 0.52 * (lon_max - lon_min),
        lat_min + 0.12 * (lat_max - lat_min),
        "N I G E R I A",
        fontsize=12,
        fontweight="bold",
        color="#666666",
        zorder=6,
    )

    _add_north_arrow_and_scale(ax, lon_min, lon_max, lat_min, lat_max)
    _format_lat_lon_axes(ax, lon_min, lon_max, lat_min, lat_max)

    cbar = fig.colorbar(mesh, ax=ax, fraction=0.038, pad=0.03)
    cbar.set_label(cbar_label, fontsize=10, fontweight="bold")

    ax.set_title(f"{title}\n{subtitle}", fontsize=12, fontweight="bold", pad=12)
    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=2,
        frameon=True,
        edgecolor="black",
        fontsize=9,
    )

    if out_path:
        fig.savefig(out_path, dpi=300)
    return fig
