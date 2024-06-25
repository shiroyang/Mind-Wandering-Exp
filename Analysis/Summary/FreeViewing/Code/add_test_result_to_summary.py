"""
This code will handle FreeViewing test results and add them to the summary data.
"""
from tqdm import tqdm
import numpy as np
import pandas as pd
import math
import os
from collections import defaultdict


# Change the parameters in the original code!!!!!!!!!!!!!

# ---------- Global Variables ---------- #
taget_file = './Analysis/Summary/FreeViewing/Data/FreeViewing_Summary_30sec.csv'
result = defaultdict((lambda: defaultdict(dict)))

id_to_image = {1:"HongKong_1", 2:"HongKong_3", 3:"India_1", 4:"India_3", 5:"London_1", 6:"London_3", 7:"NYC_1", 8:"NYC_4",
               9:"Singapore_1", 10:"Singapore_3", 11:"Vietnam_1", 12:"Vietnam_2", 13:"Brazil_1", 14:"Brazil_3", 15:"France_3", 16:"France_1",
               17:"Italy_1", 18:"Italy_4", 19:"Mexico_1", 20:"Mexico_3", 21:"Russia_1", 22:"Russia_3", 23:"Sweden_2", 24:"Sweden_4"}

def save_result():
    global result
    df = pd.read_csv(taget_file)
    df['Test'] = None
    
    for index, row in df.iterrows():
        participant = row['Participant']
        stimuli = row['Stimuli']
        if participant in result and stimuli in result[participant]:
            # Simplified Fixation Features
            df.at[index, 'Test'] = result[participant][stimuli].get('Test', np.nan)
    
    df.to_csv(taget_file, index=False)
    
    
def extract_test_result(filepath, result):
    df = pd.read_csv(filepath)
    for idx, row in df.iterrows():
        if pd.isna(row["imageName"]): continue
        image_id = int(row["imageName"].split("/")[1].split(".")[0])
        resp = row["key_resp_2.keys"]
        correct = 0
        if image_id % 2 == 0 and resp == "num_6":
            correct = 1
        elif image_id % 2 == 1 and resp == "num_4":
            correct = 1
            
        result[row["participant"]][id_to_image[image_id]]["Test"] = correct
    
def main():
    global result
    input_dir = './Data_Collection/FreeViewing/Raw/'
    name_list = [name for name in os.listdir(input_dir) if not name.startswith('.')]
    for name in tqdm(name_list):
        name_dir = os.path.join(input_dir, name)
        folder_dir = os.path.join(name_dir, "data")
        filename = [file for file in os.listdir(folder_dir) if file.endswith(".csv")][0]
        filepath = os.path.join(folder_dir, filename)
        
        extract_test_result(filepath, result)
        
    save_result()
    
    
if __name__ == '__main__':
    main()