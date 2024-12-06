#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 11:51:50 2024

@author: carinamanitius
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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


agg_mae = pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_Agg_Results/mae_results.csv", index_col=0)
binned_mae = pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_Binned_Results/mae_results.csv", index_col=0)
climate_mae = pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_Climate_Results/mae_results.csv", index_col=0)
count_mae = pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_Count_Results/mae_results.csv", index_col=0)


agg_mae = agg_mae.apply(pd.to_numeric, errors='coerce')
binned_mae = binned_mae.apply(pd.to_numeric, errors='coerce')
climate_mae = climate_mae.apply(pd.to_numeric, errors='coerce')
count_mae = count_mae.apply(pd.to_numeric, errors='coerce')

timeperiod = 'from_2000'

agg_filtered = agg_mae.loc[timeperiod]
binned_filtered = binned_mae.loc[timeperiod]
climate_filtered = climate_mae.loc[timeperiod]
count_filtered = count_mae.loc[timeperiod]

# Combine these rows into a new DataFrame
combined_df = pd.DataFrame({
    'Aggregate': agg_filtered,
    'Binned': binned_filtered,
    'Climate Only': climate_filtered,
    'Count': count_filtered
})

combined_df = combined_df.T


##### PLOTS


### MAE HEATMAP

# Create a heatmap
plt.figure(figsize=(10, 6))  # Adjust the figure size as needed
sns.heatmap(combined_df, annot=True, cmap="YlOrRd", cbar_kws={'label': 'MAE'}, fmt=".3f")

# Set plot labels and title
plt.xlabel("Response Variable")
plt.ylabel("Model Paradigm")
plt.title("MAE Heatmap for Model Paradigm and Response Variables")

plt.savefig(f"{root}/Figures/CM_figs/MAE_heatmap.png", dpi=300, bbox_inches='tight') 









