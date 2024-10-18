#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:37:50 2024

@author: carinamanitius
"""

# import packages
import pandas as pd
import geopandas as gpd
import os

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

header_file_path = f"{root}/Data/County/header_corospondance.xlsx"
shapefile_path = f"{root}/Data/Shapefiles/Counties/cb_2023_us_county_500k_MAINLAND.shp"


# Bring in column names 

header_df = pd.read_excel(header_file_path, header=None, skiprows=4)
headers = header_df.iloc[0].tolist()

# Import county shapefile

counties = gpd.read_file(shapefile_path)



##### Loop to clean dataframes

# Define a list of the time periods you have
xls_periods = [
    ('2005', '2009'),
    ('2006', '2010'),
    ('2007', '2011'),
    ('2008', '2012')
]

xlsx_periods = [
    ('2009', '2013'),
    ('2010', '2014'),
    ('2011', '2015'),
    ('2012', '2016'),
    ('2013', '2017'),
    ('2014', '2018'),
    ('2015', '2019'),
    ('2016', '2020')
]

# Create an empty list to store all dataframes
period_dfs = {}
# Dictionary to store the summed DataFrame for each period
summed_period_dfs = {}


# Loop through each time period for XLS files
for start_year, end_year in xls_periods:
    # Construct the file path for each period
    data_file_path = f"{root}/Data/County/county-to-county-{start_year}-{end_year}-current-residence-sort.xls"
    
    # Read all sheets into a dictionary of DataFrames, skipping the first 4 rows
    dfs_dict = pd.read_excel(data_file_path, sheet_name=None, skiprows=4)

    # Create a list to store DataFrames for all states in this time period
    period_states_dfs = []

    # Iterate over each sheet (state) in the dictionary
    for sheet_name, state_df in dfs_dict.items():
        # Rename the columns using the header from the header correspondence file
        state_df.columns = headers
        
        # Add new columns for the state name, start_year, and end_year
        state_df['State'] = sheet_name
        state_df['Start_Year'] = start_year
        state_df['End_Year'] = end_year
        
        # Drop all columns named 'MOE'
        state_df = state_df.loc[:, state_df.columns != 'MOE']
        
        # Append the DataFrame for this state to the list for this period
        period_states_dfs.append(state_df)
    
    # Concatenate all state DataFrames for this time period into a single DataFrame
    combined_period_df = pd.concat(period_states_dfs, ignore_index=True)
    
    # Add per capita flows 
    combined_period_df['Past_flow_pc'] = (combined_period_df['County_to_county_movers'] / combined_period_df['Past_population']) * 100
    combined_period_df['Current_flow_pc'] = (combined_period_df['County_to_county_movers'] / combined_period_df['Current_population']) * 100
    
    # Fix state and county encoding 
    combined_period_df['Current_state_FIPS'] = combined_period_df['Current_state_FIPS'].astype(str).str[1:].astype(str)    
    combined_period_df['Current_county_FIPS'] = pd.to_numeric(combined_period_df['Current_county_FIPS'], errors='coerce')
    combined_period_df = combined_period_df.dropna(subset=['Current_county_FIPS'])
    combined_period_df['Current_county_FIPS'] = combined_period_df['Current_county_FIPS'].astype(int).astype(str).str.zfill(3).astype(str)

    combined_period_df_copy = combined_period_df
    combined_period_df_copy['Past_state_FIPS'] = combined_period_df_copy['Past_state_FIPS'].astype(str).str[1:].astype(str)    
    combined_period_df_copy['Past_county_FIPS'] = pd.to_numeric(combined_period_df_copy['Past_county_FIPS'], errors='coerce')
    combined_period_df_copy = combined_period_df_copy.dropna(subset=['Past_county_FIPS'])
    combined_period_df_copy['Past_county_FIPS'] = combined_period_df_copy['Past_county_FIPS'].astype(int).astype(str).str.zfill(3).astype(str)

    # Store the combined DataFrame for this period in the dictionary
    period_dfs[f"{start_year}_{end_year}"] = combined_period_df
    
    # Now, create a summed DataFrame for this period
    summed_df_current = combined_period_df.groupby(
        ['Current_state', 'Current_county', 'Current_state_FIPS', 'Current_county_FIPS']
    ).agg({
        'County_to_county_movers': 'sum',
        'Current_population': 'sum'
    }).reset_index()

    summed_df_past = combined_period_df_copy.groupby(
        ['Past_state', 'Past_county', 'Past_state_FIPS', 'Past_county_FIPS']
    ).agg({
        'County_to_county_movers': 'sum',
        'Past_population': 'sum'
    }).reset_index()
    
    # Calculate per capita flow for the summed DataFrame
    summed_df_current['Inflow_pc'] = (summed_df_current['County_to_county_movers'] / summed_df_current['Current_population']) * 100
    summed_df_past['Outflow_pc'] = (summed_df_past['County_to_county_movers'] / summed_df_past['Past_population']) * 100
    summed_df_current['Inflow_gross'] = summed_df_current['County_to_county_movers']
    summed_df_past['Outflow_gross'] = summed_df_past['County_to_county_movers']

    summed_df = summed_df_current.merge(
        summed_df_past,
        left_on=['Current_state_FIPS', 'Current_county_FIPS'],  # Columns in the GeoDataFrame
        right_on=['Past_state_FIPS', 'Past_county_FIPS'],  # Columns in the test DataFrame
        how='left'  # Change this to 'outer', 'left', or 'right' if needed
        )
    
    summed_df = summed_df[['Current_state', 'Current_county', 'Current_state_FIPS', 'Current_county_FIPS', 'Current_population', 'Inflow_pc', 'Inflow_gross', 'Outflow_pc', 'Outflow_gross']]

    summed_df = summed_df.rename(columns={
        'Current_state': 'STATE',
        'Current_county': 'COUNTY',
        'Current_state_FIPS': 'STATE_FIPS',
        'Current_county_FIPS': 'COUNTY_FIPS',
        'Current_population': 'Population',
        })
    
    # Store the summed DataFrame for this period in the dictionary
    summed_period_dfs[f"{start_year}_{end_year}"] = summed_df
    
    # Save the combined and summed DataFrames as CSV files
    combined_csv_path = os.path.join(root, 'Data', 'County', 'By_county_clean', f'bycounty_{start_year}_{end_year}.csv')
    summed_csv_path = os.path.join(root, 'Data', 'County', 'Summed_clean', f'summed_{start_year}_{end_year}.csv')

    combined_period_df.to_csv(combined_csv_path, index=False)
    summed_df.to_csv(summed_csv_path, index=False)

        
# Loop through each time period for XLSX files
for start_year, end_year in xlsx_periods:
    # Construct the file path for each period
    data_file_path = f"{root}/Data/County/county-to-county-{start_year}-{end_year}-current-residence-sort.xlsx"
    
    # Read all sheets into a dictionary of DataFrames, skipping the first 4 rows
    dfs_dict = pd.read_excel(data_file_path, sheet_name=None, skiprows=4)

    # Create a list to store DataFrames for all states in this time period
    period_states_dfs = []

    # Iterate over each sheet (state) in the dictionary
    for sheet_name, state_df in dfs_dict.items():
        # Rename the columns using the header from the header correspondence file
        state_df.columns = headers
        
        # Add new columns for the state name, start_year, and end_year
        state_df['State'] = sheet_name
        state_df['Start_Year'] = start_year
        state_df['End_Year'] = end_year
        
        # Drop all columns named 'MOE'
        state_df = state_df.loc[:, state_df.columns != 'MOE']
        
        # Append the DataFrame for this state to the list for this period
        period_states_dfs.append(state_df)
    
    # Concatenate all state DataFrames for this time period into a single DataFrame
    combined_period_df = pd.concat(period_states_dfs, ignore_index=True)
    
    # Add per capita flows 
    combined_period_df['Past_flow_pc'] = (combined_period_df['County_to_county_movers'] / combined_period_df['Past_population']) * 100
    combined_period_df['Current_flow_pc'] = (combined_period_df['County_to_county_movers'] / combined_period_df['Current_population']) * 100
    
    # Fix state and county encoding 
    combined_period_df['Current_state_FIPS'] = combined_period_df['Current_state_FIPS'].astype(str).str[1:].astype(str)    
    combined_period_df['Current_county_FIPS'] = pd.to_numeric(combined_period_df['Current_county_FIPS'], errors='coerce')
    combined_period_df = combined_period_df.dropna(subset=['Current_county_FIPS'])
    combined_period_df['Current_county_FIPS'] = combined_period_df['Current_county_FIPS'].astype(int).astype(str).str.zfill(3).astype(str)

    combined_period_df_copy = combined_period_df
    combined_period_df_copy['Past_state_FIPS'] = combined_period_df_copy['Past_state_FIPS'].astype(str).str[1:].astype(str)    
    combined_period_df_copy['Past_county_FIPS'] = pd.to_numeric(combined_period_df_copy['Past_county_FIPS'], errors='coerce')
    combined_period_df_copy = combined_period_df_copy.dropna(subset=['Past_county_FIPS'])
    combined_period_df_copy['Past_county_FIPS'] = combined_period_df_copy['Past_county_FIPS'].astype(int).astype(str).str.zfill(3).astype(str)

    # Store the combined DataFrame for this period in the dictionary
    period_dfs[f"{start_year}_{end_year}"] = combined_period_df
    
    # Now, create a summed DataFrame for this period
    summed_df_current = combined_period_df.groupby(
        ['Current_state', 'Current_county', 'Current_state_FIPS', 'Current_county_FIPS']
    ).agg({
        'County_to_county_movers': 'sum',
        'Current_population': 'sum'
    }).reset_index()

    summed_df_past = combined_period_df_copy.groupby(
        ['Past_state', 'Past_county', 'Past_state_FIPS', 'Past_county_FIPS']
    ).agg({
        'County_to_county_movers': 'sum',
        'Past_population': 'sum'
    }).reset_index()
    
    # Calculate per capita flow for the summed DataFrame
    summed_df_current['Inflow_pc'] = (summed_df_current['County_to_county_movers'] / summed_df_current['Current_population']) * 100
    summed_df_past['Outflow_pc'] = (summed_df_past['County_to_county_movers'] / summed_df_past['Past_population']) * 100
    summed_df_current['Inflow_gross'] = summed_df_current['County_to_county_movers']
    summed_df_past['Outflow_gross'] = summed_df_past['County_to_county_movers']

    summed_df = summed_df_current.merge(
        summed_df_past,
        left_on=['Current_state_FIPS', 'Current_county_FIPS'],  # Columns in the GeoDataFrame
        right_on=['Past_state_FIPS', 'Past_county_FIPS'],  # Columns in the test DataFrame
        how='left'  # Change this to 'outer', 'left', or 'right' if needed
        )
    
    summed_df = summed_df[['Current_state', 'Current_county', 'Current_state_FIPS', 'Current_county_FIPS', 'Current_population', 'Inflow_pc', 'Inflow_gross', 'Outflow_pc', 'Outflow_gross']]

    summed_df = summed_df.rename(columns={
        'Current_state': 'STATE',
        'Current_county': 'COUNTY',
        'Current_state_FIPS': 'STATE_FIPS',
        'Current_county_FIPS': 'COUNTY_FIPS',
        'Current_population': 'Population',
        })
    
    # Store the summed DataFrame for this period in the dictionary
    summed_period_dfs[f"{start_year}_{end_year}"] = summed_df
    
    # Save the combined and summed DataFrames as CSV files
    combined_csv_path = os.path.join(root, 'Data', 'County', 'By_county_clean', f'bycounty_{start_year}_{end_year}.csv')
    summed_csv_path = os.path.join(root, 'Data', 'County', 'Summed_clean', f'summed_{start_year}_{end_year}.csv')

    combined_period_df.to_csv(combined_csv_path, index=False)
    summed_df.to_csv(summed_csv_path, index=False)

        
  
        
  
    
  
    



