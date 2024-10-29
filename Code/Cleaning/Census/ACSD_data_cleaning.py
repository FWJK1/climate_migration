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



##### Download Census data

# import dictionary of variables of interest 
var_dict = pd.read_csv(f"{root}/Code/Cleaning/Census/var_names.csv")

#  set key info

CENSUS_API_KEY = "a122d27a597252e383e8c4c5ea9706a635afbb37"
years = range(2010, 2020, 1)  

# import data and reformat into long form

final_df = pd.DataFrame()

for _, row in var_dict.iterrows():
    census_code = row['census_code']
    variable_name = row['variable_name']
    
    yearly_data = []  # To store data for all years for this variable

    for year in years:
        # Construct the URL
        census_url = f'https://api.census.gov/data/{year}/acs/acs5?get=NAME,{census_code}&for=county:*&key={CENSUS_API_KEY}'
        
        # Make the request and parse the JSON
        response = requests.get(census_url)
        response.raise_for_status()  # Check if the request was successful
        
        # Create a DataFrame from the JSON response, with an additional 'year' column
        df_census = pd.DataFrame(response.json()[1:], columns=response.json()[0])
        df_census['start_year'] = year - 4
        df_census['end_year'] = year

        # Rename the variable column to the human-readable name
        df_census = df_census.rename(columns={census_code: variable_name})
        yearly_data.append(df_census)

    # Concatenate the yearly data for the current variable
    if yearly_data:  # Only concatenate if we have data
        df_variable = pd.concat(yearly_data, ignore_index=True)

        # Merge with the final DataFrame
        if final_df.empty:
            final_df = df_variable
        else:
            final_df = pd.merge(final_df, df_variable, on=['NAME', 'start_year', 'end_year', 'state', 'county'], how='outer')


# import vars to standardize by pop

var_dict_2 = pd.read_csv(f"{root}/Code/Cleaning/Census/var_names_to_regularize.csv")


if 'pop_total' in final_df.columns:
    if final_df['pop_total'].dtype == 'object':  
        final_df['pop_total'] = pd.to_numeric(final_df['pop_total'], errors='coerce').fillna(0).astype(int)

for _, row in var_dict_2.iterrows():
    var_name = row['variable_name']
    new_var_name = row['new_name']
    
    # Check if the variable exists in final_df
    if var_name in final_df.columns:
        # Ensure the variable is converted to int
        if final_df[var_name].dtype == 'object':  
            final_df[var_name] = pd.to_numeric(final_df[var_name], errors='coerce').fillna(0).astype(int)

        # Create the new variable by dividing by total_pop
        final_df[new_var_name] = final_df[var_name] / final_df['pop_total']

# Drop original variables
final_df.drop(columns=var_dict_2['variable_name'].tolist(), inplace=True)

# deal with per household vars

old_variable_names = [
    'total_homes_renter_occupied',
    'total_homes_vaccant',
    'households_families',
    'households_non_families',
    'occupied_housing_units_without_plumbing',
    'occupied_housing_units_without_kitchen',
    'total_homes',
    'pop_total'
]


for var_name in old_variable_names:
    if var_name in final_df.columns:
        if final_df[var_name].dtype == 'object':  
            final_df[var_name] = pd.to_numeric(final_df[var_name], errors='coerce').fillna(0).astype(int)


final_df['per_homes_renter_occupied'] = final_df['total_homes_renter_occupied'] / final_df['total_homes']
final_df['per_homes_vaccant_by_homes'] = final_df['total_homes_vaccant'] / final_df['total_homes']


final_df['per_homes_family'] = final_df['households_families'] / (final_df['households_families'] + final_df['households_non_families'])


final_df['per_homes_without_plumbing'] = final_df['occupied_housing_units_without_plumbing'] / final_df['total_homes']
final_df['per_homes_without_kitchen'] = final_df['occupied_housing_units_without_kitchen'] / final_df['total_homes']

# Drop old variables
final_df = final_df.drop(columns=old_variable_names)

final_df['median_household_income'] = pd.to_numeric(final_df['median_household_income'], errors='coerce').fillna(0).astype(int)
final_df['median_age'] = pd.to_numeric(final_df['median_age'], errors='coerce').fillna(0).astype(int)
final_df['median_house_value_USD'] = pd.to_numeric(final_df['median_house_value_USD'], errors='coerce').fillna(0).astype(int)
final_df['median_rent'] = pd.to_numeric(final_df['median_rent'], errors='coerce').fillna(0).astype(int)

final_df['median_house_value_USD'] = final_df['median_house_value_USD'].replace({np.nan: np.nan}).where(final_df['median_house_value_USD'] >= 0, np.nan)

##### SAVE AS CSV
final_df.to_csv(f"{root}/Data/Census/5_year_summary.csv")





