#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  1 14:27:14 2024

@author: carinamanitius
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

paradigm = "Climate"

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


#### IMPORT DATA

mae_results = pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_Climate_Results/mae_results.csv", index_col=0)
mse_results = pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_Climate_Results/mse_results.csv", index_col=0)
rmse_results = pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_Climate_Results/mse_results.csv", index_col=0)


r2_results = pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_Climate_Results/r2_results.csv", index_col=0)
importance_results = pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_Climate_Results/mean_importance.csv", index_col=0)


mae_results = mae_results.apply(pd.to_numeric, errors='coerce')
r2_results = r2_results.apply(pd.to_numeric, errors='coerce')
importance_results = importance_results.apply(pd.to_numeric, errors='coerce')

##### PLOTS


### MAE HEATMAP

# Create a heatmap
plt.figure(figsize=(10, 6))  # Adjust the figure size as needed
sns.heatmap(mae_results, annot=True, cmap="YlOrRd", cbar_kws={'label': 'MAE'}, fmt=".3f")

# Set plot labels and title
plt.xlabel("Response Variable")
plt.ylabel("Dataset")
plt.title(f"{paradigm} Model:MAE Heatmap for Datasets and Response Variables")

plt.savefig(f"{root}/Figures/FJK_Climate_Results/MAE_heatmap.png", dpi=300, bbox_inches='tight') 

# Display the heatmap

### MSE HEATMAP

# Create a heatmap
plt.figure(figsize=(10, 6))  # Adjust the figure size as needed
sns.heatmap(mae_results, annot=True, cmap="YlOrRd", cbar_kws={'label': 'MAE'}, fmt=".3f")

# Set plot labels and title
plt.xlabel("Response Variable")
plt.ylabel("Dataset")
plt.title(f"{paradigm} Model:MSE Heatmap for Datasets and Response Variables")

plt.savefig(f"{root}/Figures/FJK_Climate_Results/MSE_heatmap.png", dpi=300, bbox_inches='tight') 

# Display the heatmap
 

 ### RMSE HEATMAP

# Create a heatmap
plt.figure(figsize=(10, 6))  # Adjust the figure size as needed
sns.heatmap(rmse_results, annot=True, cmap="YlOrRd", cbar_kws={'label': 'MAE'}, fmt=".3f")

# Set plot labels and title
plt.xlabel("Response Variable")
plt.ylabel("Dataset")
plt.title(f"{paradigm} Model:RMSE Heatmap for Datasets and Response Variables")

plt.savefig(f"{root}/Figures/FJK_Climate_Results/RMSE_heatmap.png", dpi=300, bbox_inches='tight') 

# Display the heatmap
 
 


### R2 HEATMAP

# Create the heatmap
plt.figure(figsize=(10, 6))  # Adjust the figure size as needed
sns.heatmap(r2_results, annot=True, cmap="RdYlGn", cbar_kws={'label': 'R²'}, fmt=".3f", vmin=-1, vmax=1)

# Set plot labels and title
plt.xlabel("Response Variable")
plt.ylabel("Dataset")
plt.title(f"{paradigm} Model:R² Heatmap for Datasets and Response Variables")

plt.savefig(f"{root}/Figures/FJK_Climate_Results/R2_heatmap.png", dpi=300, bbox_inches='tight') 

# Display the heatmap
 


### MEAN IMPORTANCE HEATMAP

# Calculate the average importance across all columns
average_importance = importance_results.mean(axis=1)

# Sort the DataFrame based on the average importance
importance_results_sorted = importance_results.loc[average_importance.sort_values(ascending=False).index]

# Plot the heatmap using the sorted DataFrame
plt.figure(figsize=(12, 8))  # Adjust figure size as needed
sns.heatmap(importance_results_sorted, annot=True, cmap="Blues", cbar_kws={'label': 'Mean Importance'}, fmt=".3f")

# Set plot title and labels
plt.title(f"{paradigm} Model:Mean Feature Importance Heatmap (Ordered by Average Importance)")
plt.xlabel("Response Variable")
plt.ylabel("Predictor")

# Save the heatmap as a PNG file
plt.savefig(f"{root}/Figures/FJK_Climate_Results/importance_heatmap_full.png", dpi=300, bbox_inches='tight') 

# Display the heatmap
 



### TOP 20 only (average)

# Get the top 20 features based on average importance across all columns
top_features = importance_results.mean(axis=1).nlargest(20).index

# Filter the DataFrame to include only the top features
filtered_importance_results = importance_results.loc[top_features]

# Plot the heatmap using the filtered DataFrame
plt.figure(figsize=(12, 8))  # Adjust figure size as needed
sns.heatmap(filtered_importance_results, annot=True, cmap="Blues", cbar_kws={'label': 'Mean Importance'}, fmt=".3f")

# Set plot title and labels
plt.title(f"{paradigm} Model:Mean Feature Importance Heatmap (Top 20 Features)")
plt.xlabel("Response Variable")
plt.ylabel("Predictor")

# Save the heatmap as a PNG file
plt.savefig(f"{root}/Figures/FJK_Climate_Results/importance_heatmap_top20.png", dpi=300, bbox_inches='tight')

# Display the heatmap
 


### ALL IN TOP 10 (in any model)

# Identify features that are in the top 10 importance for any column
top_10_features = importance_results.apply(lambda x: x.nlargest(10).index, axis=0).stack().unique()

