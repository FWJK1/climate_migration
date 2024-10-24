import os
 
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

import pandas as pd

# Load the data into a dataframe
file_path = r'Data\County\CMRA_Screening_Data.csv'
df = pd.read_csv(file_path)

#Drop columns containing 'RCP 8.5' in their name
df = df.drop(df.columns[df.columns.str.contains('RCP 8.5')], axis=1)
#removes all late century columns 
df = df.drop(df.columns[df.columns.str.contains('Late-century')], axis=1)
#Removes columns about annual number of days with recipitation greater than 1, 2, 3, and 4 inches
df = df.drop(df.columns[df.columns.str.contains('Annual number of days with total precipitation')], axis=1)
#not sure if we need these
df = df.drop(df.columns[df.columns.str.contains('Daily minimum temperature')], axis=1)
df = df.drop(df.columns[df.columns.str.contains('Daily maximum temperature')], axis=1)
df = df.drop(df.columns[df.columns.str.contains('Max')], axis=1)
df = df.drop(df.columns[df.columns.str.contains('Min')], axis=1)

#dropped columns about number od days with less than 0.01 inches of precipitation
df = df.drop(df.columns[df.columns.str.contains('0.01')], axis=1)

# Identify the columns that contain 'building value' or 'agricultural value'
value_columns = [col for col in df.columns if 'building value' in col or 'agricultural value' in col]
# Create a new column that sums these columns
df['Total Expected Annual Loss'] = df[value_columns].sum(axis=1)

#gets rid of rows for Mariana Islands, American Somoa, Virgin Islands, and Guam
values_to_delete = ['AS', 'GU', 'MP', 'VI']
# Filter out rows with the specified values in the 'State Abbreviation' column
df = df[~df['State Abbreviation'].isin(values_to_delete)]


#Adding Geographic identifiers. still trying to get this to work but I'm close
# import shutil

# # Function to create the Current county geographic identifier
# def create_past_and_current_geographic_identifier(row):
#     pstate_fips = str(row['Past_state_FIPS'])
#     pcounty_fips = str(row['Past_county_FIPS']).zfill(3)  # Pad county FIPS with leading zeros to ensure it is 3 digits
#     cstate_fips = str(row['Current_state_FIPS'])
#     ccounty_fips = str(row['Current_county_FIPS']).zfill(3)  # Pad county FIPS with leading zeros to ensure it is 3 digits
#     return cstate_fips + ccounty_fips, pstate_fips + pcounty_fips

# # Paths
# source_folder = 'root/data/county'
# destination_folder = 'root/data/county/county-to-county-with-geoid'

# # Create destination folder if it doesn't exist
# if not os.path.exists(destination_folder):
#     os.makedirs(destination_folder)

# # Copy files from source to destination
# for filename in os.listdir(source_folder):
#     source_file = os.path.join(source_folder, filename)
#     destination_file = os.path.join(destination_folder, filename)
#     shutil.copy(source_file, destination_file)

# # Process each file in the destination folder
# for filename in os.listdir(destination_folder):
#     file_path = os.path.join(destination_folder, filename)
#     if filename.endswith('.csv'):  # Assuming the files are CSVs
#         df = pd.read_csv(file_path)
#         df[['Current_county_geographic_identifier', 'Past_county_geographic_identifier']] = df.apply(create_past_and_current_geographic_identifier, axis=1, result_type='expand')
#         df.to_csv(file_path, index=False)