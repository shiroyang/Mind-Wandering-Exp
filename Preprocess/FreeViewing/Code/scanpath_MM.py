"""
This code will extract the scanpath from ./Preprocess/FreeViewing/Data
and save the scanpath to                 ./Preprocess/FreeViewing/Data/Scanpath/MultiMatch/1Y/1Y_Brain_1.csv
"""
import numpy as np
import pandas as pd
import os

def extract_scanpath(file_path):
    name = file_name.split("_")[0]
    if os.path.exists(f"./Preprocess/FreeViewing/Scanpath/MultiMatch/{name}"):
        os.makedirs(f"./Preprocess/FreeViewing/Scanpath/MultiMatch/{name}")
    df = pd.read_csv(file_path, low_memory=False)
    stimuli_list = df["stimuli"].dropna().unique()
    for stimuli in stimuli_list:
        stimuli_df = df[df["stimuli"] == stimuli]
        state = "Focus" if stimuli_df["state"].values[0] == 'num_4' else "MW"
        output_file_path = f"./Preprocess/FreeViewing/Scanpath/MultiMatch/{name}/{name}_{stimuli}_{state}.tsv"
        rows = stimuli_df.shape[0]
        print(rows)
        print(stimuli_df["IVT_fixation_centroid"].iloc[:10])
        
        
        break
        

if __name__ == '__main__':
    if not os.path.exists("./Preprocess/FreeViewing/Scanpath"):
        os.makedirs("./Preprocess/FreeViewing/Scanpath")
    if not os.path.exists("./Preprocess/FreeViewing/Scanpath/MultiMatch"):
        os.makedirs("./Preprocess/FreeViewing/Scanpath/MultiMatch")
    input_dir = "./Preprocess/FreeViewing/Data"
    output_dir = "./Preprocess/FreeViewing/Data/Scanpath/MultiMatch"
    
    for file_name in os.listdir(input_dir):
        if file_name.startswith("."): continue
        extract_scanpath(os.path.join(input_dir, file_name))
        break