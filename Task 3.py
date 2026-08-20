# Advanced EDA - National Electricity Grid Network Analysis
# Team Member 2
#
# This program creates:
# 1. Voltage level distribution chart
# 2. Regional connectivity heatmap
# 3. Capacity utilisation analysis


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Make a folder for the graphs
os.makedirs("figures", exist_ok=True)

# Set the style for the graphs
sns.set_theme(style="whitegrid")



# 1. LOAD THE DATA


substations = pd.read_csv("substations.csv")
lines = pd.read_csv("lines.csv")
utilities = pd.read_csv("utilities.csv")

substations.columns = (
    substations.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("(", "")
    .str.replace(")", "")
)

lines.columns = (
    lines.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("(", "")
    .str.replace(")", "")
)

utilities.columns = (
    utilities.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("(", "")
    .str.replace(")", "")
)

print("Substations:", substations.shape)
print("Lines:", lines.shape)
print("Utilities:", utilities.shape)

summary = []


def add_summary(text):
    print(text)
    summary.append(text)


add_summary("=" * 60)
add_summary("NATIONAL ELECTRICITY GRID - EDA SUMMARY")
add_summary("=" * 60)



# 2. VOLTAGE LEVEL DISTRIBUTION



voltage_count = substations["voltage_kv"].value_counts().sort_index()

voltage_capacity = (
    substations.groupby("voltage_kv")["capacity_mva"]
    .sum()
    .sort_index()
)

add_summary("\n--- Voltage Level Distribution ---")

for voltage in voltage_count.index:
    add_summary(
        f"{voltage} kV: {voltage_count[voltage]} substations | "
        f"{voltage_capacity[voltage]:.1f} MVA total capacity"
    )


# Create two graphs
fig, ax = plt.subplots(1, 2, figsize=(13, 5))


# Graph 1: Number of substations by voltage
voltage_type = pd.crosstab(
    substations["voltage_kv"],
    substations["type"]
)

voltage_type = voltage_type.sort_index()

voltage_type.plot(
    kind="bar",
    stacked=True,
    ax=ax[0]
)

ax[0].set_title("Substations by Voltage Level")
ax[0].set_xlabel("Voltage (kV)")
ax[0].set_ylabel("Number of Substations")
ax[0].tick_params(axis="x", rotation=0)
ax[0].legend(title="Type")


# Graph 2: Capacity by voltage
bars = ax[1].bar(
    voltage_capacity.index.astype(str),
    voltage_capacity.values
)

ax[1].set_title("Total Capacity by Voltage Level")
ax[1].set_xlabel("Voltage (kV)")
ax[1].set_ylabel("Capacity (MVA)")


for bar in bars:
    height = bar.get_height()
    ax[1].text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f"{height:.0f}",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(
    "figures/01_voltage_distribution.png",
    dpi=150
)

plt.close()

add_summary("Saved: figures/01_voltage_distribution.png")



# 3. REGIONAL CONNECTIVITY


substation_region = substations.set_index(
    "substation_id"
)["region"]


lines["source_region"] = lines["source_substation_id"].map(
    substation_region
)

lines["destination_region"] = lines[
    "destination_substation_id"
].map(substation_region)


lines = lines.dropna(
    subset=["source_region", "destination_region"]
)


regions = sorted(
    set(lines["source_region"]) |
    set(lines["destination_region"])
)


connection_table = pd.DataFrame(
    0,
    index=regions,
    columns=regions
)


for _, row in lines.iterrows():

    source = row["source_region"]
    destination = row["destination_region"]

    connection_table.loc[source, destination] += 1

    
    if source != destination:
        connection_table.loc[destination, source] += 1


add_summary("\n--- Regional Connectivity ---")


region_total = (
    connection_table.sum(axis=1)
    - np.diag(connection_table)
)

for region in region_total.sort_values(
    ascending=False
).index:

    add_summary(
        f"{region}: {region_total[region]} connections"
    )



most_connected = region_total.idxmax()
least_connected = region_total.idxmin()

add_summary(
    f"\nMost connected region: {most_connected} "
    f"({region_total[most_connected]} connections)"
)

add_summary(
    f"Least connected region: {least_connected} "
    f"({region_total[least_connected]} connections)"
)



