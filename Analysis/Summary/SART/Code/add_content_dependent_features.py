"""
This code will add content-dependent features for all window sizes range(4, 61, 4)

Feature1: CD_avg_rt (Content Dependent Average Reaction Time)

Feature2: CD_std_rt (Content Dependent Standard Deviation of Reaction Time)

Feature3: CD_avg_acc (Content Dependent Average Accuracy)

Feature4: CD_mse_median_rt (Content Dependent Mean Squared Error of Median Reaction Time)
まずは300回のSARTのmedian RTを計算する = t_med。
4n秒のwindowを取るとn回SARTを行う = t_i。
CD_mse_median_RT = Sigma(t_i - t_med)**2 / n

Feature5: CD_diff_avg_acc (Content Dependent Difference of Average Accuracy)
まずは300回のSARTのaverage accuracyを計算する = a_avg。
4n秒のwindowを取るとn回SARTを行う = a_i。
CD_diff_avg_Acc = Sigma(a_i - a_avg) / n
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
input_dir = None
target_file = None
result = None

def save_result(result, target_file):
    df = pd.read_csv(target_file)
    df['CD_avg_rt'] = None
    df['CD_std_rt'] = None
    df['CD_avg_acc'] = None
    df['CD_mse_median_rt'] = None
    df['CD_diff_avg_acc'] = None

    for index, row in df.iterrows():
        participant = row['Participant']
        stimuli = row['Stimuli']
        if participant in result and stimuli in result[participant]:
            df.at[index, 'CD_avg_rt'] = result[participant][stimuli].get('CD_avg_rt', np.nan)
            df.at[index, 'CD_std_rt'] = result[participant][stimuli].get('CD_std_rt', np.nan)
            df.at[index, 'CD_avg_acc'] = result[participant][stimuli].get('CD_avg_acc', np.nan)
            df.at[index, 'CD_mse_median_rt'] = result[participant][stimuli].get('CD_mse_median_rt', np.nan)
            df.at[index, 'CD_diff_avg_acc'] = result[participant][stimuli].get('CD_diff_avg_acc', np.nan)
    
    df.to_csv(target_file, index=False)
    
    
def main():
    global result, target_file, input_dir
    
    # Directory containing the data
    input_dir = './Data_Collection/SART/Raw'
    name_list = sorted([file for file in os.listdir(input_dir) if not file.startswith('.')])
    single_data = defaultdict(lambda: defaultdict(list))
    
    # Iterate over each participant
    for name in tqdm(name_list):
        name_dir = os.path.join(input_dir, name)
        folder_dir = os.path.join(name_dir, 'data')
        file_list = sorted([file for file in os.listdir(folder_dir) if file.endswith('.csv')])
        
        trial_cnt = 0
        # Load and aggregate data for each file
        for file_name in file_list:
            file_path = os.path.join(folder_dir, file_name)
            df = pd.read_csv(file_path)

            n = df.shape[0]
            for i in range(n):
                row = df.iloc[i]
                if pd.notna(row['stimulus']):
                    trial_cnt += 1
                    single_data[name]["stimulus"].append(row['stimulus'])
                    if pd.notna(row['stimulus_resp.rt']):
                        RT = abs(row['stimulus_resp.rt'] - row['stimulus_resp.started']) * 1000
                        single_data[name]["stimulus_resp.rt"].append(RT)
                    else:
                        single_data[name]["stimulus_resp.rt"].append(np.nan)
                    single_data[name]["stimulus_resp.corr"].append(row['stimulus_resp.corr'])
                    single_data[name]["prob_resp.keys"].append(row['prob_resp.keys'])
                    if pd.notna(row['prob_resp.keys']):
                        single_data[name]['probe_num'].append(trial_cnt)
        
        # Calculate the median RT
        median_rt = np.median(pd.DataFrame(single_data[name]["stimulus_resp.rt"]).dropna())

        # Calculate the average accuracy
        avg_acc = np.mean(pd.DataFrame(single_data[name]["stimulus_resp.corr"]).dropna())
    
        single_data[name]["median_rt"] = median_rt
        single_data[name]["avg_acc"] = avg_acc
        
        
    for win_size in tqdm(range(4, 61, 4)):
        target_file = f'./Analysis/Summary/SART/Data/SART_Summary_{win_size}sec.csv'
        result = defaultdict((lambda: defaultdict(dict)))
        SART_cnt = win_size // 4
        
        for name in name_list:
            median_rt = single_data[name]["median_rt"]
            avg_acc = single_data[name]["avg_acc"]
            for stimuli, probe_num in enumerate(single_data[name]['probe_num'], 1):
                result[name][stimuli]["CD_avg_rt"] = np.nanmean(single_data[name]["stimulus_resp.rt"][(probe_num - SART_cnt):probe_num])
                result[name][stimuli]["CD_std_rt"] = np.nanstd(single_data[name]["stimulus_resp.rt"][(probe_num - SART_cnt):probe_num])
                result[name][stimuli]["CD_avg_acc"] = np.nanmean(single_data[name]["stimulus_resp.corr"][(probe_num - SART_cnt):probe_num])

                result[name][stimuli]["CD_diff_avg_acc"] = np.nanmean(single_data[name]["stimulus_resp.corr"][(probe_num - SART_cnt):probe_num]) - avg_acc
                
                notna_num = 0
                result[name][stimuli]["CD_mse_median_rt"] = 0
                for RT in single_data[name]["stimulus_resp.rt"][(probe_num - SART_cnt):probe_num]:
                    if pd.notna(RT):
                        notna_num += 1
                        result[name][stimuli]["CD_mse_median_rt"] += (RT - median_rt)**2
                if notna_num != 0:
                    result[name][stimuli]["CD_mse_median_rt"] /= notna_num
                else:
                    result[name][stimuli]["CD_mse_median_rt"] = np.nan
        
        save_result(result=result, target_file=target_file)        

if __name__ == '__main__':
    main()