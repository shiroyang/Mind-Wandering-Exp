"""
This code will add the following extra features to the summary file:
1. EM features of simplified fixation based on MultiMatch Simplification algorithm.
2. RQA features of based on Recurrence Quantification Analysis.
3. Covered Area of fixations.

Before running this code, make sure you have executed the following code:
1. Preprocess/FreeViewing/Code/main_img.py (sync the stimuli images and EM data, and perform I-VT fixation detection)
2. Preprocess/FreeViewing/Code/scanpath_MM.py (trunc 30 seconds of EM data and save it as tsv file for MultiMatch)
3. Analysis/Summary/FreeViewing/Code/create_summary.py (create summary file for step1)
4. This code (select 30 seconds summary data and add simplified fixation features)

Add new columns:
|NumFix_Sim|AvgFixDisp_Sim|AvgFixDur_Sim|CoveredArea|nrec|rec|det|revdet|meanline|maxline|ent|relent|lam|tt|corm|
|NumFix_Sim_diff|AvgFixDisp_Sim_diff|AvgFixDur_Sim_diff|CoveredArea_diff|nrec_diff|rec_diff|det_diff|revdet_diff|meanline_diff|maxline_diff|ent_diff|relent_diff|lam_diff|tt_diff|corm_diff|
"""
from tqdm import tqdm
import numpy as np
import pandas as pd
import os
from collections import defaultdict
from OOP_MM import retrieve_simplified_fixation, extract_EM_features
from OOP_RQA import extract_RQA_features
from OOP_CoverdArea import CalculateCoverdArea

# Change the parameters in the original code!!!!!!!!!!!!!

# ---------- Global Variables ---------- #
taget_file = './Analysis/Summary/FreeViewing/Data/FreeViewing_Summary_30sec.csv'
result_last = defaultdict((lambda: defaultdict(dict)))
result_first = defaultdict((lambda: defaultdict(dict)))
result_diff = defaultdict((lambda: defaultdict(dict)))

def save_result():
    global result_last, result_first, result_diff
    df = pd.read_csv(taget_file)
    columns = [
        'NumFix_Sim', 'AvgFixDisp_Sim', 'AvgFixDur_Sim', 'CoveredArea', 'nrec', 'rec', 'det', 'revdet', 
        'meanline', 'maxline', 'ent', 'relent', 'lam', 'tt', 'corm'
    ]
    
    for col in columns:
        df[col] = None
        df[f'{col}_diff'] = None

    for index, row in df.iterrows():
        participant = row['Participant']
        stimuli = row['Stimuli']
        if participant in result_last and stimuli in result_last[participant]:
            # Last 30 seconds features
            for col in columns:
                df.at[index, col] = result_last[participant][stimuli].get(col, np.nan)
            
            # Diff features (Last 30 seconds - First 30 seconds)
            for col in columns:
                df.at[index, f'{col}_diff'] = result_diff[participant][stimuli].get(col, np.nan)
    
    df.to_csv(taget_file, index=False)
    
    
def compute_features(input_dir, result_dict):
    name_list = [name for name in os.listdir(input_dir) if not name.startswith('.')]
    for name in tqdm(name_list):
        name_dir = os.path.join(input_dir, name)
        file_list = [file for file in os.listdir(name_dir) if not file.startswith('.')]
        for file in file_list:
            file_path = os.path.join(name_dir, file)
            participant = name
            stimuli = file.split('_')[1] + '_' + file.split('_')[2]
            
            initial_fixation, simplified_fixation = retrieve_simplified_fixation(file_path)
            extract_EM_features(initial_fixation, simplified_fixation, participant, stimuli, result_dict)
            extract_RQA_features(file_path, participant, stimuli, result_dict)
            CalculateCoverdArea(file_path, participant, stimuli, result_dict)

def compute_diffs(result_last, result_first, result_diff):
    columns = [
        'NumFix_Sim', 'AvgFixDisp_Sim', 'AvgFixDur_Sim', 'CoveredArea', 'nrec', 'rec', 'det', 'revdet', 
        'meanline', 'maxline', 'ent', 'relent', 'lam', 'tt', 'corm'
    ]
    for participant in result_last:
        for stimuli in result_last[participant]:
            for col in columns:
                result_diff[participant][stimuli][col] = (
                    result_last[participant][stimuli].get(col, 0) - 
                    result_first[participant][stimuli].get(col, 0)
                )

def main():
    global result_last, result_first, result_diff

    input_dir_last = './Preprocess/FreeViewing/Scanpath/MultiMatch/'
    input_dir_first = './Preprocess/FreeViewing/Scanpath/Reversed/'

    # Compute features for the last 30 seconds
    compute_features(input_dir_last, result_last)
    
    # Compute features for the first 30 seconds
    compute_features(input_dir_first, result_first)
    
    # Compute diff features
    compute_diffs(result_last, result_first, result_diff)

    # Save the results
    save_result()
    
    
if __name__ == '__main__':
    main()
