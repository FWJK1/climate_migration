#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 16:16:57 2024

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


##### Import county shapefile

shapefile_path = f"{root}/Data/Shapefiles/Counties/cb_2023_us_county_500k_MAINLAND.shp"
counties = gpd.read_file(shapefile_path)


##### Import storm events database (saved as 4 sperated parquets fot git management)

# Directory containing the split Parquet files
directory_path = f'{root}/Data/Storm events'
parquet_files = [f for f in os.listdir(directory_path) if f.endswith('.parquet')]

# List to hold each DataFrame
dataframes = []

# Read each Parquet file and append to the list
for file in parquet_files:
    file_path = os.path.join(directory_path, file)
    df = pd.read_parquet(file_path)
    dataframes.append(df)
    print(f'Imported {file} with shape {df.shape}')

# Concatenate all DataFrames into a single DataFrame
events_db = pd.concat(dataframes, ignore_index=True)











sample = events_db.head(10)


# drop all non-state counties 
events_db = events_db[events_db['State FIPS'] <= 56]

# recode FIPS codes 
events_db['State FIPS'] = events_db['State FIPS'].apply(lambda x: f"{int(x):02d}")
events_db['County/Zone FIPS'] = events_db['County/Zone FIPS'].apply(lambda x: f"{int(x):03d}")
events_db['FIPS'] = events_db['State FIPS'] + events_db['County/Zone FIPS']

# Convert 'Property Damage' to numeric
def convert_damage(damage_str):
    if pd.isnull(damage_str):  # Check for NaN values
        return 0
    damage_str = damage_str.strip().upper()  # Normalize to uppercase and remove whitespace

    # Handle special case where the string is just 'K'
    if damage_str == 'K':
        return 1000

    try:
        if 'K' in damage_str:  # Handle thousands
            return int(float(damage_str.replace('K', '').replace(',', '')) * 1000)
        elif 'M' in damage_str:  # Handle millions
            return int(float(damage_str.replace('M', '').replace(',', '')) * 1000000)
        elif 'B' in damage_str:  # Handle billions
            return int(float(damage_str.replace('B', '').replace(',', '')) * 1000000000)
        elif 'H' in damage_str:  # Handle hundreds
            return int(float(damage_str.replace('H', '').replace(',', '')) * 100)
        else:  # Handle regular numbers
            return int(float(damage_str.replace(',', '')))
    except ValueError:
        # If conversion fails, return 0 or handle as needed
        print(f"Warning: Could not convert '{damage_str}' to a number.")
        return 0  # You can also choose to return NaN or another default value

events_db['Property Damage'] = events_db['Property Damage'].apply(convert_damage)



#### Generate summary stats

events_summary = events_db.groupby(['FIPS', 'Year']).agg(
    event_count=('Event Type', 'size'),  # Count of events
    total_property_damage=('Property Damage', 'sum'),
    avg_property_damage=('Property Damage', 'mean'),
    total_direct_injuries=('Direct Injuries', 'sum'),
    avg_direct_injuries=('Direct Injuries', 'mean'),
    total_indirect_injuries=('Indirect Injuries', 'sum'),
    avg_indirect_injuries=('Indirect Injuries', 'mean'),
    total_direct_deaths=('Direct Deaths', 'sum'),
    avg_direct_deaths=('Direct Deaths', 'mean'),
    total_indirect_deaths=('Indirect Deaths', 'sum'),
    avg_indirect_deaths=('Indirect Deaths', 'mean')
).reset_index()


events_summary['total_deaths'] = events_summary['total_direct_deaths'] + events_summary['total_indirect_deaths']

# Create a new DataFrame with total property damage and total deaths by FIPS across all years
total_summary = events_summary.groupby('FIPS').agg(
    total_property_damage=('total_property_damage', 'sum'),
    total_deaths=('total_deaths', 'sum')
).reset_index()


events_summary_GDF = counties.merge(total_summary, left_on='GEOID', right_on='FIPS', how='left')


##### create 5 year time period stats

# Define the 5-year periods from 1950 to 2021
start_year = 1950
end_year = 2021
periods = [(year, year + 4) for year in range(start_year, end_year - 4 + 1)]

# Initialize lists to store the aggregated data
total_damage_data = []
total_death_data = []

# Iterate through each period and aggregate the data
for start, end in periods:
    # Filter the events_summary for the current period
    period_data = events_summary[(events_summary['Year'] >= start) & (events_summary['Year'] <= end)]
    
    # Group by FIPS and aggregate
    damage_sum = period_data.groupby('FIPS')['total_property_damage'].sum().reset_index()
    death_sum = period_data.groupby('FIPS')['total_deaths'].sum().reset_index()
    
    # Rename columns to include the period
    damage_sum.columns = ['FIPS', f'{start}-{end} Property Damage']
    death_sum.columns = ['FIPS', f'{start}-{end} Deaths']
    
    # Append the data to the lists
    total_damage_data.append(damage_sum)
    total_death_data.append(death_sum)

# Merge all damage data into a single DataFrame
total_damage_df = total_damage_data[0]
for df in total_damage_data[1:]:
    total_damage_df = total_damage_df.merge(df, on='FIPS', how='outer')