plt.figure(figsize=(9, 7))

sns.heatmap(
    connection_table,
    annot=True,
    fmt="d",
    cmap="YlOrRd"
)

plt.title("Regional Connectivity Heatmap")
plt.xlabel("Region")
plt.ylabel("Region")

plt.xticks(rotation=45, ha="right")

plt.tight_layout()

plt.savefig(
    "figures/02_regional_connectivity_heatmap.png",
    dpi=150
)

plt.close()

add_summary(
    "Saved: figures/02_regional_connectivity_heatmap.png"
)



# 4. CAPACITY UTILISATION




source_lines = lines[
    ["source_substation_id", "capacity_mva"]
].rename(
    columns={
        "source_substation_id": "substation_id"
    }
)

destination_lines = lines[
    ["destination_substation_id", "capacity_mva"]
].rename(
    columns={
        "destination_substation_id": "substation_id"
    }
)


all_lines = pd.concat(
    [source_lines, destination_lines]
)


line_capacity = (
    all_lines.groupby("substation_id")["capacity_mva"]
    .sum()
)


utilisation = substations.set_index(
    "substation_id"
).copy()

utilisation["line_capacity"] = (
    line_capacity.fillna(0)
)

# Calculate utilisation ratio
utilisation["utilisation_ratio"] = (
    utilisation["line_capacity"] /
    utilisation["capacity_mva"]
)


utilisation = utilisation[
    utilisation["line_capacity"] > 0
]


add_summary("\n--- Capacity Utilisation ---")

add_summary(
    f"Substations with lines: {len(utilisation)}"
)

add_summary(
    f"Average utilisation ratio: "
    f"{utilisation['utilisation_ratio'].mean():.2f}"
)

add_summary(
    f"Median utilisation ratio: "
    f"{utilisation['utilisation_ratio'].median():.2f}"
)



top5 = utilisation.sort_values(
    "utilisation_ratio",
    ascending=False
).head(5)

add_summary("\nTop 5 highest utilisation substations:")

for name, row in top5.iterrows():

    add_summary(
        f"{row['name']} - "
        f"{row['region']} - "
        f"ratio: {row['utilisation_ratio']:.2f}"
    )



bottom5 = utilisation.sort_values(
    "utilisation_ratio"
).head(5)

add_summary("\nBottom 5 lowest utilisation substations:")

for name, row in bottom5.iterrows():

    add_summary(
        f"{row['name']} - "
        f"{row['region']} - "
        f"ratio: {row['utilisation_ratio']:.2f}"
    )



# 5. CREATE CAPACITY GRAPHS


fig, ax = plt.subplots(1, 2, figsize=(14, 6))


# Graph 1: Substation capacity vs line capacity
for substation_type, data in utilisation.groupby("type"):

    ax[0].scatter(
        data["capacity_mva"],
        data["line_capacity"],
        label=substation_type,
        alpha=0.7
    )


# Add a 1:1 line
maximum = max(
    utilisation["capacity_mva"].max(),
    utilisation["line_capacity"].max()
)

ax[0].plot(
    [0, maximum],
    [0, maximum],
    "k--",
    label="1:1 line"
)

ax[0].set_xlabel("Substation Capacity (MVA)")
ax[0].set_ylabel("Connected Line Capacity (MVA)")
ax[0].set_title("Substation Capacity vs Line Capacity")
ax[0].legend(fontsize=8)


# Graph 2: Utilisation ratios
ax[1].hist(
    utilisation["utilisation_ratio"],
    bins=15,
    edgecolor="white"
)

ax[1].axvline(
    1.0,
    linestyle="--",
    label="Ratio = 1"
)

ax[1].set_xlabel(
    "Utilisation Ratio"
)

ax[1].set_ylabel(
    "Number of Substations"
)

ax[1].set_title(
    "Capacity Utilisation Ratios"
)

ax[1].legend()


plt.tight_layout()

plt.savefig(
    "figures/03_capacity_utilisation.png",
    dpi=150
)

plt.close()

add_summary(
    "Saved: figures/03_capacity_utilisation.png"
)



# 6. SAVE THE SUMMARY


with open("eda_summary.txt", "w") as file:

    file.write(
        "\n".join(summary)
    )

print("\nAll graphs and the summary file have been created.")