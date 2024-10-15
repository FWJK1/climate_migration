#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:37:50 2024

@author: carinamanitius
"""

# import packages
import pandas as pd
import geopandas as gpd


##### Import and clean excel files

# Define the paths to your Excel files
data_file_path = '/Users/carinamanitius/Documents/GitHub/climate_migration/Data/County/county_to_county_migrations_table_2005_2009.xls'
header_file_path = '/Users/carinamanitius/Documents/GitHub/climate_migration/Data/County/header_corospondance.xlsx'
shapefile_path = '/Users/carinamanitius/Documents/GitHub/climate_migration/Data/Shapefiles/cb_2023_us_county_500k.shp'

# Read the header correspondence file (assuming the headers are in the first row)
header_df = pd.read_excel(header_file_path, header=None, skiprows=4)

# Extract the first row as the header
headers = header_df.iloc[0].tolist()

# Read all sheets into a dictionary of DataFrames, skipping the first 4 rows
dfs_dict = pd.read_excel(data_file_path, sheet_name=None, skiprows=4)

# Create an empty list to store DataFrames for each state
dfs = []

# Iterate over each DataFrame in the dictionary
for sheet_name, state_df in dfs_dict.items():
    # Rename the columns using the header from the header correspondence file
    state_df.columns = headers
    
    # Add a new column for the state name
    state_df['State'] = sheet_name
    
    # Drop all columns called 'MOE'
    state_df = state_df.loc[:, state_df.columns != 'MOE']
    
    # Append the DataFrame to the list
    dfs.append(state_df)

# Concatenate all DataFrames into a single DataFrame
combined_df = pd.concat(dfs, ignore_index=True)



###### Quick compare migration flows

filtered_df = combined_df[['Current_state_FIPS', 'Current_county_FIPS', 'Current_state', 'Current_county', 'Past_state', 'Past_county', 'County_to_county_movers', 'Current_population', 'Past_population']].copy()

filtered_df['Past_flow_pc'] = filtered_df['County_to_county_movers'] / filtered_df['Past_population']
filtered_df['Current_flow_pc'] = filtered_df['County_to_county_movers'] / filtered_df['Current_population']

summed_df = filtered_df.groupby(
    ['Current_state', 'Current_county', 'Current_state_FIPS', 'Current_county_FIPS']
).agg(
    Total_county_to_county_movers=('County_to_county_movers', 'sum'),
    Total_Current_flow_pc=('Current_flow_pc', 'sum')
).reset_index()
      

final_summed_df = summed_df.groupby('Current_state').agg(
    Total_county_to_county_movers=('Total_county_to_county_movers', 'sum'),
    Total_Current_flow_pc=('Total_Current_flow_pc', 'sum')
).reset_index()
      
      
### MAP!

counties = gpd.read_file(shapefile_path)







