#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  1 09:25:39 2024

@author: carinamanitius
"""

# import packages
import pandas as pd
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



##### Import data

# Import CMRA data
CMRA = pd.read_csv(f"{root}/Data/County/Chronic_Climate_Clean.csv")

CMRA = CMRA.drop(columns=['OBJECTID', 'County Name', 'State Geographic Identifier', 'State Abbreviation', 'State Name'])

CMRA['Geographic Identifier'] = CMRA['Geographic Identifier'].astype(str)
CMRA['COUNTY_FIPS'] = CMRA['Geographic Identifier'].str[-3:]  # Extract the last 3 characters
CMRA['STATE_FIPS'] = CMRA['Geographic Identifier'].str[:-3]  # Extract everything except the last 3 characters
CMRA['COUNTY_FIPS'] = CMRA['COUNTY_FIPS'].astype(int)
CMRA['STATE_FIPS'] = CMRA['STATE_FIPS'].astype(int)

CMRA = CMRA.drop(columns=['Geographic Identifier', ])

# Import 2000 census data
census_2000 = pd.read_csv(f"{root}/Data/Census/2000_summary.csv")

census_2000 = census_2000.drop(columns=['Unnamed: 0', 'NAME' ,'year'])
census_2000 = census_2000.rename(columns={'state': 'STATE_FIPS', 'county': 'COUNTY_FIPS'})


##### Create list periods 

# Define the start and end year for the migration periods
start_year = 2006
end_year = 2015

# Create migration periods set
migration_periods = []

for year in range(start_year, end_year + 1):
    migration_periods.append((str(year), str(year + 4)))

# Create time period sets 
from_2000_periods = [(str(2000), end_year) for (start, end_year) in migration_periods]
minus_3_periods = [(str(int(start) - 3), end_year) for (start, end_year) in migration_periods]
minus_5_periods = [(str(int(start) - 5), end_year) for (start, end_year) in migration_periods]
minus_10_periods = [(str(max(int(start) - 10, 2000)), end_year) for (start, end_year) in migration_periods]



##### Create longform datasets for each time period

# From_2000
from_2000_dfs = []

for start_year, end_year in from_2000_periods:
    df = pd.read_csv(f"{root}/Data/County/County_sum_with_StormEvents/Inclusive/From_2000/inclusive_merge_countysum_storm_{start_year}_{end_year}.csv")
    from_2000_dfs.append(df)

from_2000_long = pd.concat(from_2000_dfs, ignore_index=True)

# Minus_3
minus_3_df = []

for start_year, end_year in minus_3_periods:
    df = pd.read_csv(f"{root}/Data/County/County_sum_with_StormEvents/Inclusive/Minus_3/inclusive_merge_countysum_storm_{start_year}_{end_year}.csv")
    minus_3_df.append(df)

minus_3_long = pd.concat(minus_3_df, ignore_index=True)

# Minus_5
minus_5_df = []

for start_year, end_year in minus_5_periods:
    df = pd.read_csv(f"{root}/Data/County/County_sum_with_StormEvents/Inclusive/Minus_5/inclusive_merge_countysum_storm_{start_year}_{end_year}.csv")
    minus_5_df.append(df)

minus_5_long = pd.concat(minus_5_df, ignore_index=True)

# Minus_10
minus_10_df = []

for start_year, end_year in minus_10_periods:
    df = pd.read_csv(f"{root}/Data/County/County_sum_with_StormEvents/Inclusive/Minus_10/inclusive_merge_countysum_storm_{start_year}_{end_year}.csv")
    minus_10_df.append(df)

minus_10_long = pd.concat(minus_10_df, ignore_index=True)



##### Clean long datafrmes

dataframes = [from_2000_long, minus_3_long, minus_5_long, minus_10_long]


# # Columns to drop
columns_to_drop = ['NAME',
                    'start_year', 
                    'end_year'
                    ]

from_2000_long = from_2000_long.drop(columns=columns_to_drop)
minus_3_long = minus_3_long.drop(columns=columns_to_drop)
minus_5_long = minus_5_long.drop(columns=columns_to_drop)
minus_10_long = minus_10_long.drop(columns=columns_to_drop)


# merge with CMRA and 2000 census data 

from_2000_long = from_2000_long.merge(census_2000, on=['STATE_FIPS', 'COUNTY_FIPS'], how='left')
minus_3_long = minus_3_long.merge(census_2000, on=['STATE_FIPS', 'COUNTY_FIPS'], how='left')
minus_5_long = minus_5_long.merge(census_2000, on=['STATE_FIPS', 'COUNTY_FIPS'], how='left')
minus_10_long = minus_10_long.merge(census_2000, on=['STATE_FIPS', 'COUNTY_FIPS'], how='left')

from_2000_long = from_2000_long.merge(CMRA, on=['STATE_FIPS', 'COUNTY_FIPS'], how='left')
minus_3_long = minus_3_long.merge(CMRA, on=['STATE_FIPS', 'COUNTY_FIPS'], how='left')
minus_5_long = minus_5_long.merge(CMRA, on=['STATE_FIPS', 'COUNTY_FIPS'], how='left')
minus_10_long = minus_10_long.merge(CMRA, on=['STATE_FIPS', 'COUNTY_FIPS'], how='left')

# final clean
from_2000_long = from_2000_long.dropna()
minus_3_long = minus_3_long.dropna()
minus_5_long = minus_5_long.dropna()
minus_10_long = minus_10_long.dropna()



###### SAVE FILES
from_2000_long.to_csv(f"{root}/Data/FINAL_FOR_MODEL/From_2000.csv")
minus_3_long.to_csv(f"{root}/Data/FINAL_FOR_MODEL/minus_3_long.csv")
minus_5_long.to_csv(f"{root}/Data/FINAL_FOR_MODEL/minus_5_long.csv")
minus_10_long.to_csv(f"{root}/Data/FINAL_FOR_MODEL/minus_10_long.csv")














