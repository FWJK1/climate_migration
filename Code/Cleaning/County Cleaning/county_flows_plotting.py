#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 11:19:16 2024

@author: carinamanitius
"""

# import packages
import pandas as pd
import geopandas as gpd
import os
import matplotlib.pyplot as plt


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


##### Import 

shapefile_path = f"{root}/Data/Shapefiles/Counties/cb_2023_us_county_500k_MAINLAND.shp"
counties = gpd.read_file(shapefile_path)


# Define a list of the time periods you have
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


# Dictionary to store the summed DataFrame for each period
summed_period_gdfs = {}

# Import cleaned CSVs and merge with shapefile to make maps
for start_year, end_year in periods:
    data_file_path = f"{root}/Data/County/Summed_clean/summed_{start_year}_{end_year}.csv"
    dfs_dict = pd.read_csv(data_file_path)
    
    dfs_dict['in_gross_thousands'] = dfs_dict['Inflow_gross'] / 1000
    dfs_dict['out_gross_thousands'] = dfs_dict['Outflow_gross'] / 1000
    dfs_dict['net_thousands'] = dfs_dict['in_gross_thousands'] - dfs_dict['out_gross_thousands']
    dfs_dict['Net_pc'] = ((dfs_dict['net_thousands'] * 1000) / dfs_dict['Population']) * 100

    dfs_dict['STATE_FIPS'] = dfs_dict['STATE_FIPS'].astype(str).str.zfill(2)

    dfs_dict['COUNTY_FIPS'] = dfs_dict['COUNTY_FIPS'].astype(str).str.zfill(3)
    
    merged_gdf = counties.merge(
        dfs_dict,
        left_on=['STATEFP', 'COUNTYFP'],  # Columns in the GeoDataFrame
        right_on=['STATE_FIPS', 'COUNTY_FIPS'],  # Columns in the test DataFrame
        how='left'  # Change this to 'outer', 'left', or 'right' if needed
    )
    
    summed_period_gdfs[f"{start_year}_{end_year}"] = merged_gdf



 
 
 
######### PER CAPITA OUTFLOW

# Find the global min and max values across all GeoDataFrames for the specified column
all_values = []

# Collect all values for the column you are interested in
for merged_gdf in summed_period_gdfs.values():
    all_values.extend(merged_gdf['Outflow_pc'].dropna().tolist())

# Calculate global min and max
global_min = min(all_values)
global_max = max(all_values)

# Loop through each GeoDataFrame in summed_period_gdfs and create a plot
for period, merged_gdf in summed_period_gdfs.items():
    # Extract start and end year from the period string
    start_year, end_year = period.split('_')

    # Set the figure size
    fig, ax = plt.subplots(figsize=(10, 5))  

    # Plot the GeoDataFrame with fixed color scale
    merged_gdf.plot(column='Outflow_pc',  # Choose the appropriate column to plot
                     cmap='summer',  
                     legend=True, 
                     vmin=global_min,  # Set the same minimum for all plots
                     vmax=global_max,  # Set the same maximum for all plots
                     missing_kwds={'color': 'lightgrey', 'label': 'Missing Values'},
                     edgecolor='none', 
                     ax=ax)  

    # Remove the box and axis labels
    ax.set_axis_off()  # This removes the axis

    # Add title with the specified format
    plt.title(f'Outflow per 100, {start_year} - {end_year}', fontsize=15)

    plt.savefig(f'{root}/Figures/County EDA/Color_coded_outflow/Per_capita/pc_outflow_{start_year}_{end_year}.png')  # Uncomment to save as PNG files


  
######### PER CAPITA INFLOW

# Find the global min and max values across all GeoDataFrames for the specified column
all_values = []

# Collect all values for the column you are interested in
for merged_gdf in summed_period_gdfs.values():
    all_values.extend(merged_gdf['Inflow_pc'].dropna().tolist())

# Calculate global min and max
global_min = min(all_values)
global_max = max(all_values)

# Loop through each GeoDataFrame in summed_period_gdfs and create a plot
for period, merged_gdf in summed_period_gdfs.items():
    # Extract start and end year from the period string
    start_year, end_year = period.split('_')

    # Set the figure size
    fig, ax = plt.subplots(figsize=(10, 5))  

    # Plot the GeoDataFrame with fixed color scale
    merged_gdf.plot(column='Inflow_pc',  # Choose the appropriate column to plot
                     cmap='summer',  
                     legend=True, 
                     vmin=global_min,  # Set the same minimum for all plots
                     vmax=global_max,  # Set the same maximum for all plots
                     missing_kwds={'color': 'lightgrey', 'label': 'Missing Values'},
                     edgecolor='none', 
                     ax=ax)  

    # Remove the box and axis labels
    ax.set_axis_off()  # This removes the axis

    # Add title with the specified format
    plt.title(f'Inflow per 100, {start_year} - {end_year}', fontsize=15)

    plt.savefig(f'{root}/Figures/County EDA/Color_coded_inflow/Per_capita/pc_inflow_{start_year}_{end_year}.png')  # Uncomment to save as PNG files

    
 
######### PER CAPITA NET

# Calculate global min and max
global_min = -18
global_max = 4

# Loop through each GeoDataFrame in summed_period_gdfs and create a plot
for period, merged_gdf in summed_period_gdfs.items():
    # Extract start and end year from the period string
    start_year, end_year = period.split('_')

    # Set the figure size
    fig, ax = plt.subplots(figsize=(10, 5))  

    # Plot the GeoDataFrame with fixed color scale
    merged_gdf.plot(column='Net_pc',  # Choose the appropriate column to plot
                     cmap='RdBu',  # Change this to a diverging colormap
                     legend=True, 
                     vmin=global_min,  # Set the same minimum for all plots
                     vmax=global_max,  # Set the same maximum for all plots
                     missing_kwds={'color': 'lightgrey', 'label': 'Missing Values'},
                     edgecolor='none', 
                     ax=ax)  

    # Remove the box and axis labels
    ax.set_axis_off()  # This removes the axis

    # Add title with the specified format
    plt.title(f'Net Migration per 100, {start_year} - {end_year}', fontsize=15)

    plt.savefig(f'{root}/Figures/County EDA/Color_coded_net/Per_capita/pc_net_{start_year}_{end_year}.png')  # Uncomment to save as PNG files


    
######### GROSS NET

# Find the global min and max values across all GeoDataFrames for the specified column
all_values = []

# Collect all values for the column you are interested in
for merged_gdf in summed_period_gdfs.values():
    all_values.extend(merged_gdf['net_thousands'].dropna().tolist())

# Calculate global min and max
global_min = min(all_values)
global_max = max(all_values)

# Loop through each GeoDataFrame in summed_period_gdfs and create a plot
for period, merged_gdf in summed_period_gdfs.items():
    # Extract start and end year from the period string
    start_year, end_year = period.split('_')

    # Set the figure size
    fig, ax = plt.subplots(figsize=(10, 5))  

    # Plot the GeoDataFrame with fixed color scale
    merged_gdf.plot(column='net_thousands',  # Choose the appropriate column to plot
                     cmap='RdBu',  # Change this to a diverging colormap
                     legend=True, 
                     vmin=global_min,  # Set the same minimum for all plots
                     vmax=global_max,  # Set the same maximum for all plots
                     missing_kwds={'color': 'lightgrey', 'label': 'Missing Values'},
                     edgecolor='none', 
                     ax=ax)  

    # Remove the box and axis labels
    ax.set_axis_off()  # This removes the axis

    # Add title with the specified format
    plt.title(f'Gross Net Migration, thousands {start_year} - {end_year}', fontsize=15)

    plt.savefig(f'{root}/Figures/County EDA/Color_coded_net/Gross/gross_net_{start_year}_{end_year}.png')  # Uncomment to save as PNG files


######### GROSS INFLOW

# Find the global min and max values across all GeoDataFrames for the specified column
all_values = []

# Collect all values for the column you are interested in
for merged_gdf in summed_period_gdfs.values():
    all_values.extend(merged_gdf['in_gross_thousands'].dropna().tolist())

# Calculate global min and max
global_min = min(all_values)
global_max = max(all_values)

# Loop through each GeoDataFrame in summed_period_gdfs and create a plot
for period, merged_gdf in summed_period_gdfs.items():
    # Extract start and end year from the period string
    start_year, end_year = period.split('_')

    # Set the figure size
    fig, ax = plt.subplots(figsize=(10, 5))  

    # Plot the GeoDataFrame with fixed color scale
    merged_gdf.plot(column='in_gross_thousands',  # Choose the appropriate column to plot
                     cmap='summer',  
                     legend=True, 
                     vmin=global_min,  # Set the same minimum for all plots
                     vmax=global_max,  # Set the same maximum for all plots
                     missing_kwds={'color': 'lightgrey', 'label': 'Missing Values'},
                     edgecolor='none', 
                     ax=ax)  

    # Remove the box and axis labels
    ax.set_axis_off()  # This removes the axis

    # Add title with the specified format
    plt.title(f'Gross Inflow, thousands {start_year} - {end_year}', fontsize=15)

    plt.savefig(f'{root}/Figures/County EDA/Color_coded_inflow/Gross/gross_inflow_{start_year}_{end_year}.png')  # Uncomment to save as PNG files



######### GROSS OUTFLOW

# Find the global min and max values across all GeoDataFrames for the specified column
all_values = []

# Collect all values for the column you are interested in
for merged_gdf in summed_period_gdfs.values():
    all_values.extend(merged_gdf['out_gross_thousands'].dropna().tolist())

# Calculate global min and max
global_min = min(all_values)
global_max = max(all_values)

# Loop through each GeoDataFrame in summed_period_gdfs and create a plot
for period, merged_gdf in summed_period_gdfs.items():
    # Extract start and end year from the period string
    start_year, end_year = period.split('_')

    # Set the figure size
    fig, ax = plt.subplots(figsize=(10, 5))  

    # Plot the GeoDataFrame with fixed color scale
    merged_gdf.plot(column='out_gross_thousands',  # Choose the appropriate column to plot
                     cmap='summer',  
                     legend=True, 
                     vmin=global_min,  # Set the same minimum for all plots
                     vmax=global_max,  # Set the same maximum for all plots
                     missing_kwds={'color': 'lightgrey', 'label': 'Missing Values'},
                     edgecolor='none', 
                     ax=ax)  

    # Remove the box and axis labels
    ax.set_axis_off()  # This removes the axis

    # Add title with the specified format
    plt.title(f'Gross Outflow, thousands {start_year} - {end_year}', fontsize=15)

    plt.savefig(f'{root}/Figures/County EDA/Color_coded_outflow/Gross/gross_outflow_{start_year}_{end_year}.png')  # Uncomment to save as PNG files






