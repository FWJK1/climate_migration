#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28 14:51:37 2024

@author: carinamanitius
"""

# import packages
import pandas as pd
import requests
import os
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



# Download Census data

# Import dictionary of variables of interest
var_dict = pd.read_csv(f"{root}/Code/Cleaning/Census/var_names_2000.csv")

# Set key info
CENSUS_API_KEY = "a122d27a597252e383e8c4c5ea9706a635afbb37"
year = 2000  

# Initialize an empty DataFrame for final data
final_df = pd.DataFrame()

# Download and reformat Census data
for _, row in var_dict.iterrows():
    census_code = row['census_code']
    variable_name = row['variable_name']

    # Construct the URL for the 2000 Census
    census_url = f'https://api.census.gov/data/{year}/dec/sf3?get=NAME,{census_code}&for=county:*&key={CENSUS_API_KEY}'        
   
    # Make the request and parse the JSON response
    response = requests.get(census_url)
    response.raise_for_status()
        
    # Create a DataFrame from the JSON response
    df_census = pd.DataFrame(response.json()[1:], columns=response.json()[0])

    # Rename the variable column to the human-readable name
    df_census = df_census.rename(columns={census_code: variable_name})

    # Merge with the final DataFrame
    if final_df.empty:
        final_df = df_census
    else:
        final_df = pd.merge(final_df, df_census, on=['NAME', 'state', 'county'], how='outer')

# Add the year column at the end
final_df['year'] = year

old_variable_names = [
    'total_male_in_labour_force',
    'total_male_unemployed',
    'total_female_in_labour_force',
    'total_female_unemployed',
    'median_household_income',
    'median_rent',
    'median_house_price',
]


for var_name in old_variable_names:
    if var_name in final_df.columns:
        if final_df[var_name].dtype == 'object':  
            final_df[var_name] = pd.to_numeric(final_df[var_name], errors='coerce').fillna(0).astype(int)

final_df['unemployment_rate_2000'] = (final_df['total_male_unemployed'] + final_df['total_female_unemployed'])/ (final_df['total_male_in_labour_force'] + final_df['total_female_in_labour_force'])
final_df = final_df.drop(columns=['total_male_unemployed', 'total_female_unemployed', 'total_male_in_labour_force', 'total_female_in_labour_force'])



final_df.to_csv(f"{root}/Data/Census/2000_summary.csv")




















