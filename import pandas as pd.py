import pandas as pd

# Utility footprint: substations and lines per utility, by region
lines_with_utility = pd.read_csv('merged_lines.csv')

utility_footprint = (
    lines_with_utility
    .groupby('Code')
    .agg(
        Lines_Operated=('Line ID', 'count'),
        Regions_Covered=('Region_source', 'nunique')
    )
    .sort_values('Lines_Operated', ascending=False)
)

print("Utility footprint:")
print(utility_footprint)


# Capacity utilization — flag lines that look under/over-provisioned
# relative to voltage tier
avg_capacity_by_voltage = (
    lines.groupby('Voltage (kV)')['Capacity (MVA)']
    .mean()
)

lines['Capacity vs Voltage Avg'] = lines.apply(
    lambda r: (
        r['Capacity (MVA)']
        - avg_capacity_by_voltage[r['Voltage (kV)']]
    ),
    axis=1
)

upgrade_candidates = lines[
    lines['Capacity vs Voltage Avg']
    < -avg_capacity_by_voltage.mean()
]

print(
    f"\n{len(upgrade_candidates)} lines flagged "
    "as potential upgrade candidates"
)


# Simple technical-loss proxy:
# longer + lower-voltage lines have higher apparent loss risk
lines['Loss Proxy'] = (
    lines['Length (km)'] / lines['Voltage (kV)']
)

print("\nTop 10 lines by loss proxy (highest apparent loss risk):")

print(
    lines.nlargest(10, 'Loss Proxy')[
        [
            'Line ID',
            'Length (km)',
            'Voltage (kV)',
            'Loss Proxy'
        ]
    ]
)


# Asset age profile
substations['Age'] = (
    2026 - substations['Commissioning Year']
)

print("\nSubstation age summary:")
print(substations['Age'].describe())


# Reliability proxy:
# % of lines under maintenance, by region
maintenance_by_region = (
    lines_with_utility
    .groupby('Region_source')['Status']
    .apply(
        lambda s: (s == 'Under Maintenance').mean() * 100
    )
    .sort_values(ascending=False)
)

print("\n% of lines under maintenance, by region:")
print(maintenance_by_region)


# Capacity concentration risk:
# What share of total capacity sits in the top 10% of substations?
sorted_capacity = (
    substations['Capacity (MVA)']
    .sort_values(ascending=False)
)

top_10pct_count = max(
    1,
    int(len(sorted_capacity) * 0.10)
)

concentration = (
    sorted_capacity.head(top_10pct_count).sum()
    / sorted_capacity.sum()
    * 100
)

print(
    f"\nTop 10% of substations hold "
    f"{concentration:.1f}% of total capacity"
)