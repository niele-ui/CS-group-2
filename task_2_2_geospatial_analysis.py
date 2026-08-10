"""
Task 2.2: Geographic and Geospatial Analysis
National Electricity Grid Network Analysis
CS 112 Final Course Project - Group 2

Objective: Analyse spatial patterns and geographic distribution of the
national electricity grid.

Deliverables produced by this script:
    1. grid_interactive_map.html      - multi-layer interactive Folium map
    2. regional_analysis_report.md    - regional connectivity write-up
    3. distance_distribution.png      - line length distribution analysis
    4. geographic_clustering.png      - substation clustering visualisation
    5. regional_summary.csv           - per-region density table
    6. line_distance_categories.csv   - lines categorised by length

Usage:
    python task_2_2_geospatial_analysis.py

Requires: pandas, numpy, matplotlib, folium, geopy
    pip install pandas numpy matplotlib folium geopy
"""

import os
import math
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")           # headless-safe backend
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap, MarkerCluster
from geopy.distance import geodesic

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = DATA_DIR

# Colour per nominal voltage level (kV)
VOLTAGE_COLOURS = {
    11:  "#2ecc71",   # green   - low voltage distribution
    33:  "#3498db",   # blue
    69:  "#f1c40f",   # yellow
    161: "#e67e22",   # orange
    330: "#e74c3c",   # red     - highest voltage transmission
}

# Line-length categories (km)
SHORT_MAX = 50
MEDIUM_MAX = 150


def load_data():
    """Load the three grid datasets.

    Prefers the cleaned outputs from Task 1.1 if present, otherwise
    falls back to the raw generated CSVs.
    """
    def pick(clean_name, raw_name):
        clean_path = os.path.join(DATA_DIR, clean_name)
        raw_path = os.path.join(DATA_DIR, raw_name)
        if os.path.exists(clean_path):
            print(f"  using {clean_name}")
            return pd.read_csv(clean_path)
        print(f"  using {raw_name}")
        return pd.read_csv(raw_path)

    print("Loading datasets...")
    utilities = pick("utilities_clean.csv", "utilities.csv")
    substations = pick("substations_clean.csv", "substations.csv")
    lines = pick("lines_clean.csv", "lines.csv")
    return utilities, substations, lines


# =====================================================================
# PART 1: Recompute / verify line distances with the geodesic formula
# =====================================================================
def compute_geodesic_distances(lines, substations):
    """Recompute every line's length from substation coordinates using
    the geodesic (WGS-84 ellipsoid) formula, and compare against the
    Length (km) value recorded in the dataset."""
    print("\n[1] Recomputing line distances using the geodesic formula...")

    coords = substations.set_index("Substation ID")[["Latitude", "Longitude"]]

    computed = []
    for _, row in lines.iterrows():
        src_id = row["Source Substation ID"]
        dst_id = row["Destination Substation ID"]
        if src_id in coords.index and dst_id in coords.index:
            src = tuple(coords.loc[src_id])
            dst = tuple(coords.loc[dst_id])
            computed.append(geodesic(src, dst).kilometers)
        else:
            computed.append(np.nan)

    lines = lines.copy()
    lines["Geodesic Length (km)"] = np.round(computed, 2)
    lines["Length Difference (km)"] = np.round(
        lines["Geodesic Length (km)"] - lines["Length (km)"], 2
    )

    valid = lines["Geodesic Length (km)"].notna()
    mean_abs_diff = lines.loc[valid, "Length Difference (km)"].abs().mean()
    max_abs_diff = lines.loc[valid, "Length Difference (km)"].abs().max()

    print(f"    Lines with computable geodesic distance: {valid.sum()}/{len(lines)}")
    print(f"    Mean absolute difference vs recorded length: {mean_abs_diff:.2f} km")
    print(f"    Max absolute difference vs recorded length:  {max_abs_diff:.2f} km")

    return lines, mean_abs_diff, max_abs_diff


# =====================================================================
# PART 2: Distance categorisation
# =====================================================================
def categorise_distances(lines):
    """Categorise lines as short / medium / long transmission runs."""
    print("\n[2] Categorising lines by length...")

    def category(km):
        if pd.isna(km):
            return "Unknown"
        if km <= SHORT_MAX:
            return f"Short (<={SHORT_MAX} km)"
        if km <= MEDIUM_MAX:
            return f"Medium ({SHORT_MAX}-{MEDIUM_MAX} km)"
        return f"Long (>{MEDIUM_MAX} km)"

    lines = lines.copy()
    lines["Distance Category"] = lines["Geodesic Length (km)"].apply(category)

    counts = lines["Distance Category"].value_counts()
    print(counts.to_string())

    lines[[
        "Line ID", "Source Substation", "Destination Substation",
        "Voltage (kV)", "Length (km)", "Geodesic Length (km)",
        "Distance Category",
    ]].to_csv(os.path.join(OUT_DIR, "line_distance_categories.csv"), index=False)

    return lines, counts


