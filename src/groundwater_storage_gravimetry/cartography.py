from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Polygon


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
    nx = lon_min + 0.07 * (lon_max - lon_min)
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

    sx0 = lon_min + 0.07 * (lon_max - lon_min)
    sx1 = sx0 + 0.92
    sy = lat_min + 0.07 * (lat_max - lat_min)
    ax.plot([sx0, sx1], [sy, sy], color="black", lw=2.0, zorder=15)
    ax.plot([sx0, sx0], [sy - 0.07, sy + 0.07], color="black", lw=1.8, zorder=15)
    ax.plot([sx1, sx1], [sy - 0.07, sy + 0.07], color="black", lw=1.8, zorder=15)
    ax.text(
        (sx0 + sx1) / 2,
        sy + 0.09,
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
    ax.set_xlabel("Longitude (°E)", fontsize=10, fontweight="bold", labelpad=6)
    ax.set_ylabel("Latitude (°N)", fontsize=10, fontweight="bold", labelpad=6)
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
    border_coords: list[np.ndarray] | None = None,
    stream_lines: list[np.ndarray] | None = None,
    lake_coords: np.ndarray | None = None,
    extra_legend_patches: list[Patch | Line2D] | None = None,
    out_path: str | None = None,
) -> plt.Figure:
    """Render a publication-grade clipped spatial raster map with comprehensive external legend."""
    set_publication_style()
    fig, ax = plt.subplots(figsize=(9.0, 8.4))

    lon_min, lon_max = float(lon_grid.min()), float(lon_grid.max())
    lat_min, lat_max = float(lat_grid.min()), float(lat_grid.max())

    poly_patch = Polygon(
        basin_coords,
        closed=True,
        facecolor="none",
        edgecolor="black",
        linewidth=2.2,
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
        for idx, b_line in enumerate(border_coords):
            lbl = "International Border (Transboundary Sector)" if idx == 0 else None
            (line_obj,) = ax.plot(
                b_line[:, 0],
                b_line[:, 1],
                color="#333333",
                linestyle="-.",
                linewidth=1.2,
                label=lbl,
                zorder=8,
            )
            line_obj.set_clip_path(poly_patch)

    if stream_lines is not None:
        for idx, sline in enumerate(stream_lines):
            lbl = "Komadugu-Yobe & Chari-Logone Fluvial Network" if idx == 0 else None
            (s_obj,) = ax.plot(
                sline[:, 0],
                sline[:, 1],
                color="#0b5394",
                linewidth=1.5,
                alpha=0.9,
                label=lbl,
                zorder=9,
            )
            s_obj.set_clip_path(poly_patch)

    if lake_coords is not None:
        lake_poly = Polygon(
            lake_coords,
            closed=True,
            facecolor="#2980b9",
            edgecolor="#0b3c5d",
            linewidth=1.3,
            alpha=0.88,
            label="Lake Chad Open-Water / Sump Extent",
            zorder=11,
        )
        ax.add_patch(lake_poly)

    ax.plot([], [], color="black", linewidth=2.2, label="Quaternary Chad Formation Aquifer Boundary")

    # Cleanly positioned national sector labels inside the basin (avoiding boundary collisions)
    ax.text(11.9, 14.0, "N I G E R", fontsize=11, fontweight="bold", color="#3a3a3a", zorder=12)
    ax.text(14.8, 13.5, "C H A D", fontsize=11, fontweight="bold", color="#3a3a3a", zorder=12)
    ax.text(11.3, 11.6, "N I G E R I A", fontsize=11, fontweight="bold", color="#3a3a3a", zorder=12)
    ax.text(13.8, 10.6, "C A M E R O O N", fontsize=10, fontweight="bold", color="#3a3a3a", zorder=12)

    _add_north_arrow_and_scale(ax, lon_min, lon_max, lat_min, lat_max)
    _format_lat_lon_axes(ax, lon_min, lon_max, lat_min, lat_max)

    cbar = fig.colorbar(mesh, ax=ax, fraction=0.038, pad=0.03)
    cbar.set_label(cbar_label, fontsize=10, fontweight="bold")

    ax.set_title(f"{title}\n{subtitle}", fontsize=11.5, fontweight="bold", pad=12)

    handles, labels = ax.get_legend_handles_labels()
    if extra_legend_patches:
        handles.extend(extra_legend_patches)
        labels.extend([p.get_label() for p in extra_legend_patches])

    ax.legend(
        handles=handles,
        labels=labels,
        title="Cartographic & Hydrogeologic Legend",
        title_fontsize=9,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.14),
        ncol=2,
        frameon=True,
        facecolor="#fafafa",
        edgecolor="black",
        fontsize=8.5,
    )

    fig.subplots_adjust(bottom=0.25, top=0.90)

    if out_path:
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
    return fig
