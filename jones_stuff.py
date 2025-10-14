################################
#
################################

import json
import ast
import pandas as pd
import geopandas as gpd
import fiona
from pathlib import Path
from gerrychain import Graph



##### get Peter's data
##### This is from Hane's districts.ipynb
# Read in geopackage
# CA_data == entire folder from Peter
gpkg = Path("C:/Users/mijones/Documents/Datasets/CA_data/ca_districtr_bg_view_v1.gpkg")
layers = fiona.listlayers(gpkg)

# You should see a layer that says something like "ca_districtr_county_view_v1"
# print(layers)

# Read in geopackage
gdf = gpd.read_file(gpkg, layer="ca_districtr_bg_view_v1")

# Add coordinates for plotting
gdf['C_X'] = gdf.centroid.x
gdf['C_Y'] = gdf.centroid.y
# print(gdf.head())

# Convert geopackage first into a gpd graph
bg_graph = Graph.from_geodataframe(gdf)

# Check number of nodes (block groups)
# print(len(bg_graph.nodes()))






block_num = 25607
district_nums = [8,10,16,20,40,80]
    
## only run 8 districts for speed
for district_num in [8]:
# for district_num in district_nums:
    
    ##### get Hane's districts
    ##### only opens the first 10 for speed
    with open(f'./districting/chain_out/ca_{district_num}_dist.json') as file:
        lines = [line.rstrip() for line in file]
    
    district_plans = [ast.literal_eval(line)['assignment'] for line in lines[:10]]
    
    for plan_indx in range(len(district_plans)):
        district_plan = district_plans[plan_indx]
    # for district_plan in district_plans:
        ##### create district lists, get populations
        districts = [[] for _ in range(district_num)]
        for indx in range(block_num):
            districts[district_plan[indx]].append(indx)
        
        ## pops measures [hvap_20, non_hispanic]
        pops = {i: [0,0] for i in range(district_num)}
        for district_indx in range(district_num):
            for block_indx in districts[district_indx]:
                # print(bg_graph.nodes()[block_indx]['hvap_20'], bg_graph.nodes()[block_indx]['total_vap_20'])
                pops[district_indx][0] += bg_graph.nodes()[block_indx]['hvap_20']
                pops[district_indx][1] += (bg_graph.nodes()[block_indx]['total_vap_20'] - bg_graph.nodes()[block_indx]['hvap_20'])
                
        ## normalize pop nums to percentages
        for district_indx in range(8):
            total_pop = pops[district_indx][0] + pops[district_indx][1]
            pops[district_indx][0] /= total_pop
            pops[district_indx][1] /= total_pop
        
        # print(pops)
    
        
        output_settings = dict(
            bloc_voter_props={"H": [pops[i][0] for i in range(district_num)], "NH": [pops[i][1] for i in range(district_num)]},
            ## cohesion params came from that screenshot in the google doc
            cohesion_parameters={
                "H": {"H": 0.77, "NH": 0.23},
                "NH": {"H": 0.52, "NH": 0.48},
            },
            alphas={"H": {"H": 1, "NH": 1}, "NH": {"H": 1, "NH": 1}},
            slate_to_candidates={"H": ["H1", "H2", "H3", "H4", "H5"], "NH": ["NH1", "NH2", "NH3", "NH4", "NH5"]},
        )
    
        






