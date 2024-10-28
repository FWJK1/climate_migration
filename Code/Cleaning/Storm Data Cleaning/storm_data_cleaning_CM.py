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

# Clear the DataFrame and the list to free up memory
del df
for df in dataframes:
    del df
dataframes.clear()
del dataframes 
del parquet_files



##### CLEAN storm events dataframe 

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


# filter out years
events_db = events_db[events_db['Year'] >= 2000]



#### Generate summary stats

# sum direct and indirect deaths and injuries 
events_db['Deaths'] = events_db['Direct Deaths'] + events_db['Indirect Deaths']  #FK fixed a typo where it just summed direct deaths twice
events_db['Injuries'] = events_db['Direct Injuries'] + events_db['Indirect Injuries']

# generate summary statistics over whole time period 
events_summary = events_db.groupby(['FIPS', 'Year']).agg(
    event_count=('Event Type', 'size'),  # Count of events
    total_property_damage=('Property Damage', 'sum'),
    avg_property_damage=('Property Damage', 'mean'),
    total_injuries=('Injuries', 'sum'),
    avg_injuries=('Injuries', 'mean'),
    total_deaths=('Deaths', 'sum'),
    avg_deaths=('Deaths', 'mean'),
).reset_index()

events_summary.to_csv(f"{root}/Data/Storm events/year_county_summary.csv")


# Create a new DataFrame with total property damage and total deaths by FIPS across all years
total_summary = events_summary.groupby('FIPS').agg(
    event_count=('event_count', 'sum'),
    total_property_damage=('total_property_damage', 'sum'),
    total_injuries=('total_injuries', 'sum'),
    total_deaths=('total_deaths', 'sum')
).reset_index()


total_summary['damage_per_event'] = total_summary['total_property_damage'] / total_summary['event_count'] 
total_summary['injuries_per_event'] = total_summary['total_injuries'] / total_summary['event_count'] 
total_summary['deaths_per_event'] = total_summary['total_deaths'] / total_summary['event_count'] 

total_summary.to_csv(f"{root}/Data/Storm events/allperiods_county_summary.csv")


# merge with counties shapefile
events_summary_GDF = counties.merge(total_summary, left_on='GEOID', right_on='FIPS', how='left')



####### MAKE FIGURES ######## 

#### TOTAL DEATHS AND DAMAGES BY COUNTY 

# Set up the plot for total property damage and deaths
fig, ax = plt.subplots(2, 2, figsize=(14, 10))  # Adjusted height for better visibility

# Map 1: Total Events by County
events_summary_GDF.plot(column='event_count', ax=ax[0, 0], legend=True,
                        cmap='OrRd',  # Choose a colormap
                        edgecolor=None,  # Turn off the edge color
                        missing_kwds={
                            "color": "lightgrey",  # Color for missing data
                            "label": "Missing values"
                        })
ax[0, 0].set_title('Total Events by County')
ax[0, 0].set_axis_off()  # Turn off the axis

# Map 2: Total Property Damage by County
events_summary_GDF.plot(column='total_property_damage', ax=ax[0, 1], legend=True,
                        cmap='OrRd',  # Choose a colormap
                        edgecolor=None,  # Turn off the edge color
                        missing_kwds={
                            "color": "lightgrey",  # Color for missing data
                            "label": "Missing values"
                        })
ax[0, 1].set_title('Total Property Damage by County')
ax[0, 1].set_axis_off()  # Turn off the axis

# Map 3: Total Deaths by County
events_summary_GDF.plot(column='total_deaths', ax=ax[1, 0], legend=True,
                        cmap='Blues',  # Choose a different colormap
                        edgecolor=None,  # Turn off the edge color
                        missing_kwds={
                            "color": "lightgrey",  # Color for missing data
                            "label": "Missing values"
                        })
ax[1, 0].set_title('Total Deaths by County')
ax[1, 0].set_axis_off()  # Turn off the axis

# Map 4: Average Deaths per Event by County
events_summary_GDF['deaths_per_event'] = events_summary_GDF['total_deaths'] / events_summary_GDF['event_count']  # Calculate average deaths per event
events_summary_GDF.plot(column='deaths_per_event', ax=ax[1, 1], legend=True,
                        cmap='Blues',  # Choose a different colormap
                        edgecolor=None,  # Turn off the edge color
                        missing_kwds={
                            "color": "lightgrey",  # Color for missing data
                            "label": "Missing values"
                        })
ax[1, 1].set_title('Average Deaths per Event by County')
ax[1, 1].set_axis_off()  # Turn off the axis

# Adjust layout and show the plot
plt.tight_layout()

plt.savefig(f'{root}/Figures/Storm Events/damages_since_2000_county.png')  # Save as PNG file

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



















