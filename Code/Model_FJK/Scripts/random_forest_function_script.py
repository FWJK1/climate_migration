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
import numpy as np
import sys
import datetime

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


# Get current date and time in the format YYYY-MM-DD_HH-MM
current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
output_file = f'{root}/Code/Model_FJK/Output_Logs/{paradigm}_model_output_{current_time}.txt'

# Open the output file for writing
f = open(output_file, 'w')

# Redirect print statements to both the console and the file
class DualWriter:
    def __init__(self, console, file):
        self.console = console
        self.file = file
        
    def write(self, msg):
        self.console.write(msg)
        self.file.write(msg)
        
    def flush(self):
        self.console.flush()
        self.file.flush()

# Save the original sys.stdout and redirect it
original_stdout = sys.stdout
sys.stdout = DualWriter(sys.stdout, f)

from sklearn.model_selection import  GridSearchCV,GroupKFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
def forest_reg_search(X, y, param_grid=None, groups=None,  logged=True, **kwargs,):

    pipeline = Pipeline(steps=[
        ('rf', RandomForestRegressor(**kwargs))
    ])

    print(pipeline)

    if not param_grid:
        param_grid = {
            "rf__n_estimators": [500, 800],  # Number of trees
            "rf__max_depth": [None],  # Max depth of trees
            "rf__min_samples_split": [2, 5, 10],  # Min samples to split a node
            "rf__min_samples_leaf": [1, 2, 4],  # Min samples required at leaf node
            "rf__max_features": ['sqrt'],  # Features to consider for splits
        }


    cv_strategy = GroupKFold(n_splits=3)

    clf = GridSearchCV(pipeline, param_grid,
                       cv=cv_strategy.split(X, y, groups),
                       refit='neg_mean_squared_error',
                       scoring='neg_mean_squared_error', # suggest scoring with mse ... as splitting by train/test makes r2 relationship to variance make less sense
                       n_jobs=-2,
                       verbose=3)
    clf.fit(X, y)


     # Print the MSE for each parameter combination in the grid search
    results = clf.cv_results_
    print('--' * 50)
    print("Mean Squared Errors for each parameter combination:")
    for mean_score, params in zip(results['mean_test_score'], results['params']):
        print(f"Parameters: {params}, MSE: {-mean_score}")  # Convert MSE from negative to positive


    if logged:
        best_model = clf.best_estimator_
        y_pred_log = best_model.predict(X)  # Predictions on log scale
        y_pred = np.expm1(y_pred_log)  # Reverse log transformation (exp(x) - 1)

        # Compute MSE on the original scale (non-log)
        mse_original = mean_squared_error(np.expm1(y), y_pred)  # Exponentiate y to get original scale

        print('--' * 50)
        print(f"Non-log Best Train MSE (original scale): {mse_original}")

    return clf




### Define a function to take negative log
def fjk_log(data):
    # Vectorized transformation for positive and negative values
    data_transformed = np.where(data > 0, np.log1p(data), -np.log1p(np.abs(data)))
    return data_transformed



##### Import data
datasets = {
    'from_2000': pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_{paradigm}_Sets/From_2000.csv", usecols=lambda column: column != 'Unnamed: 0'),
    # 'minus_3': pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_{paradigm}_Sets/minus_3_long.csv", usecols=lambda column: column != 'Unnamed: 0'),
    # 'minus_5': pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_{paradigm}_Sets/minus_5_long.csv", usecols=lambda column: column != 'Unnamed: 0'),
    # 'minus_10': pd.read_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_{paradigm}_Sets/minus_10_long.csv", usecols=lambda column: column != 'Unnamed: 0')
}

for key in datasets.keys():
    datasets[key].drop(columns=['Population', 'Outflow_gross', 'Inflow_gross'], inplace=True, errors='ignore')
    datasets[key]['Net_pc'] = datasets[key]['Inflow_pc'] - datasets[key]['Outflow_pc']

from_2000_full = datasets['from_2000']
# minus_3_full = datasets['minus_3']
# minus_5_full = datasets['minus_5']
# minus_10_full = datasets['minus_10']

response_variables = [
    'Outflow_pc', 
    'Inflow_pc', 
    'Net_pc'
    ]
results = []

##### MODEL
# Prepare to store feature importances
# group_split = ShuffleSplit(n_splits=1, test_size=0.2, random_state=42) ## just regular shuffle split is fine (make it not group)

param_results = pd.DataFrame(columns=response_variables, index=datasets.keys())
mae_results = pd.DataFrame(columns=response_variables, index=datasets.keys())
mse_results = pd.DataFrame(columns=response_variables, index=datasets.keys())
rmse_results = pd.DataFrame(columns=response_variables, index=datasets.keys())
baseline_mae_results = pd.DataFrame(columns=response_variables, index=datasets.keys())

r2_results = pd.DataFrame(columns=response_variables, index=datasets.keys())
importance_results = pd.DataFrame()

for dataset_name, data in datasets.items():
     for response_col in response_variables:
         print(f"Model includes {dataset_name}: {response_col},")