# =====================================================================
# PART 3: Regional density analysis
# =====================================================================
def regional_analysis(substations, lines):
    """Compare grid density across regions and identify coverage gaps."""
    print("\n[3] Analysing substation density by region...")

    # Substation counts and capacity per region
    regional = substations.groupby("Region").agg(
        substation_count=("Substation ID", "count"),
        total_capacity_mva=("Capacity (MVA)", "sum"),
        mean_capacity_mva=("Capacity (MVA)", "mean"),
        mean_voltage_kv=("Voltage (kV)", "mean"),
        max_voltage_kv=("Voltage (kV)", "max"),
    ).round(2)

    # Count lines touching each region (either endpoint)
    sub_region = substations.set_index("Substation ID")["Region"].to_dict()
    lines = lines.copy()
    lines["Source Region"] = lines["Source Substation ID"].map(sub_region)
    lines["Destination Region"] = lines["Destination Substation ID"].map(sub_region)

    source_counts = lines["Source Region"].value_counts()
    dest_counts = lines["Destination Region"].value_counts()
    line_counts = source_counts.add(dest_counts, fill_value=0)
    regional["line_endpoints"] = regional.index.map(line_counts).fillna(0).astype(int)

    # Geographic spread (bounding box area proxy) per region
    spread = substations.groupby("Region").agg(
        lat_min=("Latitude", "min"), lat_max=("Latitude", "max"),
        lon_min=("Longitude", "min"), lon_max=("Longitude", "max"),
    )
    # Rough km-square area of the region's substation bounding box
    spread["approx_area_km2"] = (
        (spread["lat_max"] - spread["lat_min"]) * 111.0
        * (spread["lon_max"] - spread["lon_min"]) * 111.0
        * np.cos(np.radians((spread["lat_max"] + spread["lat_min"]) / 2))
    ).abs().round(1)

    regional["approx_footprint_km2"] = spread["approx_area_km2"]
    regional["substations_per_1000km2"] = (
        regional["substation_count"] / regional["approx_footprint_km2"] * 1000
    ).replace([np.inf, -np.inf], np.nan).round(3)

    regional = regional.sort_values("substation_count", ascending=False)
    regional.to_csv(os.path.join(OUT_DIR, "regional_summary.csv"))

    print(regional[["substation_count", "total_capacity_mva", "line_endpoints"]].to_string())

    # Cross-border / inter-regional connectivity
    cross_regional = lines[
        lines["Source Region"] != lines["Destination Region"]
    ]
    print(f"\n    Inter-regional lines: {len(cross_regional)}/{len(lines)}")

    cross_border = pd.DataFrame()
    if "Country" in substations.columns:
        sub_country = substations.set_index("Substation ID")["Country"].to_dict()
        lines["Source Country"] = lines["Source Substation ID"].map(sub_country)
        lines["Destination Country"] = lines["Destination Substation ID"].map(sub_country)
        cross_border = lines[lines["Source Country"] != lines["Destination Country"]]
        print(f"    Cross-border (WAPP interconnection) lines: {len(cross_border)}")

    return regional, lines, cross_regional, cross_border


