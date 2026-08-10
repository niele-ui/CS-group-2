# Regional and Geospatial Analysis Report
**Task 2.2 — Geographic and Geospatial Analysis**
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

- Mean absolute difference: **13.26 km**
- Maximum absolute difference: **47.76 km**

The recorded lengths differ noticeably from the geodesic values. Downstream analysis in this report uses the recomputed geodesic distances, since they follow directly from the coordinates.

---

## 2. Regional connectivity and density

The network spans **18 regions** and **44 substations**.

**Greater Accra** carries the densest concentration of infrastructure, with
**6 substations**. This is consistent with it functioning as the
network's primary load centre in the generated data.

Per-region summary (full table in `regional_summary.csv`):

| Region | Substations | Total capacity (MVA) | Line endpoints |
|---|---|---|---|
| Greater Accra | 6 | 520.2 | 22 |
| Ashanti | 5 | 1099.6 | 15 |
| Western | 4 | 323.0 | 12 |
| Central | 4 | 316.2 | 12 |
| Eastern | 4 | 828.5 | 12 |
| Volta | 4 | 470.3 | 10 |
| Bono | 3 | 252.6 | 6 |
| Northern | 3 | 155.6 | 4 |
| Upper East | 2 | 520.7 | 5 |
| Benin | 1 | 487.6 | 1 |

### Inter-regional and cross-border links

- **16 of 55 lines** (29%) connect substations in different regions; the remaining 39 are intra-regional. The network is therefore weighted toward local distribution, with a smaller backbone of inter-regional links carrying power between regions. Those inter-regional lines are structurally the most important, since comparatively few of them tie the regions together.
- **4 lines** cross an international border, representing the network's West African Power Pool (WAPP) interconnection points in this dataset.

---

## 3. Distance analysis

Lines were categorised by geodesic length:

| Category | Count |
|---|---|
| Medium (50-150 km) | 27 |
| Short (<=50 km) | 19 |
| Long (>150 km) | 9 |

The **Medium (50-150 km)** category dominates. The mix of short and long runs matters
operationally: long transmission runs carry higher losses and are more exposed
to weather and vegetation faults, so a network weighted toward long lines
implies a heavier maintenance burden per unit of delivered power.

Full per-line detail is in `line_distance_categories.csv`, and the distribution
is plotted in `distance_distribution.png`.

---

## 4. Geographic clustering

K-means clustering on substation coordinates (5 clusters)
groups the network into distinct geographic pockets:

| Cluster | Substations | Total capacity (MVA) | Regions covered |
|---|---|---|---|
| 0 | 8 | 1305.4 | Burkina Faso, Burkina Faso border, Northern, Upper East, Upper West |
| 1 | 16 | 2317.9 | Ashanti, Bono, Central, Cote d'Ivoire, Cote d'Ivoire border, Western |
| 2 | 1 | 251.6 | Guinea |
| 3 | 13 | 1581.1 | Central, Eastern, Greater Accra, Volta |
| 4 | 6 | 1490.1 | Benin, Togo, Togo border, Volta |

**Cluster 1** holds the largest share of installed
capacity, marking it as the network's centre of gravity. Concentration of this
kind is a double-edged property: it is efficient to serve dense demand from a
tight cluster of high-capacity assets, but it also means a disturbance in that
cluster propagates widely. This links directly to the N-1 contingency work in
Task 2.1 and Task 5 — the clusters identified here are the natural candidates
to test first.

See `geographic_clustering.png`.

---

## 5. Coverage gaps

The three regions with the fewest substations in this dataset are:

- **Burkina Faso** — 1 substation(s), 445.9 MVA total capacity
- **Togo** — 1 substation(s), 120.2 MVA total capacity
- **Burkina Faso border** — 1 substation(s), 156.1 MVA total capacity

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
