#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  1 11:45:48 2024

@author: carinamanitius & fitzkoch
"""

# import packages
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import ShuffleSplit, GroupShuffleSplit
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

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import RandomizedSearchCV, GridSearchCV, KFold, train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import make_scorer, mean_squared_error, r2_score, mean_absolute_error
def forest_reg_search(X, y, param_grid=None, groups=None, **kwargs):

    pipeline = Pipeline(steps=[
        ('rf', RandomForestRegressor(**kwargs))
    ])

    print(pipeline)

    if not param_grid:
        param_grid = {
            "rf__n_estimators": [100, 200, 500],  # Number of trees
            "rf__max_depth": [1, 3, 5, 10, None],  # Max depth of trees
            "rf__min_samples_split": [2, 5, 10],  # Min samples to split a node
            "rf__min_samples_leaf": [1, 2, 4],  # Min samples required at leaf node
            "rf__max_features": ['sqrt'],  # Features to consider for splits
        }

    cv_strategy = KFold(n_splits=5)

    clf = GridSearchCV(pipeline, param_grid,
                       cv=cv_strategy,
                       refit='neg_mean_squared_error',
                       scoring='neg_mean_squared_error', # suggest scoring with mse ... as splitting by train/test makes r2 relationship to variance make less sense
                       n_jobs=-1,
                       verbose=3)
    clf.fit(X, y)

    return clf

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

length = len(from_2000_full)
train_index, test_index = train_test_split(range(length), test_size=0.2, random_state=42)

response_variables = ['Outflow_pc', 'Inflow_pc', 'Net_pc']
results = []

##### MODEL
# Prepare to store feature importances
group_split = ShuffleSplit(n_splits=1, test_size=0.2, random_state=42) ## just regular shuffle split is fine (make it not group)

param_results = pd.DataFrame(columns=response_variables, index=datasets.keys())
mae_results = pd.DataFrame(columns=response_variables, index=datasets.keys())
mse_results = pd.DataFrame(columns=response_variables, index=datasets.keys())
r2_results = pd.DataFrame(columns=response_variables, index=datasets.keys())
importance_results = pd.DataFrame()



for dataset_name, data in datasets.items():
    # Prepare predictors
    predictors = data.columns.difference(response_variables + ['STATE_FIPS', 'COUNTY_FIPS'])
    df = data[['STATE_FIPS', 'COUNTY_FIPS'] + list(predictors) + list(response_variables)]
    train_data = df.iloc[train_index]
    test_data = df.iloc[test_index]

    for response_col in response_variables:
    # Create a new DataFrame with only the relevant columns
        
        X_train = train_data[predictors]
        y_train = train_data[response_col]
        X_test = test_data[predictors]
        y_test = test_data[response_col]


        clf = forest_reg_search(X_train, y_train, groups=train_data[['STATE_FIPS', 'COUNTY_FIPS']].apply(tuple, axis=1) )

    
        # Make predictions
        best_model = clf.best_estimator_
        print("RESULTS \n\n ")
        print(clf.best_params_ , f"gives:{clf.best_score_:.5f}")
        y_pred = best_model.predict(X_test)
        
        
        # Calculate regression metrics
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        print(f"Mean Squared Error (MSE): {mse}")
        print(f"R²: {r2}")
        print(f"MAE : {mae}")
        print("RESULTS END \n\n ")
        

        # Store MAE and R² results
        param_results.loc[dataset_name, response_col] = str(clf.best_params_)
        mse_results.loc[dataset_name, response_col] = mse
        mae_results.loc[dataset_name, response_col] = mae
        r2_results.loc[dataset_name, response_col] = r2
        
        # Get feature importances
        rf_model = best_model.named_steps['rf']
        feature_importances = rf_model.feature_importances_
        mean_importances = pd.Series(feature_importances, index=predictors)
        
        # Store mean importances in a results DataFrame
        importance_column = f"{dataset_name}_{response_col}"
        importance_results[importance_column] = mean_importances

# Fill NaN values with 0 in the importance_results DataFrame
importance_results.fillna(0, inplace=True)

param_results.to_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_Results/param_results.csv")
mae_results.to_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_Results/mae_results.csv")
r2_results.to_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_Results/r2_results.csv")
importance_results.to_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_Results/mean_importance.csv")

