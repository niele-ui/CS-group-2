import folium
import pandas as pd
from geopy.distance import geodesic

# Load the source data before building the lookup and calculating distances.
substations = pd.read_csv('substations.csv')
lines = pd.read_csv('lines.csv')

# Create substation lookup
sub_lookup = substations.set_index('Substation ID')

# Recompute line distances using the geodesic formula
def recompute_distance(row):
    src = sub_lookup.loc[row['Source Substation ID']]
    dst = sub_lookup.loc[row['Destination Substation ID']]
    
    return geodesic(
        (src['Latitude'], src['Longitude']),
        (dst['Latitude'], dst['Longitude'])
    ).km

# Calculate distances
lines['Recomputed Distance (km)'] = lines.apply(recompute_distance, axis=1)

# Calculate difference
lines['Distance Difference (km)'] = (
    lines['Length (km)'] - lines['Recomputed Distance (km)']
)

print(
    lines[
        [
            'Line ID',
            'Length (km)',
            'Recomputed Distance (km)',
            'Distance Difference (km)'
        ]
    ]
)

# Categorize lines by length
def categorize_length(km):
    if km < 20:
        return 'Short'
    elif km < 60:
        return 'Medium'
    return 'Long'

lines['Length Category'] = lines['Length (km)'].apply(categorize_length)

print("\nLine length category counts:")
print(lines['Length Category'].value_counts())

# Build the interactive map
m = folium.Map(location=[7.9, -1.0], zoom_start=6)

voltage_colors = {
    11: 'green',
    33: 'blue',
    69: 'orange',
    161: 'red',
    330: 'purple'
}

# Add substations
for idx, sub in substations.iterrows():
    folium.CircleMarker(
        location=[sub['Latitude'], sub['Longitude']],
        radius=5,
        popup=f"{sub['Name']} ({sub['Voltage (kV)']} kV, {sub['Region']})",
        color=voltage_colors.get(sub['Voltage (kV)'], 'gray'),
        fill=True,
        fill_opacity=0.7
    ).add_to(m)

# Add transmission lines
for idx, line in lines.iterrows():
    try:
        src = sub_lookup.loc[line['Source Substation ID']]
        dst = sub_lookup.loc[line['Destination Substation ID']]

        folium.PolyLine(
            locations=[
                [src['Latitude'], src['Longitude']],
                [dst['Latitude'], dst['Longitude']]
            ],
            weight=2,
            color='gray',
            opacity=0.6
        ).add_to(m)

    except KeyError:
        continue

# Save map
m.save('substation_map.html')

print("Map saved to substation_map.html")

# Substation density by region
print("\nSubstation density by region:")
print(substations['Region'].value_counts())