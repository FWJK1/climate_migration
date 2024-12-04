#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  1 11:45:48 2024

@author: carinamanitius
"""

# import packages
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score
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
datasets = {
    'from_2000': pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/From_2000.csv", usecols=lambda column: column != 'Unnamed: 0'),
    # 'minus_3': pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/minus_3_long.csv", usecols=lambda column: column != 'Unnamed: 0'),
    # 'minus_5': pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/minus_5_long.csv", usecols=lambda column: column != 'Unnamed: 0'),
    # 'minus_10': pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/minus_10_long.csv", usecols=lambda column: column != 'Unnamed: 0')
}

for key in datasets.keys():
    datasets[key].drop(columns=['Population', 'Outflow_gross', 'Inflow_gross'], inplace=True, errors='ignore')
    datasets[key]['Net_pc'] = datasets[key]['Inflow_pc'] - datasets[key]['Outflow_pc']

from_2000_full = datasets['from_2000']
# minus_3_full = datasets['minus_3']
# minus_5_full = datasets['minus_5']
# minus_10_full = datasets['minus_10']

response_variables = ['Outflow_pc', 'Inflow_pc', 'Net_pc']
results = []

##### MODEL
# Prepare to store feature importances
group_split = GroupShuffleSplit(n_splits=1, test_size=0.2)

mae_results = pd.DataFrame(columns=response_variables, index=datasets.keys())
r2_results = pd.DataFrame(columns=response_variables, index=datasets.keys())
importance_results = pd.DataFrame()

for dataset_name, data in datasets.items():
    # Prepare predictors
    predictors = data.columns.difference(response_variables + ['STATE_FIPS', 'COUNTY_FIPS'])

    for response_col in response_variables:
        # Create a new DataFrame with only the relevant columns
        df = data[['STATE_FIPS', 'COUNTY_FIPS', response_col] + list(predictors)]

        # Create the train-test split
        for train_index, test_index in group_split.split(df, groups=df[['STATE_FIPS', 'COUNTY_FIPS']].apply(tuple, axis=1)):
            train_data = df.iloc[train_index]
            test_data = df.iloc[test_index]
            
            X_train = train_data[predictors]
            y_train = train_data[response_col]
            X_test = test_data[predictors]
            y_test = test_data[response_col]
            
            # Define the pipeline
            pipeline = Pipeline([
                ('rf', RandomForestRegressor(n_estimators=500))
            ])
            
            # Fit the model
            pipeline.fit(X_train, y_train)
            
            # Make predictions
            y_pred = pipeline.predict(X_test)
            
            # Calculate regression metrics
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            print(f"dataset_name:    mae = {mae:.4f}, r2 = {r2:.4f}")

            # Store MAE and R² results
            mae_results.loc[dataset_name, response_col] = mae
            r2_results.loc[dataset_name, response_col] = r2
            
            # Get feature importances
            importances = pipeline.named_steps['rf'].feature_importances_
            mean_importances = pd.Series(importances, index=predictors)
            
            # Store mean importances in a results DataFrame
            importance_column = f"{dataset_name}_{response_col}"
            importance_results[importance_column] = mean_importances

# Fill NaN values with 0 or any other value you prefer in the importance_results DataFrame
importance_results.fillna(0, inplace=True)


mae_results.to_csv(f"{root}/Data/FINAL_FOR_MODEL/Simple/mae_results.csv")
r2_results.to_csv(f"{root}/Data/FINAL_FOR_MODEL/Simple/r2_results.csv")
importance_results.to_csv(f"{root}/Data/FINAL_FOR_MODEL/Simple/mean_importance.csv")










