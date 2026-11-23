from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba
from matplotlib.patches import Circle, Ellipse, PathPatch, Polygon
from matplotlib.path import Path as MplPath
import networkx as nx
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter


# Muted, high-contrast colors inspired by the supplied journal figure.
_PALETTE = [
    "#E45B59",  # coral red
    "#438FC4",  # blue
    "#36A56B",  # green
    "#C1B94F",  # muted yellow
    "#9470B7",  # purple
    "#E59A4F",  # orange
    "#3CA6A1",  # teal
    "#C879A6",  # rose
]
_DARK = "#263238"
_TEXT = "#20272D"
_MUTED = "#6D777F"


def _configure_font() -> str:
    """Prefer Times-style journal typography while keeping a CJK fallback available."""
    serif_candidates = [
        "Times New Roman", "Nimbus Roman", "Nimbus Roman No9 L",
        "Liberation Serif", "TeX Gyre Termes", "DejaVu Serif",
    ]
    cjk_candidates = [
        Path("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "msyh.ttc",
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "simhei.ttf",
        Path.home() / "Library/Fonts/Arial Unicode.ttf",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    serif = next((name for name in serif_candidates if name in available), "DejaVu Serif")
    fallback_family = None
    for font_path in cjk_candidates:
        if font_path.exists():
            try:
                font_manager.fontManager.addfont(str(font_path))
                fallback_family = font_manager.FontProperties(fname=str(font_path)).get_name()
                break
            except Exception:
                continue
    plt.rcParams["font.family"] = serif
    plt.rcParams["font.serif"] = [serif] + ([fallback_family] if fallback_family else [])
    plt.rcParams["mathtext.fontset"] = "stix"
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["ps.fonttype"] = 42
    return serif


def _palette_for_clusters(cluster_ids: list[int]) -> dict[int, str]:
    return {cluster: _PALETTE[i % len(_PALETTE)] for i, cluster in enumerate(cluster_ids)}


def _layout(graph: nx.Graph, seed: int = 42) -> dict:
    """Compact ForceAtlas2 layout; disconnected components are packed near the main map."""
    if graph.number_of_nodes() == 0:
        return {}
    if graph.number_of_nodes() == 1:
        return {next(iter(graph.nodes)): np.array([0.0, 0.0])}

    def local_layout(subgraph: nx.Graph, local_seed: int) -> dict:
        if subgraph.number_of_nodes() == 1:
            return {next(iter(subgraph.nodes)): np.array([0.0, 0.0])}
        if hasattr(nx, "forceatlas2_layout"):
            try:
                return nx.forceatlas2_layout(
                    subgraph, max_iter=420, jitter_tolerance=1.0,
                    scaling_ratio=1.65, gravity=0.85, strong_gravity=False,
                    linlog=False, weight="weight", seed=local_seed,
                )
            except Exception:
                pass
        return nx.spring_layout(
            subgraph, seed=local_seed, weight="weight", iterations=450,
            k=1.10 / np.sqrt(subgraph.number_of_nodes()),
        )

    components = sorted(nx.connected_components(graph), key=lambda c: (-len(c), sorted(map(str, c))[0]))
    if len(components) == 1:
        raw = local_layout(graph, seed)
        coords = np.array([raw[n] for n in graph.nodes], dtype=float)
        coords -= coords.mean(axis=0)
        max_range = max(float(np.ptp(coords[:, 0])), float(np.ptp(coords[:, 1])), 1e-6)
        coords *= 10.0 / max_range
        coords[:, 0] *= 1.10
        coords[:, 1] *= 0.94
        return {node: coords[i] for i, node in enumerate(graph.nodes)}

    # A force layout can fling tiny disconnected components far away. Lay out
    # each component independently and pack small components around the main one.
    main_nodes = components[0]
    main_graph = graph.subgraph(main_nodes).copy()
    main_raw = local_layout(main_graph, seed)
    main_xy = np.array(list(main_raw.values()), dtype=float)
    main_xy -= main_xy.mean(axis=0)
    main_radius = max(float(np.max(np.linalg.norm(main_xy, axis=1))), 1e-6)
    main_xy *= 2.65 / main_radius
    positions = {node: main_xy[i] for i, node in enumerate(main_raw)}
    main_radius = 2.65

    smaller = components[1:]
    for i, component in enumerate(smaller):
        subgraph = graph.subgraph(component).copy()
        local = local_layout(subgraph, seed + i + 1)
        local_xy = np.array(list(local.values()), dtype=float)
        local_xy -= local_xy.mean(axis=0)
        if len(component) == 1:
            component_radius = 0.28
        else:
            local_radius = max(float(np.max(np.linalg.norm(local_xy, axis=1))), 1e-6)
            component_radius = 0.35 + 0.08 * np.sqrt(len(component))
            local_xy *= component_radius / local_radius
        if len(component) == 1:
            local_xy[0] = np.array([0.0, 0.0])
        angle = 2 * np.pi * i / max(len(smaller), 1)
        center_distance = main_radius + component_radius - 0.10
        center = np.array([np.cos(angle), np.sin(angle)]) * center_distance
        for j, node in enumerate(local):
            positions[node] = local_xy[j] + center

    coords = np.array([positions[n] for n in graph.nodes], dtype=float)
    coords -= coords.mean(axis=0)
    max_range = max(float(np.ptp(coords[:, 0])), float(np.ptp(coords[:, 1])), 1e-6)
    coords *= 10.0 / max_range
    coords[:, 0] *= 1.10  # a restrained landscape bias for journal-width figures
    coords[:, 1] *= 0.94
    return {node: coords[i] for i, node in enumerate(graph.nodes)}


def _node_size(value: float, max_value: float) -> float:
    ratio = max(float(value), 1.0) / max(float(max_value), 1.0)
    return 78.0 + 620.0 * (ratio ** 1.22)


def _pretty_term(term: str) -> str:
    text = str(term).strip()
    replacements = [
        ("co2", "CO2"), ("ghg", "GHG"), ("lca", "LCA"), ("ccs", "CCS"),
        ("fcc", "FCC"), ("api", "API"), ("leap", "LEAP"),
    ]
    lower = text.casefold()
    for old, new in replacements:
        lower = lower.replace(old, new.casefold())
    # Title-case normal words while preserving common acronyms and CO₂.
    words = []
    for word in lower.split():
        if word in {"co2", "ghg", "lca", "ccs", "fcc", "api", "leap"}:
            words.append(word.upper())
        else:
            words.append(word[:1].upper() + word[1:])
    return " ".join(words)


def _cluster_titles(graph: nx.Graph, nodes: pd.DataFrame) -> dict[int, str]:
    """Create transparent, data-derived headings from each cluster's top terms."""
    titles: dict[int, str] = {}
    if nodes.empty:
        return titles
    for cid, group in nodes.groupby("cluster"):
        ranked = group.sort_values(
            ["occurrences", "total_link_strength", "keyword"],
            ascending=[False, False, True],
        )
        selected: list[str] = []
        for term in ranked["keyword"].astype(str):
            tokens = set(term.casefold().replace("-", " ").split())
            if selected:
                previous = set(selected[0].casefold().replace("-", " ").split())
                overlap = len(tokens & previous) / max(len(tokens | previous), 1)
                if overlap >= 0.55:
                    continue
            selected.append(term)
            if len(selected) == 2:
                break
        if not selected:
            continue
        title = " & ".join(_pretty_term(t) for t in selected)
        if len(title) > 38:
            title = _pretty_term(selected[0])
        titles[int(cid)] = f"# {title}"
    return titles


def _draw_cluster_hulls(ax, graph: nx.Graph, pos: dict, palette: dict[int, str]) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Draw soft dashed ellipses around clusters, matching the reference-map style."""
    extents: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for cid in sorted(palette):
        members = [n for n in graph.nodes if int(graph.nodes[n].get("cluster", 1)) == cid]
        pts = np.array([pos[n] for n in members], dtype=float)
        color = palette[cid]
        if len(pts) == 1:
            center = pts[0]
            radius = 0.48
            patch = Circle(center, radius=radius, facecolor=to_rgba(color, 0.035),
                           edgecolor=_DARK, linewidth=1.8,
                           linestyle=(0, (3.2, 2.2)), zorder=0)
            ax.add_patch(patch)
            extents[cid] = (center - radius, center + radius)
            continue

        center = pts.mean(axis=0)
        if len(pts) == 2:
            delta = pts[1] - pts[0]
            major_radius = max(float(np.linalg.norm(delta)) / 2 + 0.42, 0.62)
            minor_radius = 0.48
            angle = float(np.degrees(np.arctan2(delta[1], delta[0])))
        else:
            covariance = np.cov((pts - center).T)
            eigenvalues, eigenvectors = np.linalg.eigh(covariance)
            order = np.argsort(eigenvalues)[::-1]
            eigenvalues = np.maximum(eigenvalues[order], 1e-5)
            eigenvectors = eigenvectors[:, order]
            rotated = (pts - center) @ eigenvectors
            # Robust quantiles reduce the influence of one remote keyword while
            # keeping the ellipse large enough to surround the dense core.
            major_radius = max(float(np.quantile(np.abs(rotated[:, 0]), 0.96)) * 1.28, 0.62) + 0.16
            minor_radius = max(float(np.quantile(np.abs(rotated[:, 1]), 0.96)) * 1.28, 0.54) + 0.16
            angle = float(np.degrees(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0])))

        patch = Ellipse(center, width=2 * major_radius, height=2 * minor_radius,
                        angle=angle, facecolor=to_rgba(color, 0.035),
                        edgecolor=_DARK, linewidth=1.8,
                        linestyle=(0, (3.2, 2.2)), zorder=0)
        ax.add_patch(patch)
        theta = np.radians(angle)
        extent_x = np.sqrt((major_radius * np.cos(theta)) ** 2 + (minor_radius * np.sin(theta)) ** 2)
        extent_y = np.sqrt((major_radius * np.sin(theta)) ** 2 + (minor_radius * np.cos(theta)) ** 2)
        extents[cid] = (center - np.array([extent_x, extent_y]),
                        center + np.array([extent_x, extent_y]))
    return extents


def _edge_collection(graph: nx.Graph, pos: dict, palette: dict[int, str]) -> LineCollection:
    segments, colors, widths = [], [], []
    max_weight = max((float(d.get("weight", 1)) for _, _, d in graph.edges(data=True)), default=1.0)
    edges = sorted(graph.edges(data=True), key=lambda item: (str(item[0]), str(item[1])))
    for i, (a, b, data) in enumerate(edges):
        p0 = np.asarray(pos[a], dtype=float)
        p2 = np.asarray(pos[b], dtype=float)
        delta = p2 - p0
        distance = float(np.linalg.norm(delta))
        if distance < 1e-8:
            continue
        normal = np.array([-delta[1], delta[0]]) / distance
        same_cluster = graph.nodes[a].get("cluster") == graph.nodes[b].get("cluster")
        sign = 1.0 if i % 2 == 0 else -1.0
        bend = min(0.22, 0.055 * distance) * sign
        if not same_cluster:
            bend *= 0.65
        control = (p0 + p2) / 2 + normal * bend
        t = np.linspace(0.0, 1.0, 12)
        curve = ((1 - t)[:, None] ** 2 * p0
                 + 2 * ((1 - t) * t)[:, None] * control
                 + (t[:, None] ** 2) * p2)
        segments.append(curve)
        weight = float(data.get("weight", 1))
        strength = np.sqrt(max(weight, 1.0) / max(max_weight, 1.0))
        widths.append(0.9 + 1.9 * strength)
        if same_cluster:
            color = palette.get(int(graph.nodes[a].get("cluster", 1)), "#87939B")
            colors.append(to_rgba(color, 0.30 + 0.28 * strength))
        else:
            from matplotlib.colors import to_rgb
            ca = np.array(to_rgb(palette.get(int(graph.nodes[a].get("cluster", 1)), "#87939B")))
            cb = np.array(to_rgb(palette.get(int(graph.nodes[b].get("cluster", 1)), "#87939B")))
            mixed = tuple((ca * 0.5 + cb * 0.5).tolist())
            colors.append((*mixed, 0.14 + 0.10 * strength))
    return LineCollection(segments, colors=colors, linewidths=widths, zorder=1,
                          capstyle="round", joinstyle="round")


def _auto_label_limit(n_nodes: int, max_labels: int | None) -> int:
    if max_labels is not None and max_labels > 0:
        return min(int(max_labels), n_nodes)
    if n_nodes <= 80:
        return n_nodes
    if n_nodes <= 140:
        return max(80, int(round(n_nodes * 0.82)))
    return min(180, max(110, int(round(n_nodes * 0.74))))


def _relax_labels(fig, ax, text_artists: list, iterations: int = 85) -> dict:
    """Resolve text collisions efficiently in display coordinates."""
    if len(text_artists) < 2:
        return {}
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    original = {id(t): np.asarray(t.get_position(), dtype=float).copy() for t in text_artists}
    boxes = [t.get_window_extent(renderer=renderer).expanded(1.14, 1.28) for t in text_artists]
    shifts_total = np.zeros((len(text_artists), 2), dtype=float)

    for _ in range(iterations):
        shifts = np.zeros_like(shifts_total)
        collisions = 0
        for i in range(len(boxes)):
            a = boxes[i]
            for j in range(i + 1, len(boxes)):
                b = boxes[j]
                overlap_x = min(a.x1, b.x1) - max(a.x0, b.x0)
                overlap_y = min(a.y1, b.y1) - max(a.y0, b.y0)
                if overlap_x <= 0 or overlap_y <= 0:
                    continue
                collisions += 1
                ca = np.array([(a.x0 + a.x1) / 2, (a.y0 + a.y1) / 2])
                cb = np.array([(b.x0 + b.x1) / 2, (b.y0 + b.y1) / 2])
                if overlap_x < overlap_y:
                    direction = np.sign(ca[0] - cb[0])
                    if direction == 0:
                        direction = -1 if (i + j) % 2 else 1
                    amount = overlap_x * 0.72 + 1.8
                    shifts[i, 0] += direction * amount / 2
                    shifts[j, 0] -= direction * amount / 2
                else:
                    direction = np.sign(ca[1] - cb[1])
                    if direction == 0:
                        direction = -1 if (i + j) % 2 else 1
                    amount = overlap_y * 0.72 + 1.8
                    shifts[i, 1] += direction * amount / 2
                    shifts[j, 1] -= direction * amount / 2
        if collisions == 0:
            break
        # Update approximate bounding boxes directly; one canvas draw is enough.
        for i, shift in enumerate(shifts):
            if not np.any(shift):
                continue
            boxes[i] = matplotlib.transforms.Bbox.from_extents(
                boxes[i].x0 + shift[0], boxes[i].y0 + shift[1],
                boxes[i].x1 + shift[0], boxes[i].y1 + shift[1],
            )
            shifts_total[i] += shift

    for i, text in enumerate(text_artists):
        if np.any(shifts_total[i]):
            display_xy = ax.transData.transform(text.get_position()) + shifts_total[i]
            text.set_position(ax.transData.inverted().transform(display_xy))
    moved = {}
    for text in text_artists:
        moved[id(text)] = (original[id(text)], np.asarray(text.get_position(), dtype=float).copy())
    return moved


def _draw_cluster_titles(ax, graph: nx.Graph, pos: dict, nodes: pd.DataFrame,
                         palette: dict[int, str], extents: dict) -> list:
    titles = _cluster_titles(graph, nodes)
    all_xy = np.array(list(pos.values()))
    global_center = all_xy.mean(axis=0)
    artists = []
    for cid in sorted(titles):
        members = [n for n in graph.nodes if int(graph.nodes[n].get("cluster", 1)) == cid]
        pts = np.array([pos[n] for n in members])
        center = pts.mean(axis=0)
        direction = center - global_center
        norm = float(np.linalg.norm(direction))
        if norm < 1e-5:
            angle = -np.pi / 2 + 2 * np.pi * (cid - 1) / max(len(titles), 1)
            direction = np.array([np.cos(angle), np.sin(angle)])
        else:
            direction /= norm
        min_xy, max_xy = extents[cid]
        radial_extent = max(float(np.dot(p - center, direction)) for p in pts)
        title_pos = center + direction * (radial_extent + 0.48)
        align = "left" if direction[0] > 0.24 else ("right" if direction[0] < -0.24 else "center")
        # Keep the title slightly above the boundary when the radial direction is horizontal.
        if abs(direction[1]) < 0.28:
            title_pos[1] += 0.20 if center[1] >= global_center[1] else -0.20
        size = 40.0 if len(members) >= 10 else (34.0 if len(members) >= 4 else 28.0)
        artist = ax.text(
            title_pos[0], title_pos[1], titles[cid],
            color=palette[cid], fontsize=size, fontweight="bold",
            ha=align, va="center", zorder=6,
            
        )
        artists.append(artist)
    return artists


def _draw_network(graph: nx.Graph, nodes: pd.DataFrame, output: Path, mode: str = "cluster",
                  max_labels: int | None = None, dpi: int = 400) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    _configure_font()
    pos = _layout(graph)
    fig, ax = plt.subplots(figsize=(19.5, 13.2), constrained_layout=False)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_axis_off()

    if graph.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "No keywords meet the selected occurrence threshold",
                ha="center", va="center", transform=ax.transAxes, color=_MUTED, fontsize=14)
        fig.savefig(output, dpi=dpi, bbox_inches="tight", facecolor="white", pad_inches=0.25)
        plt.close(fig)
        return pos

    cluster_ids = sorted({int(graph.nodes[n].get("cluster", 1)) for n in graph.nodes})
    palette = _palette_for_clusters(cluster_ids)
    extents = _draw_cluster_hulls(ax, graph, pos, palette)

    # Curved, translucent edges: within-cluster links inherit the cluster color;
    # cross-cluster links are neutral and deliberately quieter.
    ax.add_collection(_edge_collection(graph, pos, palette))

    max_occ = max(float(graph.nodes[n].get("occurrences", 1)) for n in graph.nodes)
    scale = 1.55 if mode != "overlay" else 1.0
    node_sizes = {n: _node_size(graph.nodes[n].get("occurrences", 1), max_occ) * scale for n in graph.nodes}
    if mode == "overlay":
        years = [graph.nodes[n].get("avg_year") for n in graph.nodes]
        numeric_years = [float(y) for y in years if y is not None and np.isfinite(y)]
        vmin, vmax = (min(numeric_years), max(numeric_years)) if numeric_years else (2000, 2025)
        if vmin == vmax:
            vmax = vmin + 1
        node_values = [graph.nodes[n].get("avg_year") if graph.nodes[n].get("avg_year") is not None else vmin for n in graph.nodes]
        sc = nx.draw_networkx_nodes(
            graph, pos, ax=ax, nodelist=list(graph.nodes),
            node_size=[node_sizes[n] for n in graph.nodes],
            node_color=node_values, cmap="viridis", vmin=vmin, vmax=vmax,
            alpha=0.96, linewidths=1.25, edgecolors="white",
        )
        cbar = fig.colorbar(sc, ax=ax, shrink=0.68, pad=0.012, fraction=0.025)
        cbar.set_label("Average publication year", fontsize=10, color=_TEXT, labelpad=9)
        cbar.ax.tick_params(labelsize=8, colors=_MUTED, length=2)
        cbar.outline.set_visible(False)
    else:
        for cid in cluster_ids:
            members = [n for n in graph.nodes if int(graph.nodes[n].get("cluster", 1)) == cid]
            nx.draw_networkx_nodes(
                graph, pos, ax=ax, nodelist=members,
                node_size=[node_sizes[n] for n in members],
                node_color=palette[cid], alpha=0.96,
                linewidths=1.25, edgecolors="white",
            )

    # Automatically choose a readable subset; all nodes are labelled in small maps.
    label_limit = _auto_label_limit(graph.number_of_nodes(), max_labels)
    rank_all = sorted(
        graph.nodes,
        key=lambda n: (
            -(float(graph.nodes[n].get("occurrences", 0)) ** 0.68)
            * np.log1p(float(graph.degree(n, weight="weight"))),
            str(n).casefold(),
        ),
    )
    # Always retain labels for tiny disconnected components: otherwise their
    # cluster heading would be visible but the actual terms could disappear.
    cluster_sizes = {cid: sum(1 for n in graph.nodes if int(graph.nodes[n].get("cluster", 1)) == cid)
                     for cid in cluster_ids}
    mandatory = [n for n in rank_all if cluster_sizes.get(int(graph.nodes[n].get("cluster", 1)), 99) <= 3]
    rank = list(dict.fromkeys(mandatory + [n for n in rank_all if n not in mandatory][:max(0, label_limit - len(mandatory))]))
    text_artists = []
    for node in rank:
        occ = float(graph.nodes[node].get("occurrences", 1))
        size = 24.0 + 9.0 * (occ / max_occ) ** 0.68
        text = ax.text(
            pos[node][0], pos[node][1], str(node),
            fontsize=size, color=_TEXT, ha="center", va="center",
            fontweight="medium", zorder=5,
        )
        text_artists.append(text)

    title_artists = _draw_cluster_titles(ax, graph, pos, nodes, palette, extents)

    # Give the labels and topic headings enough canvas room before collision resolution.
    xy = np.array(list(pos.values()))
    low = xy.min(axis=0)
    high = xy.max(axis=0)
    span = np.maximum(high - low, 1.0)
    margin = np.maximum(span * 0.26, 1.05)
    for lo, hi in extents.values():
        low = np.minimum(low, lo)
        high = np.maximum(high, hi)
    # Add extra headroom for cluster headings.
    low -= margin * np.array([0.85, 0.75])
    high += margin * np.array([0.85, 0.95])
    ax.set_xlim(low[0], high[0])
    ax.set_ylim(low[1], high[1])
    ax.set_aspect("equal", adjustable="box")
    fig.subplots_adjust(left=0.03, right=0.97, bottom=0.035, top=0.965)

    moved = _relax_labels(fig, ax, text_artists + title_artists, iterations=110)
    # Draw small leader lines only when automatic label deconfliction moves a label visibly.
    leader_segments = []
    leader_colors = []
    for text in text_artists:
        before, after = moved.get(id(text), (None, None))
        if before is None:
            continue
        p0 = ax.transData.transform(before)
        p1 = ax.transData.transform(after)
        if np.linalg.norm(p1 - p0) > 13:
            leader_segments.append([before, after])
            leader_colors.append(to_rgba("#89949B", 0.35))
    if leader_segments:
        ax.add_collection(LineCollection(leader_segments, colors=leader_colors,
                                         linewidths=0.9, zorder=4.4))

    # Cluster headings retain live text in SVG; their white backing keeps them legible.

    fig.savefig(output, dpi=dpi, bbox_inches="tight", facecolor="white", pad_inches=0.18)
    fig.savefig(output.with_suffix(".svg"), bbox_inches="tight", facecolor="white", pad_inches=0.18)
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight", facecolor="white", pad_inches=0.18)
    plt.close(fig)
    return pos


def _export_vosviewer(graph: nx.Graph, nodes: pd.DataFrame, positions: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    ordered = sorted(graph.nodes, key=lambda n: n.casefold())
    id_map = {term: i + 1 for i, term in enumerate(ordered)}
    node_lookup = nodes.set_index("keyword").to_dict("index") if not nodes.empty else {}

    map_path = out_dir / "vosviewer_map.txt"
    with map_path.open("w", encoding="utf-8", newline="") as f:
        f.write("id\tlabel\tx\ty\tcluster\tweight<Occurrences>\tweight<Links>\tweight<Total link strength>\tscore<Avg. pub. year>\n")
        for term in ordered:
            row = node_lookup[term]
            x, y = positions.get(term, (0.0, 0.0))
            avg_year = row.get("avg_publication_year")
            avg_year = "" if pd.isna(avg_year) else f"{float(avg_year):.4f}"
            label = term.replace('"', '""')
            if any(ch in label for ch in "\t,;"):
                label = f'"{label}"'
            f.write(f"{id_map[term]}\t{label}\t{float(x):.6f}\t{float(y):.6f}\t{int(row['cluster'])}\t{int(row['occurrences'])}\t{int(row['links'])}\t{int(row['total_link_strength'])}\t{avg_year}\n")

    network_path = out_dir / "vosviewer_network.txt"
    with network_path.open("w", encoding="utf-8", newline="") as f:
        for a, b, data in sorted(graph.edges(data=True), key=lambda x: (id_map[x[0]], id_map[x[1]])):
            f.write(f"{id_map[a]}\t{id_map[b]}\t{int(data.get('weight', 1))}\n")

    items = []
    for term in ordered:
        row = node_lookup[term]
        x, y = positions.get(term, (0.0, 0.0))
        scores = {}
        if pd.notna(row.get("avg_publication_year")):
            scores["Avg. pub. year"] = float(row["avg_publication_year"])
        items.append({
            "id": id_map[term], "label": term, "x": float(x), "y": float(y),
            "cluster": int(row["cluster"]),
            "weights": {"Occurrences": int(row["occurrences"]), "Links": int(row["links"]), "Total link strength": int(row["total_link_strength"])},
            "scores": scores,
        })
    links = [{"source_id": id_map[a], "target_id": id_map[b], "strength": float(data.get("weight", 1))}
             for a, b, data in graph.edges(data=True)]
    cluster_ids = sorted({int(row["cluster"]) for row in node_lookup.values()})
    clusters = [{"cluster": cid, "label": _cluster_titles(graph, nodes).get(cid, f"Cluster {cid}")} for cid in cluster_ids]
    payload = {
        "network": {"items": items, "links": links, "clusters": clusters},
        "config": {"parameters": {"largest_component": False, "scale": 1.0, "curved_links": True}},
        "info": {"title": "SciMap-Agent keyword co-occurrence network", "description": "Generated from document-level keyword co-occurrence. Display layout uses ForceAtlas2 with compact component packing (or spring-layout fallback); visualization headings are derived from the highest-frequency terms in each detected cluster."},
    }
    (out_dir / "vosviewer_network.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _plot_density(graph: nx.Graph, positions: dict, output: Path, dpi: int = 400) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(14, 9.5), constrained_layout=False)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_axis_off()
    if len(positions) >= 2:
        xy = np.array([positions[n] for n in positions])
        x_min, y_min = xy.min(axis=0) - 0.35
        x_max, y_max = xy.max(axis=0) + 0.35
        hist, _, _ = np.histogram2d(xy[:, 0], xy[:, 1], bins=200,
                                    range=[[x_min, x_max], [y_min, y_max]],
                                    weights=[graph.nodes[n].get("occurrences", 1) for n in positions])
        smooth = gaussian_filter(hist, sigma=6)
        ax.imshow(smooth.T, origin="lower", extent=[x_min, x_max, y_min, y_max],
                  cmap="magma", aspect="auto", alpha=0.95)
        ax.scatter(xy[:, 0], xy[:, 1], s=24, c="white", alpha=0.68,
                   linewidths=0.55, edgecolors="#4A4A4A")
    else:
        ax.text(0.5, 0.5, "Insufficient nodes for density map", ha="center", va="center")
    fig.subplots_adjust(left=0.03,right=0.97,bottom=0.04,top=0.96)
    fig.savefig(output, dpi=dpi, bbox_inches="tight", facecolor="white", pad_inches=0.12)
    fig.savefig(output.with_suffix(".svg"), bbox_inches="tight", facecolor="white", pad_inches=0.12)
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight", facecolor="white", pad_inches=0.12)
    plt.close(fig)


def export_visuals(graph: nx.Graph, nodes: pd.DataFrame, out_dir: str | Path,
                   max_labels: int | None = None, dpi: int = 400) -> dict[str, str]:
    out_dir = Path(out_dir)
    figures = out_dir / "figures"
    tables = out_dir / "tables"
    vos = out_dir / "vosviewer"
    figures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)

    nodes.to_csv(tables / "keyword_nodes.csv", index=False, encoding="utf-8-sig")
    edge_rows = [{"source": a, "target": b, "weight": d.get("weight", 1)} for a, b, d in graph.edges(data=True)]
    pd.DataFrame(edge_rows, columns=["source", "target", "weight"]).to_csv(tables / "keyword_edges.csv", index=False, encoding="utf-8-sig")

    cluster_pos = _draw_network(graph, nodes, figures / "keyword_network.png", mode="cluster", max_labels=max_labels, dpi=dpi)
    _draw_network(graph, nodes, figures / "keyword_overlay.png", mode="overlay", max_labels=max_labels, dpi=dpi)
    _plot_density(graph, cluster_pos, figures / "keyword_density.png", dpi=dpi)
    _export_vosviewer(graph, nodes, cluster_pos, vos)

    style = {
        "name": "journal-cluster",
        "layout": "ForceAtlas2 with compact component packing (spring-layout fallback)",
        "edges": "curved quadratic Bezier paths; within-cluster color and muted cross-cluster tint",
        "clusters": "soft elliptical cluster boundaries with dashed outlines and translucent fills",
        "labels": "automatic importance ranking and display-space collision relaxation",
        "cluster_headings": "automatically derived from the two highest-frequency non-overlapping terms in each cluster",
        "vector_text": "SVG and PDF retain editable Times-style text where supported by installed fonts",
        "typography": "Times New Roman preferred for English text and numerals; CJK fallback is used only when required",
        "output_resolution": "600 dpi PNG plus PDF and SVG by default",
    }
    (figures / "visual_style.json").write_text(json.dumps(style, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"figures": str(figures), "tables": str(tables), "vosviewer": str(vos)}
