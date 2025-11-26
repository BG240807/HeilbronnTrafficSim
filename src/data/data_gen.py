import osmnx as ox
import matplotlib.pyplot as plt

def main():
	# --- CONFIGURATION STEP ---
	print("Step 0: Configuring OSMnx settings...")
	ox.settings.all_oneway = True 
	# --------------------------

	print("Step 1: Downloading map data for Heilbronn...")
		
	# 1. Download the graph
	# !!! THE FIX IS HERE: simplify=False !!!
	graph = ox.graph_from_place(
		"Heilbronn, Germany", 
		network_type="drive", 
		simplify=False
	)
		
	print("Step 2: Map downloaded! Stats:")
	print(f" - Intersections (Nodes): {len(graph.nodes)}")
	print(f" - Road segments (Edges): {len(graph.edges)}")

	# 2. Save the map for SUMO
	output_filename = "heilbronn.osm"
	# This will now work because the graph is "unsimplified"
	ox.save_graph_xml(graph, filepath=output_filename)
	print(f"Step 3: Map saved as '{output_filename}'.")

	# 3. Plot the graph
	# Note: It might look a bit 'messier' now because every tiny curve point is a node
	print("Step 4: Displaying plot... (Close the window to finish)")
	ox.plot_graph(graph)

if __name__ == "__main__":
	main()