# Filter the DataFrame to include only those features
filtered_importance_results = importance_results.loc[top_10_features]

# Calculate the average importance across all columns for sorting
average_importance = filtered_importance_results.mean(axis=1)

# Sort the filtered DataFrame based on the average importance
importance_results_sorted = filtered_importance_results.loc[average_importance.sort_values(ascending=False).index]

# Plot the heatmap using the sorted DataFrame
plt.figure(figsize=(12, 8))  # Adjust figure size as needed
sns.heatmap(importance_results_sorted, annot=True, cmap="Blues", cbar_kws={'label': 'Mean Importance'}, fmt=".3f")

# Set plot title and labels
plt.title(f"{paradigm} Model:Mean Feature Importance Heatmap (Top 10 Features in Any Column)")
plt.xlabel("Response Variable")
plt.ylabel("Predictor")

# Save the heatmap as a PNG file
plt.savefig(f"{root}/Figures/FJK_Climate_Results/importance_heatmap_top10_any.png", dpi=300, bbox_inches='tight')

# Display the heatmap
 



### CLIMATE IMPORTANCE 

# Define the features of interest

# Combine the lists of features
features_of_interest = ['property_damage', 'deaths']

# Filter the importance_results DataFrame to include only the specified features
importance_results_temp = importance_results.loc[features_of_interest]

# Calculate the average importance across all columns
average_importance = importance_results_temp.mean(axis=1)

# Sort the DataFrame based on the average importance
importance_results_sorted = importance_results_temp.loc[average_importance.sort_values(ascending=False).index]

# Plot the heatmap using the sorted DataFrame
plt.figure(figsize=(12, 8))  # Adjust figure size as needed
sns.heatmap(importance_results_sorted, annot=True, cmap="Blues", cbar_kws={'label': 'Mean Importance'}, fmt=".3f")

# Set plot title and labels
plt.title(f"{paradigm} Model:Mean Feature Importance Heatmap for Total Properties and Deaths (Ordered by Average Importance)")
plt.xlabel("Response Variable")
plt.ylabel("Predictor")

# Save the heatmap as a PNG file
plt.savefig(f"{root}/Figures/FJK_Climate_Results/importance_heatmap_property_death.png", dpi=300, bbox_inches='tight')

# Display the heatmap
 







### BAR PLOT MAE AND R2

# Melt the results DataFrame for MAE to long format if needed
mae_long = mae_results.reset_index().melt(id_vars='index', var_name='Response Variable', value_name='MAE')
mae_long.rename(columns={'index': 'Dataset'}, inplace=True)

plt.figure(figsize=(10, 6))
sns.barplot(data=mae_long, x='Dataset', y='MAE', hue='Response Variable')
plt.title(f"{paradigm} Model:MAE Comparison Across Datasets and Response Variables")
plt.ylabel("Mean Absolute Error")
plt.savefig(f"{root}/Figures/FJK_Climate_Results/MSE_bar.png", dpi=300, bbox_inches='tight')
 


### BOX PLOT FEATURE IMPORTANCE 

# Flatten mean_importance_results if it has a MultiIndex, then melt to long form
importance_long = importance_results.stack().reset_index()
importance_long.columns = ['Predictor', 'Dataset_Response', 'Importance']

plt.figure(figsize=(12, 6))
sns.boxplot(data=importance_long, x='Predictor', y='Importance')
plt.xticks(rotation=90)
plt.title(f"{paradigm} Model:Distribution of Feature Importances Across Datasets and Response Variables")
plt.savefig(f"{root}/Figures/FJK_Climate_Results/feature_boxplot.png", dpi=300, bbox_inches='tight')

 




### COMPARE MAE AND R2

# Assuming mae_results and r2_results are combined in one DataFrame
performance_df = mae_results.melt(var_name='Response Variable', value_name='MAE').join(
    r2_results.melt(var_name='Response Variable', value_name='R2')['R2']
)

# Create a scatter plot of MAE vs R²
plt.figure(figsize=(10, 6))
sns.scatterplot(data=performance_df, x='MAE', y='R2', hue='Response Variable', style='Response Variable', s=100)

# Set plot title and labels
plt.title(f"{paradigm} Model:Scatter Plot of MAE vs R² Across Datasets and Response Variables")
plt.xlabel("Mean Absolute Error (MAE)")
plt.ylabel("R² Value")
plt.legend(title='Response Variable')

# Save the scatter plot as a PNG file
plt.savefig(f"{root}/Figures/FJK_Climate_Results/MAE_R2_scatterplot.png", dpi=300, bbox_inches='tight')

# Display the plot
 
paradigm = "Climate"

baseline_mae_results = pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_{paradigm}_Results/baseline_mae_results.csv", index_col=0)
baseline_mae_results = baseline_mae_results.apply(pd.to_numeric, errors='coerce')
percentage_diff_df = ((baseline_mae_results - mae_results) / baseline_mae_results) * 100
plt.figure(figsize=(10, 6))
sns.heatmap(percentage_diff_df, annot=True, cmap="coolwarm", center=0, fmt=".3f")
plt.title(f'Percentage Improvement from Baseline (Median) to {paradigm} Model MAE')
plt.savefig(f"{root}/Figures/FJK_{paradigm}_Results/MAE_differential_heatplot.png", dpi=300, bbox_inches='tight')