for dataset_name, data in datasets.items():
    # Prepare predictors
    predictors = data.columns.difference(response_variables + ['STATE_FIPS', 'COUNTY_FIPS', 'start_year', 'end_year'])
    df = data[['STATE_FIPS', 'COUNTY_FIPS', 'start_year', 'end_year'] + list(predictors) + list(response_variables)]

    ## create the train and test indices
    train_df = df[~df['end_year'].isin([2018, 2019])]
    test_df = df[df['end_year'].isin([2018, 2019])]
    train_index = train_df.index
    test_index = test_df.index

    train_data = df.iloc[train_index]
    test_data = df.iloc[test_index]

    for response_col in response_variables:
        current_time = datetime.datetime.now().strftime('%d_%H-%M-%S')
        print(f"{'--' *50} \n{'--' *50} \nNow processing dataset: {dataset_name}, on {response_col} at {current_time} ")

        # Calculate the 1st and 99th percentiles for y_train and y_test
        y_train = train_data[response_col]
        y_test = test_data[response_col]

        y_train_1st_percentile = np.percentile(y_train, 1)
        y_train_99th_percentile = np.percentile(y_train, 99)

        y_test_1st_percentile = np.percentile(y_test, 1)
        y_test_99th_percentile = np.percentile(y_test, 99)

        # Filter the train_data and test_data to exclude both the top and bottom 1%
        # print("removing outliers")
        # train_data = train_data[(y_train >= y_train_1st_percentile) & (y_train <= y_train_99th_percentile)]
        # test_data = test_data[(y_test >= y_test_1st_percentile) & (y_test <= y_test_99th_percentile)]

        # redefine the splits
        X_train = train_data[predictors]
        y_train = train_data[response_col]
        X_test = test_data[predictors]
        y_test = test_data[response_col]



        y_train_positive = np.abs(y_train)
        y_test_positive = np.abs(y_test)    


        ## Remove outliers and make it logarithmic
        y_train = fjk_log(y_train)
        y_test = fjk_log(y_test)



        clf = forest_reg_search(X_train, y_train, groups=train_data[['STATE_FIPS', 'COUNTY_FIPS']].apply(tuple, axis=1) )

    
        # Make predictions
        best_model = clf.best_estimator_
        print(f"\n\n{'--' * 50}  \n{dataset_name}: {response_col} Best Model:")
        print(clf.best_params_)
        print( f"Train Log-side MSE score: {-clf.best_score_:.5f}, (See above for original scale train score)")

        
        y_pred = best_model.predict(X_test)
        y_pred = np.expm1(y_pred)
        y_test = np.expm1(y_test)
        
        
        # Calculate regression metrics
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        baseline_pred = np.full_like(y_test, y_test.mean())  # Predict the mean value for all instances
        baseline_mae = mean_absolute_error(y_test, baseline_pred)
        baseline_pred_median = np.full_like(y_test, np.median(y_test))
        baseline_mae_median = mean_absolute_error(y_test, baseline_pred_median)

        current_time = datetime.datetime.now().strftime('%d_%H-%M-%S')
        

        print(f"Test Set Scores: ")
        print(f"    Mean Squared Error (MSE): {mse: 5f}")
        print(f"    RMSE on the full dataset: {rmse:.5f}")
        print(f"    R²: {r2: 5f}")
        print(f"    MAE : {mae: 5f}")
        print(f"    Baseline MAE (mean prediction): {baseline_mae: 5f}")
        print(f"    Baseline MAE (median prediction): {baseline_mae_median: 5f}")

        print(f"RESULTS END at {current_time} \n\n ")
        

        # Store MAE and R² results
        param_results.loc[dataset_name, response_col] = str(clf.best_params_)
        mse_results.loc[dataset_name, response_col] = mse
        rmse_results.loc[dataset_name, response_col] = rmse
        mae_results.loc[dataset_name, response_col] = mae
        r2_results.loc[dataset_name, response_col] = r2
        baseline_mae_results.loc[dataset_name, response_col] = baseline_mae

        
        # Get feature importances
        rf_model = best_model.named_steps['rf']
        feature_importances = rf_model.feature_importances_
        mean_importances = pd.Series(feature_importances, index=predictors)
        
        # Store mean importances in a results DataFrame
        importance_column = f"{dataset_name}_{response_col}"
        importance_results[importance_column] = mean_importances

# Fill NaN values with 0 in the importance_results DataFrame
importance_results.fillna(0, inplace=True)

param_results.to_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_{paradigm}_Results/param_results.csv")
mae_results.to_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_{paradigm}_Results/mae_results.csv")
mse_results.to_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_{paradigm}_Results/mse_results.csv")
rmse_results.to_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_{paradigm}_Results/rmse_results.csv")
baseline_mae_results.to_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_{paradigm}_Results/baseline_mae_results.csv")

r2_results.to_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_{paradigm}_Results/r2_results.csv")
importance_results.to_csv(f"{root}/Data/FINAL_FOR_MODEL/FJK_{paradigm}_Results/mean_importance.csv")


## cleanup
# Restore the original sys.stdout (console printing)
sys.stdout = original_stdout

# Close the file after the process is complete
f.close()
print("File Closed")