from pathlib import Path
import networkx as nx
import fiona
import geopandas as gpd
from gerrychain import Graph
import pickle


##### get Peter's data
##### This is from Hane's districts.ipynb
# Read in geopackage
# CA_data == entire folder from Peter
gpkg = Path("./geographic_data/ca_districtr_bg_view_v1.gpkg")
layers = fiona.listlayers(gpkg)

# You should see a layer that says something like "ca_districtr_county_view_v1"
print(layers)

# # Read in geopackage
gdf = gpd.read_file(gpkg, layer="ca_districtr_bg_view_v1")
gdf.set_index("path", inplace=True)
internal_points_layer = gpd.read_file(
    gpkg, layer="ca_districtr_bg_view_v1__internal_points"
)
internal_points_layer.set_index("path", inplace=True)

# There is an internal points layer that makes this better
# Add coordinates for plotting
gdf["C_X"] = internal_points_layer.geometry.x
gdf["C_Y"] = internal_points_layer.geometry.y
print(gdf.head())


# Convert geopackage first into a gpd graph
bg_graph = Graph.from_geodataframe(gdf)
print(f"Original Edge count: {len(bg_graph.edges())}")

# Open a previous version of the graph and use its edges to fix islands
with open("./geographic_data/06_bg_2020.pkl", "rb") as file:
    previous_bg_graph = pickle.load(file)


edges = list(previous_bg_graph.edges())

for edge in edges:
    bg_graph.add_edge(edge[0], edge[1])

assert nx.is_connected(
    bg_graph
), "Terrible things have happened and the graph is still disconnected!!"

print(f"Final Edge count: {len(bg_graph.edges())}")
# Save graph for later
bg_graph.to_json("./geographic_data/CA_bg_2020_dualgraph.json")
