#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  1 10:57:15 2024

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
from_2000_full = pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/From_2000.csv", usecols=lambda column: column != 'Unnamed: 0')
minus_3_full = pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/minus_3_long.csv", usecols=lambda column: column != 'Unnamed: 0')
minus_5_full = pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/minus_5_long.csv", usecols=lambda column: column != 'Unnamed: 0')
minus_10_full = pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/minus_10_long.csv", usecols=lambda column: column != 'Unnamed: 0')



##### PREP DATA
# Keep only the predictors and the outflow_gross response variable
response_variables = ['Outflow_gross', 'Outflow_pc', 'Inflow_gross', 'Inflow_pc']
response_col = 'Outflow_gross'

predictors = from_2000_full.columns.difference(['Outflow_gross', 'Outflow_pc', 'Inflow_gross', 'Inflow_pc', 'STATE_FIPS', 'COUNTY_FIPS'])

# Create a new DataFrame with only the relevant columns
data = from_2000_full[['STATE_FIPS', 'COUNTY_FIPS', response_col] + list(predictors)]


##### MODEL

# Prepare to store feature importances
group_split = GroupShuffleSplit(n_splits=1, test_size=0.2)

# Create the train-test split
for train_index, test_index in group_split.split(data, groups=data[['STATE_FIPS', 'COUNTY_FIPS']].apply(tuple, axis=1)):
    train_data = data.iloc[train_index]
    test_data = data.iloc[test_index]
    
    X_train = train_data[predictors]
    y_train = train_data[response_col]
    X_test = test_data[predictors]
    y_test = test_data[response_col]
    
    # Define the pipeline
    pipeline = Pipeline([
        ('rf', RandomForestRegressor(n_estimators=100))
    ])
    
    # Fit the model
    pipeline.fit(X_train, y_train)
    
    # Make predictions
    y_pred = pipeline.predict(X_test)
    
    # Calculate regression metrics
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"MAE: {mae}, R²: {r2}")  # Print metrics for the test set
    
    # Get feature importances
    importances = pipeline.named_steps['rf'].feature_importances_
    mean_importances = pd.Series(importances, index=predictors).sort_values(ascending=False)

