# =====================================================================
# PART 4: Substation clustering (high-capacity geographic clusters)
# =====================================================================
def cluster_substations(substations, n_clusters=5):
    """Simple k-means-style geographic clustering implemented with numpy
    so the script has no scikit-learn dependency."""
    print("\n[4] Identifying geographic clusters of substations...")

    subs = substations.dropna(subset=["Latitude", "Longitude"]).copy()
    points = subs[["Latitude", "Longitude"]].to_numpy()

    n_clusters = min(n_clusters, len(points))
    rng = np.random.default_rng(42)
    centroids = points[rng.choice(len(points), n_clusters, replace=False)].copy()

    labels = np.zeros(len(points), dtype=int)
    for _ in range(100):
        dists = np.linalg.norm(points[:, None, :] - centroids[None, :, :], axis=2)
        new_labels = dists.argmin(axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for k in range(n_clusters):
            if (labels == k).any():
                centroids[k] = points[labels == k].mean(axis=0)

    subs["Cluster"] = labels

    cluster_summary = subs.groupby("Cluster").agg(
        substations=("Substation ID", "count"),
        total_capacity_mva=("Capacity (MVA)", "sum"),
        mean_voltage_kv=("Voltage (kV)", "mean"),
        centre_lat=("Latitude", "mean"),
        centre_lon=("Longitude", "mean"),
        regions=("Region", lambda s: ", ".join(sorted(set(s)))),
    ).round(2)

    print(cluster_summary[["substations", "total_capacity_mva", "regions"]].to_string())
    return subs, cluster_summary


# =====================================================================
# PART 5: Static visualisations
# =====================================================================
def plot_distance_distribution(lines, counts):
    """Histogram + category bar chart of line lengths."""
    print("\n[5] Plotting distance distribution...")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    valid = lines["Geodesic Length (km)"].dropna()
    axes[0].hist(valid, bins=15, color="#3498db", edgecolor="white")
    axes[0].axvline(SHORT_MAX, color="#e67e22", linestyle="--", label=f"{SHORT_MAX} km")
    axes[0].axvline(MEDIUM_MAX, color="#e74c3c", linestyle="--", label=f"{MEDIUM_MAX} km")
    axes[0].set_title("Distribution of Transmission Line Lengths")
    axes[0].set_xlabel("Geodesic length (km)")
    axes[0].set_ylabel("Number of lines")
    axes[0].legend()

    order = [c for c in counts.index if c != "Unknown"]
    axes[1].bar(range(len(order)), [counts[c] for c in order],
                color=["#2ecc71", "#f1c40f", "#e74c3c"][:len(order)])
    axes[1].set_xticks(range(len(order)))
    axes[1].set_xticklabels(order, rotation=15, ha="right")
    axes[1].set_title("Lines by Distance Category")
    axes[1].set_ylabel("Number of lines")

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "distance_distribution.png"), dpi=150)
    plt.close()
    print("    Saved distance_distribution.png")


def plot_clusters(subs, cluster_summary):
    """Scatter plot of substations coloured by geographic cluster."""
    print("[6] Plotting geographic clustering...")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    palette = ["#e74c3c", "#3498db", "#2ecc71", "#f1c40f", "#9b59b6",
               "#1abc9c", "#e67e22", "#34495e"]

    for k in sorted(subs["Cluster"].unique()):
        grp = subs[subs["Cluster"] == k]
        axes[0].scatter(
            grp["Longitude"], grp["Latitude"],
            s=grp["Capacity (MVA)"].fillna(10) * 2,
            color=palette[k % len(palette)],
            alpha=0.7, edgecolors="white", label=f"Cluster {k}",
        )
    axes[0].scatter(
        cluster_summary["centre_lon"], cluster_summary["centre_lat"],
        marker="X", s=200, color="black", label="Cluster centre", zorder=5,
    )
    axes[0].set_title("Substation Geographic Clusters\n(marker size = capacity MVA)")
    axes[0].set_xlabel("Longitude")
    axes[0].set_ylabel("Latitude")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.2)

    # Capacity per cluster
    axes[1].bar(
        cluster_summary.index.astype(str),
        cluster_summary["total_capacity_mva"],
        color=[palette[k % len(palette)] for k in cluster_summary.index],
    )
    axes[1].set_title("Total Installed Capacity by Cluster")
    axes[1].set_xlabel("Cluster")
    axes[1].set_ylabel("Total capacity (MVA)")
    axes[1].grid(axis="y", alpha=0.2)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "geographic_clustering.png"), dpi=150)
    plt.close()
    print("    Saved geographic_clustering.png")


