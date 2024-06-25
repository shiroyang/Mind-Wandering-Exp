# Scanpath for SART
# Truncate the scanpath data to the MultiMatch format
# Each file has 5 probes, and each file is labeled from 1 to 3, where the offset is from 0 to 2
# So the number of stimuli is offset * 5 + current_probe

import numpy as np
import pandas as pd
import os

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SAMPLE_RATE = 60
FIXATION_INDENTIFIER = "IVT_fixation_centroid"
TRUNC_FRAMES = 32 * 60

def to_pixel(x, y):
    return x * SCREEN_WIDTH, y * SCREEN_HEIGHT

def extract_scanpath(file_path):
    name = os.path.splitext(os.path.basename(file_path))[0].split("_")[0]
    if not os.path.exists(f"./Preprocess/SART/Scanpath/MultiMatch/{name}"):
        os.makedirs(f"./Preprocess/SART/Scanpath/MultiMatch/{name}")
    df = pd.read_csv(file_path, low_memory=False)
    offset = int(file_path.split("_")[-1].split(".")[0]) - 1
    n = df.shape[0]
    cur_probe = 0
    probe_number = None
    state = None
    idx = 0
    # First crop the raw data for each probe
    while idx < n-1:
        prev = df.iloc[idx]
        next = df.iloc[idx+1]
        if pd.isna(prev["state"]) and not pd.isna(next["state"]):
            cur_probe += 1
            state = "Focus" if next["state"] == 'num_4' else "MW"
            probe_number = offset * 5 + cur_probe
            j = idx + 1
            fixation_centroid = []
            while j < n and not pd.isna(df.iloc[j]["state"]):
                fixation_centroid.append(eval(df.iloc[j][FIXATION_INDENTIFIER]))
                j += 1
            idx = j
            
            fixation_centroid = fixation_centroid[-TRUNC_FRAMES:]
            
            # Then convert the fixation centroid to {"start_x", "start_y", "duration"}
            output_file_path = f"./Preprocess/SART/Scanpath/MultiMatch/{name}/{name}_{probe_number}_{state}.tsv"
            data = pd.DataFrame(columns=["start_x", "start_y", "duration"])
            x_list = []
            y_list = []
            duration_list = []
            k = 0
            
            while k < len(fixation_centroid) - 1:
                if fixation_centroid[k][0] is None or fixation_centroid[k][1] is None:
                    k += 1
                    continue
                x, y = to_pixel(fixation_centroid[k][0], fixation_centroid[k][1])
                x_list.append(x)
                y_list.append(y)
                l = k + 1
                while l < len(fixation_centroid) and fixation_centroid[l] == fixation_centroid[k]:
                    l += 1
                # duration in seconds
                duration = (l - k) / SAMPLE_RATE
                duration_list.append(duration)
                k = l        

            data["start_x"] = x_list
            data["start_y"] = y_list
            data["duration"] = duration_list
            data.to_csv(output_file_path, sep="\t", index=False)
            
        idx += 1
        
    # stimuli_list = df["stimuli"].dropna().unique()
    # for stimuli in stimuli_list:
    #     stimuli_df = df[df["stimuli"] == stimuli]
        
    #     # Change this if you want to truncate the scanpath data
    #     stimuli_df = stimuli_df[-TRUNC_FRAMES:]
        
    #     state = "Focus" if stimuli_df["state"].values[0] == 'num_4' else "MW"
    #     output_file_path = f"./Preprocess/SART/Scanpath/MultiMatch/{name}/{name}_{stimuli}_{state}.tsv"
    #     data = pd.DataFrame(columns=["start_x", "start_y", "duration"])
    #     x_list = []
    #     y_list = []
    #     duration_list = []
    #     i = 0
    #     rows = stimuli_df.shape[0]
    #     while i < rows:
    #         cur_x, cur_y = eval(stimuli_df[FIXATION_INDENTIFIER].values[i])
    #         if cur_x is None or cur_y is None:
    #             i += 1
    #             continue
    #         cur_x, cur_y = to_pixel(cur_x, cur_y)
    #         j = i + 1
    #         while j < rows and stimuli_df[FIXATION_INDENTIFIER].values[j] == stimuli_df[FIXATION_INDENTIFIER].values[i]:
    #             j += 1
    #         duration = (j - i) / SAMPLE_RATE
    #         x_list.append(cur_x)
    #         y_list.append(cur_y)
    #         duration_list.append(duration)
    #         i = j
    #     data["start_x"] = x_list
    #     data["start_y"] = y_list
    #     data["duration"] = duration_list
    #     data.to_csv(output_file_path, sep="\t", index=False)

if __name__ == '__main__':
    if not os.path.exists("./Preprocess/SART/Scanpath"):
        os.makedirs("./Preprocess/SART/Scanpath")
    if not os.path.exists("./Preprocess/SART/Scanpath/MultiMatch"):
        os.makedirs("./Preprocess/SART/Scanpath/MultiMatch")
    input_dir = "./Preprocess/SART/Data"
    
    for file_name in os.listdir(input_dir):
        if file_name.startswith("."):
            continue
        extract_scanpath(os.path.join(input_dir, file_name))