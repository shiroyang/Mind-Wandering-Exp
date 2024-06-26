"""
This code will add the following extra features to the summary file:
1. EM features of simplified fixation based on MultiMatch Simplification algorithm.
2. RQA features of based on Recurrence Quantification Analysis.
3. Covered Area of fixations.

Before running this code, make sure you have excuted the following code:
1. Preprocess/FreeViewing/Code/main_img.py (sync the stimuli images and EM data, and perform I-VT fixation detection)
2. Preprocess/FreeViewing/Code/scanpath_MM.py (trunc 30 seconds of EM data and save it as tsv file for MultiMatch)
3. Analysis/Summary/FreeViewing/Code/create_summary.py (create summary file for step1)
4. This code (select 30 seconds summary data and add simplified fixation features)

Add new columns:
|NumFix_Sim|AvgFixDisp_Sim|AvgFixDur_Sim|
"""
from tqdm import tqdm
import numpy as np
import pandas as pd
import math
import os
from collections import defaultdict
from OOP_MM import retrieve_simplified_fixation, extract_EM_features
from OOP_RQA import extract_RQA_features
from OOP_CoverdArea import CalculateCoverdArea

# Change the parameters in the original code!!!!!!!!!!!!!

# ---------- Global Variables ---------- #
target_file = './Analysis/Summary/SART/Data/SART_Summary_32sec.csv'
result = defaultdict((lambda: defaultdict(dict)))

def save_result():
    global result
    df = pd.read_csv(target_file)
    df['NumFix_Sim'] = None
    df['AvgFixDisp_Sim'] = None
    df['AvgFixDur_Sim'] = None
    df['CoveredArea'] = None
    df['nrec'] = None   
    df['rec'] = None
    df['det'] = None
    df['revdet'] = None
    df['meanline'] = None
    df['maxline'] = None
    df['ent'] = None
    df['relent'] = None
    df['lam'] = None
    df['tt'] = None
    df['corm'] = None

    for index, row in df.iterrows():
        participant = row['Participant']
        stimuli = str(row['Stimuli'])
        if participant in result and stimuli in result[participant]:
            # Simplified Fixation Features
            df.at[index, 'NumFix_Sim'] = result[participant][stimuli].get('NumFix_Sim', np.nan)
            df.at[index, 'AvgFixDisp_Sim'] = result[participant][stimuli].get('AvgFixDisp_Sim', np.nan)
            df.at[index, 'AvgFixDur_Sim'] = result[participant][stimuli].get('AvgFixDur_Sim', np.nan)
            # Covered Area
            df.at[index, 'CoveredArea'] = result[participant][stimuli]['CoveredArea']
            # RQA Features
            df.at[index, 'nrec'] = result[participant][stimuli]['nrec']
            df.at[index, 'rec'] = result[participant][stimuli]['rec']
            df.at[index, 'det'] = result[participant][stimuli]['det']
            df.at[index, 'revdet'] = result[participant][stimuli]['revdet']
            df.at[index, 'meanline'] = result[participant][stimuli]['meanline']
            df.at[index, 'maxline'] = result[participant][stimuli]['maxline']
            df.at[index, 'ent'] = result[participant][stimuli]['ent']
            df.at[index, 'relent'] = result[participant][stimuli]['relent']
            df.at[index, 'lam'] = result[participant][stimuli]['lam']
            df.at[index, 'tt'] = result[participant][stimuli]['tt']
            df.at[index, 'corm'] = result[participant][stimuli]['corm'] 
    
    df.to_csv(target_file, index=False)
    
    
def main():
    global result
    input_dir = './Preprocess/SART/Scanpath/MultiMatch/'
    name_list = [name for name in os.listdir(input_dir) if not name.startswith('.')]
    for name in tqdm(name_list):
        name_dir = os.path.join(input_dir, name)
        file_list = [file for file in os.listdir(name_dir) if not file.startswith('.')]
        for file in file_list:
            file_path = os.path.join(name_dir, file)
            participant = name
            stimuli = file.split('_')[1]
            
            initial_fixation, simplified_fixation = retrieve_simplified_fixation(file_path)
            extract_EM_features(initial_fixation, simplified_fixation, participant, stimuli, result)
            extract_RQA_features(file_path, participant, stimuli, result)
            CalculateCoverdArea(file_path, participant, stimuli, result)
    
    save_result()

    
if __name__ == '__main__':
    main()