# =====================================================================
# PART 6: Interactive multi-layer Folium map
# =====================================================================
def build_interactive_map(substations, lines, utilities, subs_clustered):
    """Build the multi-layer interactive map deliverable."""
    print("[7] Building interactive multi-layer map...")

    centre = [substations["Latitude"].mean(), substations["Longitude"].mean()]
    fmap = folium.Map(location=centre, zoom_start=7, tiles="CartoDB positron")

    coords = substations.set_index("Substation ID")[["Latitude", "Longitude"]]

    # --- Layer 1: substations coloured by voltage level ---
    voltage_layer = folium.FeatureGroup(name="Substations by voltage", show=True)
    for _, sub in substations.iterrows():
        kv = sub.get("Voltage (kV)")
        colour = VOLTAGE_COLOURS.get(int(kv) if pd.notna(kv) else 0, "#7f8c8d")
        folium.CircleMarker(
            location=[sub["Latitude"], sub["Longitude"]],
            radius=4 + (float(sub.get("Capacity (MVA)") or 0) ** 0.5) / 3,
            color=colour, fill=True, fill_color=colour, fill_opacity=0.75, weight=1,
            popup=folium.Popup(
                f"<b>{sub['Name']}</b><br>"
                f"Region: {sub.get('Region', 'n/a')}<br>"
                f"Country: {sub.get('Country', 'n/a')}<br>"
                f"Voltage: {kv} kV<br>"
                f"Capacity: {sub.get('Capacity (MVA)', 'n/a')} MVA<br>"
                f"Type: {sub.get('Type', 'n/a')}<br>"
                f"Status: {sub.get('Status', 'n/a')}",
                max_width=280,
            ),
            tooltip=sub["Name"],
        ).add_to(voltage_layer)
    voltage_layer.add_to(fmap)

    # --- Layer 2: transmission lines coloured by voltage ---
    lines_layer = folium.FeatureGroup(name="Transmission lines", show=True)
    for _, ln in lines.iterrows():
        s_id, d_id = ln["Source Substation ID"], ln["Destination Substation ID"]
        if s_id not in coords.index or d_id not in coords.index:
            continue
        kv = ln.get("Voltage (kV)")
        colour = VOLTAGE_COLOURS.get(int(kv) if pd.notna(kv) else 0, "#7f8c8d")
        folium.PolyLine(
            locations=[list(coords.loc[s_id]), list(coords.loc[d_id])],
            color=colour,
            weight=1 + (float(kv or 0) / 150),
            opacity=0.6,
            dash_array="5,5" if ln.get("Status") != "Active" else None,
            popup=(
                f"<b>Line {ln['Line ID']}</b><br>"
                f"{ln['Source Substation']} &rarr; {ln['Destination Substation']}<br>"
                f"Voltage: {kv} kV<br>"
                f"Recorded length: {ln.get('Length (km)')} km<br>"
                f"Geodesic length: {ln.get('Geodesic Length (km)')} km<br>"
                f"Category: {ln.get('Distance Category', 'n/a')}<br>"
                f"Status: {ln.get('Status', 'n/a')}"
            ),
        ).add_to(lines_layer)
    lines_layer.add_to(fmap)

    # --- Layer 3: line-density heatmap ---
    heat_points = []
    for _, ln in lines.iterrows():
        s_id, d_id = ln["Source Substation ID"], ln["Destination Substation ID"]
        if s_id in coords.index and d_id in coords.index:
            s, d = coords.loc[s_id], coords.loc[d_id]
            # sample midpoint plus endpoints to weight corridors
            heat_points.append([s["Latitude"], s["Longitude"]])
            heat_points.append([d["Latitude"], d["Longitude"]])
            heat_points.append([(s["Latitude"] + d["Latitude"]) / 2,
                                (s["Longitude"] + d["Longitude"]) / 2])
    heat_layer = folium.FeatureGroup(name="Line-density heatmap", show=False)
    HeatMap(heat_points, radius=22, blur=18, min_opacity=0.3).add_to(heat_layer)
    heat_layer.add_to(fmap)

    # --- Layer 4: per-utility network maps ---
    util_names = utilities.set_index("Utility ID")["Alias"].to_dict() \
        if "Alias" in utilities.columns else {}
    for util_id, grp in lines.groupby("Utility ID"):
        alias = util_names.get(util_id, f"Utility {util_id}")
        ulayer = folium.FeatureGroup(name=f"Network: {alias}", show=False)
        for _, ln in grp.iterrows():
            s_id, d_id = ln["Source Substation ID"], ln["Destination Substation ID"]
            if s_id not in coords.index or d_id not in coords.index:
                continue
            folium.PolyLine(
                locations=[list(coords.loc[s_id]), list(coords.loc[d_id])],
                color="#8e44ad", weight=2.5, opacity=0.8,
                popup=f"{alias}: {ln['Source Substation']} &rarr; {ln['Destination Substation']}",
            ).add_to(ulayer)
        ulayer.add_to(fmap)

    # --- Layer 5: geographic clusters ---
    cluster_layer = folium.FeatureGroup(name="Geographic clusters", show=False)
    palette = ["#e74c3c", "#3498db", "#2ecc71", "#f1c40f", "#9b59b6",
               "#1abc9c", "#e67e22", "#34495e"]
    for _, sub in subs_clustered.iterrows():
        c = palette[int(sub["Cluster"]) % len(palette)]
        folium.CircleMarker(
            location=[sub["Latitude"], sub["Longitude"]],
            radius=6, color=c, fill=True, fill_color=c, fill_opacity=0.8, weight=1,
            popup=f"{sub['Name']}<br>Cluster {sub['Cluster']}",
        ).add_to(cluster_layer)
    cluster_layer.add_to(fmap)

    # --- Legend ---
    legend_rows = "".join(
        f'<div><span style="background:{c};width:12px;height:12px;'
        f'display:inline-block;margin-right:6px;border-radius:2px;"></span>{kv} kV</div>'
        for kv, c in sorted(VOLTAGE_COLOURS.items())
    )
    legend_html = f"""
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999;
                background: white; padding: 10px 14px; border: 1px solid #ccc;
                border-radius: 6px; font-family: sans-serif; font-size: 12px;
                box-shadow: 0 1px 4px rgba(0,0,0,.25);">
      <b>Voltage level</b>{legend_rows}
      <div style="margin-top:6px;color:#666;">Marker size &prop; capacity (MVA)</div>
      <div style="color:#666;">Synthetic data \u2014 CS 112 Group 2</div>
    </div>"""
    fmap.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl(collapsed=False).add_to(fmap)

    out_path = os.path.join(OUT_DIR, "grid_interactive_map.html")
    fmap.save(out_path)
    print(f"    Saved grid_interactive_map.html")
    return out_path


