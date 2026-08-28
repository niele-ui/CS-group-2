import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
utilities = pd.read_csv('utilities.csv')
substations = pd.read_csv('substations.csv')
lines = pd.read_csv('lines.csv')
# Build the graph — undirected, since AC power can flow either way along a line
G = nx.from_pandas_edgelist(
 lines, source='Source Substation', target='Destination Substation',
 edge_attr=['Length (km)', 'Voltage (kV)'], create_using=nx.Graph()
)
print(f"Number of nodes (substations): {G.number_of_nodes()}")
print(f"Number of edges (lines): {G.number_of_edges()}")
# Centrality measures
degree_centrality = nx.degree_centrality(G)
betweenness_centrality = nx.betweenness_centrality(G)
closeness_centrality = nx.closeness_centrality(G)
pagerank = nx.pagerank(G)
top_by_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
print("\nTop 10 Substations by Degree Centrality:")
for substation, centrality in top_by_degree:
 print(f"{substation}: {centrality:.4f}")
top_by_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
print("\nTop 10 Substations by Betweenness Centrality (critical intermediaries):")
for substation, centrality in top_by_betweenness:
 print(f"{substation}: {centrality:.4f}")
# Network diameter and average path length (only valid if the graph is fully connected)
if nx.is_connected(G):
 print(f"\nNetwork diameter: {nx.diameter(G)}")
 print(f"Average shortest path length: {nx.average_shortest_path_length(G):.2f}")
else:
 print(f"\nGraph has {nx.number_connected_components(G)} components — diameter/path length only valid per-component.")
# Clustering coefficient
print(f"Average clustering coefficient: {nx.average_clustering(G):.4f}")
# Community detection (regional clusters / cross-border patterns)
from networkx.algorithms.community import greedy_modularity_communities
communities = list(greedy_modularity_communities(G))
print(f"\nDetected {len(communities)} communities")
for i, c in enumerate(communities):
 print(f"Community {i}: {len(c)} substations")
# --- N-1 Contingency Analysis ---
# Simulates what happens if a major substation is taken out — the same check
# grid operators run before scheduling maintenance on a critical asset.
top_hub = top_by_degree[0][0]
G_minus = G.copy()
G_minus.remove_node(top_hub)
print(f"\nConnected components before removing '{top_hub}': {nx.number_connected_components(G)}")
print(f"Connected components after removing '{top_hub}': {nx.number_connected_components(G_minus)}")
# Run this for the top 5 hubs, not just the single top one, and log the results
n1_results = []
for hub, _ in top_by_degree[:5]:
 G_test = G.copy()
 G_test.remove_node(hub)
 n1_results.append({
 'Substation': hub,
 'Components_Before': nx.number_connected_components(G),
 'Components_After': nx.number_connected_components(G_test),
 'Fragments_Network': nx.number_connected_components(G_test) > nx.number_connected_components(G)
 })
n1_df = pd.DataFrame(n1_results)
print("\nN-1 Contingency Summary (top 5 hubs):")
print(n1_df)
n1_df.to_csv('n1_contingency_results.csv', index=False)
# Visualize the network
plt.figure(figsize=(12, 8))
nx.draw(G, with_labels=True, node_size=200, node_color='lightblue', font_size=6)
plt.title('National Grid Substation Network')
plt.tight_layout()
plt.savefig('network_graph.png')
plt.show()
