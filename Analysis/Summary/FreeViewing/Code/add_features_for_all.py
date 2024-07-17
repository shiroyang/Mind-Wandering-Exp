"""
This code will add temporal and spatial features for all window sizes range(5, 41, 5)
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
input_dir = None
target_file = None
result = None

def save_result():
    global result, target_file
    df = pd.read_csv(target_file)
    df['NumFix_Sim'] = None
    df['AvgFixDisp_Sim'] = None
    df['AvgFixDur_Sim'] = None
    df['CoveredArea'] = None
    # df['nrec'] = None   
    # df['rec'] = None
    df['det'] = None
    df['revdet'] = None
    df['meanline'] = None
    df['maxline'] = None
    df['ent'] = None
    df['relent'] = None
    df['lam'] = None
    df['tt'] = None
    df['corm'] = None
    
    df["num_rec"] = None
    df["weighted_num_rec"] = None   
    df["num_rec_ratio"] = None
    

    for index, row in df.iterrows():
        participant = row['Participant']
        stimuli = row['Stimuli']
        if participant in result and stimuli in result[participant]:
            # Simplified Fixation Features
            df.at[index, 'NumFix_Sim'] = result[participant][stimuli].get('NumFix_Sim', np.nan)
            df.at[index, 'AvgFixDisp_Sim'] = result[participant][stimuli].get('AvgFixDisp_Sim', np.nan)
            df.at[index, 'AvgFixDur_Sim'] = result[participant][stimuli].get('AvgFixDur_Sim', np.nan)
            # Covered Area
            df.at[index, 'CoveredArea'] = result[participant][stimuli]['CoveredArea']
            # RQA Features
            # df.at[index, 'nrec'] = result[participant][stimuli]['nrec']
            # df.at[index, 'rec'] = result[participant][stimuli]['rec']
            df.at[index, 'det'] = result[participant][stimuli]['det']
            df.at[index, 'revdet'] = result[participant][stimuli]['revdet']
            df.at[index, 'meanline'] = result[participant][stimuli]['meanline']
            df.at[index, 'maxline'] = result[participant][stimuli]['maxline']
            df.at[index, 'ent'] = result[participant][stimuli]['ent']
            df.at[index, 'relent'] = result[participant][stimuli]['relent']
            df.at[index, 'lam'] = result[participant][stimuli]['lam']
            df.at[index, 'tt'] = result[participant][stimuli]['tt']
            df.at[index, 'corm'] = result[participant][stimuli]['corm'] 
            
            df.at[index, 'num_rec'] = result[participant][stimuli]['num_rec']
            df.at[index, 'weighted_num_rec'] = result[participant][stimuli]['weighted_num_rec']
            df.at[index, 'num_rec_ratio'] = result[participant][stimuli]['num_rec_ratio']
            
    
    df.to_csv(target_file, index=False)
    
    
def main():
    global result, target_file, input_dir
    for win_size in tqdm(range(4, 45, 4)):
        # Initialize the result
        result = defaultdict((lambda: defaultdict(dict)))
        input_dir = f'./Preprocess/FreeViewing/Scanpath/{win_size}/'
        target_file = f'./Analysis/Summary/FreeViewing/Data/FreeViewing_Summary_{win_size}sec.csv'
        name_list = [name for name in os.listdir(input_dir) if not name.startswith('.')]
        for name in name_list:
            name_dir = os.path.join(input_dir, name)
            file_list = [file for file in os.listdir(name_dir) if not file.startswith('.')]
            for file in file_list:
                file_path = os.path.join(name_dir, file)
                participant = name
                stimuli = file.split('_')[1] + '_' + file.split('_')[2]
                initial_fixation, simplified_fixation = retrieve_simplified_fixation(file_path)
                extract_EM_features(initial_fixation, simplified_fixation, participant, stimuli, result)
                extract_RQA_features(file_path, participant, stimuli, result)
                CalculateCoverdArea(file_path, participant, stimuli, result)
                
        save_result()
                        
    
if __name__ == '__main__':
    main()