# =====================================================================
# PART 7: Regional analysis report
# =====================================================================
def write_regional_report(regional, counts, cross_regional, cross_border,
                          cluster_summary, mean_diff, max_diff, lines, substations):
    print("[8] Writing regional analysis report...")

    top_region = regional.index[0]
    top_count = regional.iloc[0]["substation_count"]
    least_served = regional.sort_values("substation_count").head(3)

    highest_capacity_cluster = cluster_summary["total_capacity_mva"].idxmax()

    md = f"""# Regional and Geospatial Analysis Report
**Task 2.2 \u2014 Geographic and Geospatial Analysis**
CS 112 Final Course Project, Group 2

> All figures below are derived from the project's synthetic dataset. They
> describe the generated network only and should not be read as claims about
> Ghana's actual electricity infrastructure.

---

## 1. Method

Line lengths were recomputed from substation coordinates using the geodesic
(WGS-84 ellipsoid) formula via `geopy.distance.geodesic`, rather than relying
on the `Length (km)` column supplied in the dataset. This gives an independent
check on the recorded values and a consistent basis for the distance analysis
that follows.

Comparing computed against recorded lengths:

- Mean absolute difference: **{mean_diff:.2f} km**
- Maximum absolute difference: **{max_diff:.2f} km**

{"The recorded lengths track the geodesic values closely, so either column can be used interchangeably in later analysis." if mean_diff < 5 else "The recorded lengths differ noticeably from the geodesic values. Downstream analysis in this report uses the recomputed geodesic distances, since they follow directly from the coordinates."}

---

## 2. Regional connectivity and density

The network spans **{len(regional)} regions** and **{len(substations)} substations**.

**{top_region}** carries the densest concentration of infrastructure, with
**{int(top_count)} substations**. This is consistent with it functioning as the
network's primary load centre in the generated data.

Per-region summary (full table in `regional_summary.csv`):

| Region | Substations | Total capacity (MVA) | Line endpoints |
|---|---|---|---|
"""
    for region, row in regional.head(10).iterrows():
        md += (f"| {region} | {int(row['substation_count'])} | "
               f"{row['total_capacity_mva']:.1f} | {int(row['line_endpoints'])} |\n")

    md += f"""
### Inter-regional and cross-border links

- **{len(cross_regional)} of {len(lines)} lines** ({len(cross_regional)/len(lines)*100:.0f}%) connect substations in different regions; the remaining {len(lines)-len(cross_regional)} are intra-regional. {"The network is therefore weighted toward local distribution, with a smaller backbone of inter-regional links carrying power between regions. Those inter-regional lines are structurally the most important, since comparatively few of them tie the regions together." if len(cross_regional)/len(lines) < 0.5 else "The majority of lines cross regional boundaries, indicating a network organised around long-haul transfer rather than local distribution."}
- **{len(cross_border)} lines** cross an international border, representing the network's West African Power Pool (WAPP) interconnection points in this dataset.

---

## 3. Distance analysis

Lines were categorised by geodesic length:

| Category | Count |
|---|---|
"""
    for cat, n in counts.items():
        md += f"| {cat} | {n} |\n"

    dominant = counts.idxmax()
    md += f"""
The **{dominant}** category dominates. The mix of short and long runs matters
operationally: long transmission runs carry higher losses and are more exposed
to weather and vegetation faults, so a network weighted toward long lines
implies a heavier maintenance burden per unit of delivered power.

Full per-line detail is in `line_distance_categories.csv`, and the distribution
is plotted in `distance_distribution.png`.

---

## 4. Geographic clustering

K-means clustering on substation coordinates ({len(cluster_summary)} clusters)
groups the network into distinct geographic pockets:

| Cluster | Substations | Total capacity (MVA) | Regions covered |
|---|---|---|---|
"""
    for k, row in cluster_summary.iterrows():
        md += (f"| {k} | {int(row['substations'])} | {row['total_capacity_mva']:.1f} | "
               f"{row['regions']} |\n")

    md += f"""
**Cluster {highest_capacity_cluster}** holds the largest share of installed
capacity, marking it as the network's centre of gravity. Concentration of this
kind is a double-edged property: it is efficient to serve dense demand from a
tight cluster of high-capacity assets, but it also means a disturbance in that
cluster propagates widely. This links directly to the N-1 contingency work in
Task 2.1 and Task 5 \u2014 the clusters identified here are the natural candidates
to test first.

See `geographic_clustering.png`.

---

## 5. Coverage gaps

The three regions with the fewest substations in this dataset are:

"""
    for region, row in least_served.iterrows():
        md += f"- **{region}** \u2014 {int(row['substation_count'])} substation(s), {row['total_capacity_mva']:.1f} MVA total capacity\n"

    md += f"""
These stand out as relatively thin coverage **within the generated network**.
An important caveat: substation count alone is a weak measure of whether an
area is underserved. A sparse region may simply have low demand, or a small
land area, or be served adequately from an adjacent region's assets. Drawing a
real conclusion about underservice would require population and demand data
that this dataset does not contain, so the gaps flagged here should be treated
as a starting point for investigation rather than a finding.

---

## 6. Deliverables produced

| File | Contents |
|---|---|
| `grid_interactive_map.html` | Multi-layer interactive map: substations by voltage, transmission lines, line-density heatmap, per-utility networks, geographic clusters |
| `regional_analysis_report.md` | This report |
| `distance_distribution.png` | Line-length histogram and category breakdown |
| `geographic_clustering.png` | Cluster scatter plot and capacity-by-cluster chart |
| `regional_summary.csv` | Per-region density and capacity table |
| `line_distance_categories.csv` | Every line with recomputed distance and category |

---

## 7. Limitations

1. The dataset is synthetic and seeded; results characterise the generated network, not Ghana's real grid.
2. Region footprint areas are approximated from substation bounding boxes, not true administrative boundaries, so the density-per-area figures are indicative only.
3. Clustering uses raw latitude/longitude in Euclidean space. Over Ghana's latitude range the distortion is small, but it is not a projected coordinate system.
4. Coverage-gap analysis lacks population and demand data, as noted in Section 5.
"""

    path = os.path.join(OUT_DIR, "regional_analysis_report.md")
    with open(path, "w") as f:
        f.write(md)
    print("    Saved regional_analysis_report.md")


# =====================================================================
def main():
    utilities, substations, lines = load_data()

    lines, mean_diff, max_diff = compute_geodesic_distances(lines, substations)
    lines, counts = categorise_distances(lines)
    regional, lines, cross_regional, cross_border = regional_analysis(substations, lines)
    subs_clustered, cluster_summary = cluster_substations(substations)

    plot_distance_distribution(lines, counts)
    plot_clusters(subs_clustered, cluster_summary)
    build_interactive_map(substations, lines, utilities, subs_clustered)
    write_regional_report(regional, counts, cross_regional, cross_border,
                          cluster_summary, mean_diff, max_diff, lines, substations)

    print("\n" + "=" * 60)
    print("Task 2.2 complete. Files written to:", OUT_DIR)
    for f in ["grid_interactive_map.html", "regional_analysis_report.md",
              "distance_distribution.png", "geographic_clustering.png",
              "regional_summary.csv", "line_distance_categories.csv"]:
        print("  -", f)


if __name__ == "__main__":
    main()
