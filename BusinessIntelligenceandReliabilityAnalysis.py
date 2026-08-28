# Task 2.3 - Business Intelligence and Reliability Analysis
# Team Member 2 - Data Analyst

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# Load the datasets

utilities = pd.read_csv("utilities.csv")
substations = pd.read_csv("substations.csv")
lines = pd.read_csv("lines.csv")

# rename columns to make them easier to work with
utilities = utilities.rename(columns={"Utility ID": "Utility_ID", "Name": "Utility_Name"})
substations = substations.rename(columns={"Substation ID": "Substation_ID", "Name": "Substation_Name",
                                           "Voltage (kV)": "Voltage_kV", "Capacity (MVA)": "Capacity_MVA",
                                           "Commissioning Year": "Commissioning_Year"})
lines = lines.rename(columns={"Utility ID": "Utility_ID", "Source Substation ID": "From_Substation_ID",
                               "Source Substation": "From_Substation", "Destination Substation ID": "To_Substation_ID",
                               "Destination Substation": "To_Substation", "Voltage (kV)": "Voltage_kV",
                               "Length (km)": "Length_km", "Capacity (MVA)": "Capacity_MVA"})

# add utility name to the lines table
lines = pd.merge(lines, utilities[["Utility_ID", "Utility_Name"]], on="Utility_ID", how="left")


def voltage_tier(v):
    if v >= 161:
        return "High"
    elif v == 69:
        return "Medium"
    else:
        return "Low"


lines["Voltage_Tier"] = lines["Voltage_kV"].apply(voltage_tier)


# ------------------------------------------------------------
# Utility footprint
# ------------------------------------------------------------

print("=" * 60)
print("UTILITY FOOTPRINT")
print("=" * 60)

lines_per_utility = lines.groupby("Utility_Name").size().sort_values(ascending=False)
print("\nLines per utility")
print(lines_per_utility)

plt.figure(figsize=(10, 6))
sns.barplot(x=lines_per_utility.values, y=lines_per_utility.index)
plt.title("Lines Operated by Utility")
plt.xlabel("Number of Lines")
plt.tight_layout()
plt.savefig("lines_by_utility.png")
plt.show()

# find which substations each utility connects to (as source or destination)
source_links = lines[["Utility_Name", "From_Substation_ID"]].rename(columns={"From_Substation_ID": "Substation_ID"})
dest_links = lines[["Utility_Name", "To_Substation_ID"]].rename(columns={"To_Substation_ID": "Substation_ID"})
utility_links = pd.concat([source_links, dest_links])
utility_links = pd.merge(utility_links, substations[["Substation_ID", "Region", "Commissioning_Year"]],
                          on="Substation_ID", how="left")

substations_per_utility = utility_links.groupby("Utility_Name")["Substation_ID"].nunique().sort_values(ascending=False)
print("\nSubstations touched per utility")
print(substations_per_utility)

lines = pd.merge(lines, substations[["Substation_ID", "Region"]], left_on="From_Substation_ID",
                  right_on="Substation_ID", how="left")

print("\nLines per utility per region")
print(lines.groupby(["Utility_Name", "Region"]).size())

print("\nLines per utility per voltage tier")
print(lines.groupby(["Utility_Name", "Voltage_Tier"]).size())


# ------------------------------------------------------------
# Capacity by region and growth opportunities
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("CAPACITY AND GROWTH OPPORTUNITIES")
print("=" * 60)

ghana_substations = substations[substations["Country"] == "Ghana"]

substations_per_region = ghana_substations.groupby("Region").size().sort_values()
capacity_per_region = ghana_substations.groupby("Region")["Capacity_MVA"].sum().sort_values()

print("\nSubstations per region (fewest first)")
print(substations_per_region)
print("\nTotal capacity per region, MVA (lowest first)")
print(capacity_per_region)
print("\nRegions with the fewest substations are the growth-opportunity candidates:")
print(substations_per_region.head(3))