# Merge all death data into a single DataFrame
total_death_df = total_death_data[0]
for df in total_death_data[1:]:
    total_death_df = total_death_df.merge(df, on='FIPS', how='outer')

# Fill NaN values with 0 for both DataFrames
total_damage_df.fillna(0, inplace=True)
total_death_df.fillna(0, inplace=True)





# Import cleaned migration CSVs and merge with shapefile to make maps
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

summed_period_gdfs = {}

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













#### TOTAL DEATHS AND DAMAGES BY COUNTY 


# Set up the plot for total property damage
fig, ax = plt.subplots(1, 2, figsize=(14, 7))

# Map 1: Total Property Damage by County
events_summary_GDF.plot(column='total_property_damage', ax=ax[0], legend=True,
                 cmap='OrRd',  # Choose a colormap
                 edgecolor=None,  # Turn off the edge color
                 missing_kwds={
                     "color": "lightgrey",  # Color for missing data
                     "label": "Missing values"
                 })
ax[0].set_title('Total Property Damage by County')
ax[0].set_axis_off()  # Turn off the axis

# Map 2: Total Deaths by County
events_summary_GDF.plot(column='total_deaths', ax=ax[1], legend=True,
                 cmap='Blues',  # Choose a different colormap
                 edgecolor=None,  # Turn off the edge color
                 missing_kwds={
                     "color": "lightgrey",  # Color for missing data
                     "label": "Missing values"
                 })
ax[1].set_title('Total Deaths by County')
ax[1].set_axis_off()  # Turn off the axis

# Adjust layout and show the plot
plt.tight_layout()

plt.savefig(f'{root}/Figures/Storm Events/damages_all_years_county.png')  # Uncomment to save as PNG files

plt.show()



#### TOTAL DEATHS AND DAMAGES BY COUNTY (PERCENTILE)


# Calculate the percentiles for total property damage and total deaths
events_summary_GDF['property_damage_percentile'] = events_summary_GDF['total_property_damage'].rank(pct=True) * 100
events_summary_GDF['death_percentile'] = events_summary_GDF['total_deaths'].rank(pct=True) * 100

# Set up the plot for total property damage and deaths
fig, ax = plt.subplots(1, 2, figsize=(14, 7))

# Map 1: Total Property Damage by County (Percentiles)
events_summary_GDF.plot(column='property_damage_percentile', ax=ax[0], legend=True,
                         cmap='OrRd',  # Choose a colormap
                         edgecolor=None,  # Turn off the edge color
                         missing_kwds={
                             "color": "lightgrey",  # Color for missing data
                             "label": "Missing values"
                         })
ax[0].set_title('Total Property Damage by County (Percentiles)')
ax[0].set_axis_off()  # Turn off the axis

# Map 2: Total Deaths by County (Percentiles)
events_summary_GDF.plot(column='death_percentile', ax=ax[1], legend=True,
                         cmap='Blues',  # Choose a different colormap
                         edgecolor=None,  # Turn off the edge color
                         missing_kwds={
                             "color": "lightgrey",  # Color for missing data
                             "label": "Missing values"
                         })
ax[1].set_title('Total Deaths by County (Percentiles)')
ax[1].set_axis_off()  # Turn off the axis

# Adjust layout and show the plot
plt.tight_layout()

plt.savefig(f'{root}/Figures/Storm Events/damages_all_years_percent_county.png')  # Uncomment to save as PNG files

plt.show()



##### TOTAL DAMAGE AND DEATHS ACROSS US

# Assuming events_summary DataFrame is already created
# Aggregate sums across all FIPS for each year
yearly_totals = events_summary.groupby('Year').agg(
    total_property_damage=('total_property_damage', 'sum'),
    total_direct_deaths=('total_direct_deaths', 'sum'),
    total_indirect_deaths=('total_indirect_deaths', 'sum')
).reset_index()

# Calculate total deaths (direct + indirect)
yearly_totals['total_deaths'] = yearly_totals['total_direct_deaths'] + yearly_totals['total_indirect_deaths']

# Plotting the data
fig, ax1 = plt.subplots(figsize=(12, 6))

# Plot total property damage
ax1.plot(yearly_totals['Year'], yearly_totals['total_property_damage'], marker='o', linestyle='-', color='b', label='Total Property Damage')
ax1.set_xlabel('Year')
ax1.set_ylabel('Total Property Damage', color='b')
ax1.tick_params(axis='y', labelcolor='b')

# Create a second y-axis for total deaths
ax2 = ax1.twinx()
ax2.plot(yearly_totals['Year'], yearly_totals['total_deaths'], marker='o', linestyle='-', color='r', label='Total Deaths')
ax2.set_ylabel('Total Deaths', color='r')
ax2.tick_params(axis='y', labelcolor='r')

# Add title and grid
plt.title('Total Property Damage and Total Deaths from Storm Events in US by Year')
ax1.grid()
ax1.legend(loc='upper left')
ax2.legend(loc='upper right')

# Show plot
plt.tight_layout()

plt.savefig(f'{root}/Figures/Storm Events/damages_all_years_USA.png')  # Uncomment to save as PNG files

plt.show()



















