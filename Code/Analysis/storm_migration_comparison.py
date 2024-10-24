#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 20:53:01 2024

@author: carinamanitius
"""

# import packages
import pandas as pd
import geopandas as gpd
import os
import matplotlib.pyplot as plt
import imageio
import numpy as np



##### Get WD
 
def find_repo_root(start_path):
    current_path = os.path.abspath(start_path)
   
    while True:
        # Check for the existence of the .git directory or other indicators
        if os.path.isdir(os.path.join(current_path, '.git')) or \
           os.path.isfile(os.path.join(current_path, 'README.md')):
            return current_path
       
        parent_path = os.path.dirname(current_path)
       
        # Stop if we reach the root directory
        if parent_path == current_path:
            break
       
        current_path = parent_path
 
    return None  # Return None if not found
 
root = find_repo_root(os.getcwd())



##### Import data

# county shapefile
counties = gpd.read_file(f"{root}/Data/Shapefiles/Counties/cb_2023_us_county_500k_MAINLAND.shp")

# storm events 
events_summary = pd.read_csv(f"{root}/Data/Storm events/year_county_summary.csv")
total_summary = pd.read_csv(f"{root}/Data/Storm events/allperiods_county_summary.csv")

# import and append migration data 
periods = [
    ('2005', '2009'),
    ('2006', '2010'),
    ('2007', '2011'),
    ('2008', '2012'),
    ('2009', '2013'),
    ('2010', '2014'),
    ('2011', '2015'),
    ('2012', '2016'),
    ('2013', '2017'),
    ('2014', '2018'),
    ('2015', '2019'),
    ('2016', '2020')
]

migration_flows = {}

for start_year, end_year in periods:
    data_file_path = f"{root}/Data/County/Summed_clean/summed_{start_year}_{end_year}.csv"
    dfs_dict = pd.read_csv(data_file_path)
    
    dfs_dict['in_gross_thousands'] = dfs_dict['Inflow_gross'] / 1000
    dfs_dict['out_gross_thousands'] = dfs_dict['Outflow_gross'] / 1000
    dfs_dict['net_thousands'] = dfs_dict['in_gross_thousands'] - dfs_dict['out_gross_thousands']
    dfs_dict['Net_pc'] = ((dfs_dict['net_thousands'] * 1000) / dfs_dict['Population']) * 100

    dfs_dict['STATE_FIPS'] = dfs_dict['STATE_FIPS'].astype(str).str.zfill(2)

    dfs_dict['COUNTY_FIPS'] = dfs_dict['COUNTY_FIPS'].astype(str).str.zfill(3)
    
    
    migration_flows[f"{start_year}_{end_year}"] = dfs_dict




##### merge data 

events_summary_GDF = counties.merge(total_summary, left_on='GEOID', right_on='FIPS', how='left')



# merge migration and damages and deaths

events_summary['FIPS'] = events_summary['FIPS'].astype(str).str.zfill(5)  # Assuming FIPS has 5 digits
merged_gdf['GEOID'] = merged_gdf['GEOID'].astype(str)  # Ensure GEOID is a string



merged_data = merged_gdf.merge(
    events_summary,
    left_on='GEOID',  # Merge on the GEOID from merged_gdf
    right_on='FIPS',  # Merge on the FIPS from events_summary
    how='left'  # Change to 'inner' if you want only matching records
)

filtered_data = merged_data.dropna(subset=['total_property_damage', 'net_thousands'])

# Create the scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(filtered_data['total_property_damage'], 
            filtered_data['net_thousands'], 
            alpha=0.7)  # Adjust alpha for transparency

# Add labels and title
plt.xlabel('Total Property Damage (in thousands)', fontsize=12)
plt.ylabel('Net Thousands', fontsize=12)
plt.title('Scatter Plot of Total Property Damage vs. Net Thousands by FIPS', fontsize=15)

# Optionally, add gridlines for better readability
plt.grid()

# Show the plot
plt.tight_layout()

plt.savefig(f'{root}/Figures/Storm Events/damages_scatter.png')  # Uncomment to save as PNG files

plt.show()