plt.figure(figsize=(10, 6))
sns.barplot(x=substations_per_region.values, y=substations_per_region.index)
plt.title("Substations by Region")
plt.xlabel("Substations")
plt.tight_layout()
plt.savefig("substations_by_region.png")
plt.show()

# capacity utilization ratio - connected line capacity vs a substation's own rated capacity
capacity_from = lines.groupby("From_Substation_ID")["Capacity_MVA"].sum()
capacity_to = lines.groupby("To_Substation_ID")["Capacity_MVA"].sum()
connected_capacity = capacity_from.add(capacity_to, fill_value=0)

substations["Connected_Capacity"] = substations["Substation_ID"].map(connected_capacity).fillna(0)
substations["Utilization_Ratio"] = substations["Connected_Capacity"] / substations["Capacity_MVA"]

top_utilization = substations.sort_values("Utilization_Ratio", ascending=False).head(10)
print("\nTop 10 substations by utilization ratio (upgrade candidates)")
print(top_utilization[["Substation_Name", "Region", "Capacity_MVA", "Connected_Capacity", "Utilization_Ratio"]])

plt.figure(figsize=(10, 6))
sns.barplot(data=top_utilization, x="Utilization_Ratio", y="Substation_Name")
plt.title("Top 10 Substations by Capacity Utilization Ratio")
plt.tight_layout()
plt.savefig("upgrade_candidates.png")
plt.show()


# ------------------------------------------------------------
# Technical loss proxy
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("TECHNICAL LOSS PROXY")
print("=" * 60)

# simple proxy - longer lines and lower voltage mean more relative loss
lines["Loss_Proxy"] = lines["Length_km"] / lines["Voltage_kV"]

loss_by_voltage = lines.groupby("Voltage_kV")["Loss_Proxy"].mean()
print("\nAverage loss proxy by voltage level")
print(loss_by_voltage)

worst_lines = lines.sort_values("Loss_Proxy", ascending=False).head(10)
print("\nTop 10 lines with the highest loss proxy")
print(worst_lines[["From_Substation", "To_Substation", "Voltage_kV", "Length_km", "Loss_Proxy"]])

plt.figure(figsize=(8, 5))
sns.barplot(x=loss_by_voltage.index.astype(str), y=loss_by_voltage.values)
plt.title("Average Loss Proxy by Voltage Level")
plt.xlabel("Voltage (kV)")
plt.tight_layout()
plt.savefig("loss_proxy.png")
plt.show()


# ------------------------------------------------------------
# Asset age
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("ASSET AGE")
print("=" * 60)

substations["Age_Years"] = 2026 - substations["Commissioning_Year"]

bins = [1960, 1970, 1980, 1990, 2000, 2010, 2020, 2030]
labels = ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
substations["Decade"] = pd.cut(substations["Commissioning_Year"], bins=bins, labels=labels, right=False)

age_counts = substations["Decade"].value_counts().sort_index()
print("\nSubstations commissioned by decade")
print(age_counts)

plt.figure(figsize=(10, 6))
plt.bar(age_counts.index.astype(str), age_counts.values)
plt.title("Substations Commissioned by Decade")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig("age_distribution.png")
plt.show()

avg_year_by_utility = utility_links.groupby("Utility_Name")["Commissioning_Year"].mean().sort_values()
print("\nAverage commissioning year by utility (smaller number = older fleet)")
print(avg_year_by_utility)

median_year = substations["Commissioning_Year"].median()
older_half = substations[substations["Commissioning_Year"] < median_year]
newer_half = substations[substations["Commissioning_Year"] >= median_year]

print("\nOlder half average capacity (MVA):", round(older_half["Capacity_MVA"].mean(), 1))
print("Newer half average capacity (MVA):", round(newer_half["Capacity_MVA"].mean(), 1))
print("Older half % active:", round((older_half["Status"] == "Active").mean() * 100, 1))
print("Newer half % active:", round((newer_half["Status"] == "Active").mean() * 100, 1))


