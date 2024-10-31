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
file_path = root+'\Data\County\CMRA_Screening_Data.csv'
df = pd.read_csv(file_path)

# List of columns to keep
columns_to_keep = [
    'OBJECTID',
    'Geographic Identifier',
    'County Name',
    'State Geographic Identifier',
    'State Abbreviation',
    'State Name',
    'Mean - Annual total precipitation',
    'Mean - Daily average temperature',
    'Mean - Annual single highest maximum temperature',
    'Mean - Daily minimum temperature',
    'Mean - Daily maximum temperature'
]

# Filter the DataFrame to keep columns that contain any of the specified strings
columns_to_keep = [col for col in df.columns if any(s in col for s in columns_to_keep)]
df_filtered = df[columns_to_keep]

# Drop columns that contain 'RCP 8.5' or 'Late-century'
df_filtered = df_filtered.loc[:, ~df_filtered.columns.str.contains('RCP 8.5|Late-century|Mid-century')]

# Create a new column for change in precipitation

# Create a new column for change in mean daily average temperature
df_filtered['Change in mean daily average temperature [DegF]'] = df['RCP 4.5 Early-century - Mean - Daily average temperature [degF]'] - df['Historical - Mean - Daily average temperature [degF]']

# Create a new column for change in mean daily maximum temperature
df_filtered['Change in mean daily maximum temperature [DegF]'] = df['RCP 4.5 Early-century - Mean - Daily maximum temperature [degF]'] - df['Historical - Mean - Daily maximum temperature [degF]']

# Create a new column for change in mean daily minimum temperature
df_filtered['Change in mean daily minimum temperature [DegF]'] = df['RCP 4.5 Early-century - Mean - Daily minimum temperature [degF]'] - df['Historical - Mean - Daily minimum temperature [degF]']

# Create a new column for change in mean annual single highest maximum temperature
df_filtered['Change in mean annual single highest maximum temperature'] = df['RCP 4.5 Ealry-century - Mean - Annual single highest maximum temperature [degF]'] - df['Historical - Mean - Annual single highest maximum temperature [degF]']

df_filtered = df_filtered.loc[:, ~df_filtered.columns.str.contains('RCP 4.5|Late-century|Mid-century')]

# Output the DataFrame to a new CSV file
df_filtered.to_csv(root+'\Data\County\Chronic_Climate_Clean.csv', index=False)



#Adds Geographic identifiers to the by_county_clean folder for past a current county
import os
import shutil
import pandas as pd

# Function to create the Current county geographic identifier
def create_past_and_current_geographic_identifier(row):
    pstate_fips = str(row['Past_state_FIPS']).lstrip('0')
    pcounty_fips = str(row['Past_county_FIPS']).rstrip('0').rstrip('.').zfill(3)  # Pad county FIPS with leading zeros to ensure it is 3 digits
    cstate_fips = str(row['Current_state_FIPS']).lstrip('0')
    ccounty_fips = str(row['Current_county_FIPS']).zfill(3)  # Pad county FIPS with leading zeros to ensure it is 3 digits
    return cstate_fips + ccounty_fips, pstate_fips + pcounty_fips

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

# Paths
source_folder = root+'/Data/County/by_county_clean'
destination_folder = root+'/Data/County/by_county_clean_geoid'

# Create destination folder if it doesn't exist
if not os.path.exists(destination_folder):
    os.makedirs(destination_folder)

# Copy files containing 'county' from source to destination
for filename in os.listdir(source_folder):
    if 'bycounty' in filename.lower():  # Check if 'county' is in the filename (case-insensitive)
        source_file = os.path.join(source_folder, filename)
        destination_file = os.path.join(destination_folder, filename)
        shutil.copy(source_file, destination_file)

# Process each file in the destination folder
for filename in os.listdir(destination_folder):
    file_path = os.path.join(destination_folder, filename)
    if filename.endswith(('.csv')):  # Check for csv files
        df = pd.read_csv(file_path)
        print(f"Processing file: {filename}")
        #print("Columns in the DataFrame:", df.columns.tolist())
        
        # Check if required columns exist
        required_columns = ['Past_state_FIPS', 'Past_county_FIPS', 'Current_state_FIPS', 'Current_county_FIPS']
        if all(col in df.columns for col in required_columns):
            df[['Current_county_geographic_identifier', 'Past_county_geographic_identifier']] = df.apply(create_past_and_current_geographic_identifier, axis=1, result_type='expand')
            df.to_csv(file_path, index=False)
        else:
            print(f"Missing required columns in file: {filename}")
print("Files processed and saved in the new folder.")