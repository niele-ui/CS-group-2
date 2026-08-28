# Task 1.2 - Exploratory Data Analysis (EDA)
# Team Member 2 - Data Analyst

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# Load the datasets

utilities = pd.read_csv("utilities.csv")
substations = pd.read_csv("substations.csv")
lines = pd.read_csv("lines.csv")


# Basic information

print("=" * 60)
print("DATASET OVERVIEW")
print("=" * 60)

print("\nUtilities Dataset")
print("Shape:", utilities.shape)
utilities.info()

print("\nSubstations Dataset")
print("Shape:", substations.shape)
substations.info()

print("\nLines Dataset")
print("Shape:", lines.shape)
lines.info()


# Missing values

print("\n" + "=" * 60)
print("MISSING VALUES")
print("=" * 60)

print("\nUtilities")
print(utilities.isnull().sum())

print("\nSubstations")
print(substations.isnull().sum())

print("\nLines")
print(lines.isnull().sum())


# Duplicate records

print("\n" + "=" * 60)
print("DUPLICATES")
print("=" * 60)

print("Utilities:", utilities.duplicated().sum())
print("Substations:", substations.duplicated().sum())
print("Lines:", lines.duplicated().sum())


# Descriptive statistics

print("\n" + "=" * 60)
print("DESCRIPTIVE STATISTICS")
print("=" * 60)

print("\nUtilities")
print(utilities.describe())

print("\nSubstations")
print(substations.describe())

print("\nTransmission Lines")
print(lines.describe())


# Frequency distributions

print("\n" + "=" * 60)
print("FREQUENCY DISTRIBUTIONS")
print("=" * 60)


def frequency_table(df, name):
    print("\n------", name, "------")

    columns = df.select_dtypes(include="object").columns

    for column in columns:
        print("\n" + column)
        print(df[column].value_counts())


frequency_table(utilities, "Utilities")
frequency_table(substations, "Substations")
frequency_table(lines, "Lines")


# Top utilities by number of lines

print("\n" + "=" * 60)
print("TOP UTILITIES")
print("=" * 60)

utility_counts = lines.groupby("Utility_ID").size()
utility_counts = utility_counts.reset_index()
utility_counts.columns = ["Utility_ID", "Number_of_Lines"]

utility_counts = pd.merge(
    utility_counts,
    utilities,
    on="Utility_ID",
    how="left"
)

utility_counts = utility_counts.sort_values(
    by="Number_of_Lines",
    ascending=False
)

print(utility_counts)

plt.figure(figsize=(10, 6))
sns.barplot(
    data=utility_counts,
    x="Number_of_Lines",
    y="Utility_Name"
)
plt.title("Top Utilities by Number of Lines")
plt.tight_layout()
plt.savefig("top_utilities.png")
plt.show()


# Most connected substations

print("\n" + "=" * 60)
print("MOST CONNECTED SUBSTATIONS")
print("=" * 60)

from_counts = lines["From_Substation_ID"].value_counts()
to_counts = lines["To_Substation_ID"].value_counts()

connections = from_counts + to_counts
connections = connections.fillna(0)

connections = connections.reset_index()
connections.columns = ["Substation_ID", "Connections"]

connections = pd.merge(
    connections,
    substations,
    on="Substation_ID",
    how="left"
)

connections = connections.sort_values(
    by="Connections",
    ascending=False
)

print(connections.head(10))

plt.figure(figsize=(10, 6))
sns.barplot(
    data=connections.head(10),
    x="Connections",
    y="Substation_Name"
)
plt.title("Top 10 Most Connected Substations")
plt.tight_layout()
plt.savefig("connected_substations.png")
plt.show()


# Substations by region

print("\n" + "=" * 60)
print("SUBSTATIONS BY REGION")
print("=" * 60)

region_counts = substations["Region"].value_counts()

print(region_counts)

plt.figure(figsize=(10, 6))
sns.barplot(
    x=region_counts.values,
    y=region_counts.index
)
plt.title("Substations by Region")
plt.tight_layout()
plt.savefig("substations_region.png")
plt.show()


# Transmission lines by region

region_lines = pd.merge(
    lines,
    substations[["Substation_ID", "Region"]],
    left_on="From_Substation_ID",
    right_on="Substation_ID",
    how="left"
)

line_region_counts = region_lines["Region"].value_counts()

print("\nTransmission Lines by Region")
print(line_region_counts)

plt.figure(figsize=(10, 6))
sns.barplot(
    x=line_region_counts.values,
    y=line_region_counts.index
)
plt.title("Transmission Lines by Region")
plt.tight_layout()
plt.savefig("lines_region.png")
plt.show()


# Substation status

print("\n" + "=" * 60)
print("SUBSTATION STATUS")
print("=" * 60)

status_counts = substations["Status"].value_counts()

print(status_counts)

plt.figure(figsize=(6, 6))
status_counts.plot(
    kind="pie",
    autopct="%1.1f%%"
)
plt.ylabel("")
plt.title("Substation Status")
plt.tight_layout()
plt.savefig("status_distribution.png")
plt.show()


# Voltage level distribution

print("\n" + "=" * 60)
print("VOLTAGE DISTRIBUTION")
print("=" * 60)

voltage_counts = substations["Voltage_kV"].value_counts()
voltage_counts = voltage_counts.sort_index()

print(voltage_counts)

plt.figure(figsize=(8, 5))
sns.barplot(
    x=voltage_counts.index.astype(str),
    y=voltage_counts.values
)
plt.xlabel("Voltage (kV)")
plt.ylabel("Count")
plt.title("Voltage Level Distribution")
plt.tight_layout()
plt.savefig("voltage_distribution.png")
plt.show()


# Initial observations

print("\n" + "=" * 60)
print("INITIAL OBSERVATIONS")
print("=" * 60)

print("""
1. Some utility companies have more transmission lines than others.

2. A few substations connect to many other substations.

3. Most substations are active.

4. Some regions have more substations and transmission lines than other regions.

5. The 161 kV voltage level is the most common.

6. The lengths of transmission lines are different across the network.
""")

print("\nEDA COMPLETE.")
