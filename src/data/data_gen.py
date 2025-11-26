import osmnx as ox
import matplotlib.pyplot as plt

def main():
	print("Step 1: Downloading map data for Heilbronn...")
		
	# 1. Download the graph
	# 'network_type="drive"' ensures we get roads for cars, not walking paths
	graph = ox.graph_from_place("Heilbronn, Germany", network_type="drive")
		
	print("Step 2: Map downloaded! Stats:")
	# Basic check to see if we actually got data (nodes = intersections, edges = roads)
	print(f" - Intersections (Nodes): {len(graph.nodes)}")
	print(f" - Road segments (Edges): {len(graph.edges)}")

	# 2. Save the map for SUMO
	# SUMO cannot read Python variables. It needs a file (usually .osm or .net.xml).
	# We save this as an OpenStreetMap (.osm) file.
	output_filename = "heilbronn.osm"
	ox.save_graph_xml(graph, filepath=output_filename)
	print(f"Step 3: Map saved as '{output_filename}'. You can import this into SUMO later.")

	# 3. Plot the graph (Visual confirmation)
	print("Step 4: Displaying plot... (Close the window to finish the program)")
	ox.plot_graph(graph)

# This block is standard Python syntax.
# It means: "If this file is run directly, execute the main() function."
if __name__ == "__main__":
	main()