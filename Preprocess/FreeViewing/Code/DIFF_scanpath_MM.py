# Truncate the first TRUNC_FRAMES scanpath data to the fixation based scanpath data for MultiMatch
# [(x, y, duration), ...], x and y are in pixel coordinates, duration is in seconds

import numpy as np
import pandas as pd
import os

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SAMPLE_RATE = 60
FIXATION_INDENTIFIER = "IVT_fixation_centroid"
TRUNC_FRAMES = 30 * 60

def to_pixel(x, y):
    return x * SCREEN_WIDTH, y * SCREEN_HEIGHT

def extract_scanpath(file_path):
    name = os.path.splitext(os.path.basename(file_path))[0].split("_")[0]
    if not os.path.exists(f"./Preprocess/FreeViewing/Scanpath/Reversed/{name}"):
        os.makedirs(f"./Preprocess/FreeViewing/Scanpath/Reversed/{name}")
    df = pd.read_csv(file_path, low_memory=False)
    stimuli_list = df["stimuli"].dropna().unique()
    for stimuli in stimuli_list:
        stimuli_df = df[df["stimuli"] == stimuli]
        
        # Change this if you want to truncate the scanpath data
        #stimuli_df = stimuli_df[-TRUNC_FRAMES:]
        stimuli_df = stimuli_df[:TRUNC_FRAMES]
        
    
        state = "Focus" if stimuli_df["state"].values[0] == 'num_4' else "MW"
        output_file_path = f"./Preprocess/FreeViewing/Scanpath/Reversed/{name}/{name}_{stimuli}_{state}.tsv"
        data = pd.DataFrame(columns=["start_x", "start_y", "duration"])
        x_list = []
        y_list = []
        duration_list = []
        i = 0
        rows = stimuli_df.shape[0]
        while i < rows:
            cur_x, cur_y = eval(stimuli_df[FIXATION_INDENTIFIER].values[i])
            if cur_x is None or cur_y is None:
                i += 1
                continue
            cur_x, cur_y = to_pixel(cur_x, cur_y)
            j = i + 1
            while j < rows and stimuli_df[FIXATION_INDENTIFIER].values[j] == stimuli_df[FIXATION_INDENTIFIER].values[i]:
                j += 1
            duration = (j - i) / SAMPLE_RATE
            x_list.append(cur_x)
            y_list.append(cur_y)
            duration_list.append(duration)
            i = j
        data["start_x"] = x_list
        data["start_y"] = y_list
        data["duration"] = duration_list
        data.to_csv(output_file_path, sep="\t", index=False)

if __name__ == '__main__':
    if not os.path.exists("./Preprocess/FreeViewing/Scanpath"):
        os.makedirs("./Preprocess/FreeViewing/Scanpath")
    if not os.path.exists("./Preprocess/FreeViewing/Scanpath/Reversed"):
        os.makedirs("./Preprocess/FreeViewing/Scanpath/Reversed")
    input_dir = "./Preprocess/FreeViewing/Data"
    
    for file_name in os.listdir(input_dir):
        if file_name.startswith("."):
            continue
        extract_scanpath(os.path.join(input_dir, file_name))