# ------------------------------------------------------------
# Maintenance reliability
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("MAINTENANCE RELIABILITY")
print("=" * 60)

maintenance_lines = lines[lines["Status"] == "Under Maintenance"]
print("\nLines currently under maintenance")
print(maintenance_lines[["From_Substation", "To_Substation", "Utility_Name", "Length_km"]])

lines_total_by_utility = lines.groupby("Utility_Name").size()
maintenance_by_utility = maintenance_lines.groupby("Utility_Name").size()
maintenance_percent = (maintenance_by_utility / lines_total_by_utility * 100).fillna(0).sort_values(ascending=False)
print("\n% of lines under maintenance, by utility")
print(maintenance_percent)

plt.figure(figsize=(10, 6))
sns.barplot(x=maintenance_percent.values, y=maintenance_percent.index)
plt.title("% of Lines Under Maintenance by Utility")
plt.xlabel("% Under Maintenance")
plt.tight_layout()
plt.savefig("maintenance_by_utility.png")
plt.show()


# ------------------------------------------------------------
# Capacity concentration
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("CAPACITY CONCENTRATION")
print("=" * 60)

top10_capacity = substations.sort_values("Capacity_MVA", ascending=False).head(10)
top10_share = top10_capacity["Capacity_MVA"].sum() / substations["Capacity_MVA"].sum() * 100

print("\nTop 10 substations by installed capacity")
print(top10_capacity[["Substation_Name", "Region", "Capacity_MVA"]])
print("\nThese 10 substations hold", round(top10_share, 1), "% of total installed capacity")

plt.figure(figsize=(10, 6))
sns.barplot(data=top10_capacity, x="Capacity_MVA", y="Substation_Name")
plt.title("Top 10 Substations by Installed Capacity")
plt.tight_layout()
plt.savefig("capacity_concentration.png")
plt.show()


# ------------------------------------------------------------
# Reliability risk scores
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("RELIABILITY RISK SCORES")
print("=" * 60)

# simple point-based risk score for lines
lines["Risk_Score"] = 0
lines.loc[lines["Status"] == "Under Maintenance", "Risk_Score"] += 2
lines.loc[lines["Length_km"] > 200, "Risk_Score"] += 1

top_risk_lines = lines.sort_values("Risk_Score", ascending=False).head(10)
print("\nTop 10 highest-risk lines")
print(top_risk_lines[["From_Substation", "To_Substation", "Length_km", "Status", "Risk_Score"]])

# how many lines connect to each substation
connections_from = lines["From_Substation_ID"].value_counts()
connections_to = lines["To_Substation_ID"].value_counts()
substations["Connections"] = substations["Substation_ID"].map(
    connections_from.add(connections_to, fill_value=0)).fillna(0)

# simple point-based criticality score for substations
substations["Criticality_Score"] = 0
substations.loc[substations["Connections"] >= 4, "Criticality_Score"] += 2
substations.loc[substations["Age_Years"] >= 40, "Criticality_Score"] += 1

top_critical = substations.sort_values("Criticality_Score", ascending=False).head(10)
print("\nTop 10 most critical substations")
print(top_critical[["Substation_Name", "Region", "Connections", "Age_Years", "Criticality_Score"]])

plt.figure(figsize=(10, 6))
sns.barplot(data=top_critical, x="Criticality_Score", y="Substation_Name")
plt.title("Top 10 Most Critical Substations")
plt.tight_layout()
plt.savefig("critical_substations.png")
plt.show()


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("KEY FINDINGS")
print("=" * 60)

print("""
1. Ghana Grid Company operates the most lines and reaches the most substations.

2. A handful of substations have connected line capacity far above their own
   rated capacity - these are the upgrade candidates.

3. Regions with fewer substations, like Upper West and Northern, are the
   clearest growth opportunities.

4. Low voltage lines have a much higher loss proxy than high voltage lines.

5. A small number of substations hold a large share of total capacity.

6. Very few lines are currently under maintenance.
""")

print("ANALYSIS COMPLETE.")
