"""
In this code, we will directly read the scanpath data prepared for the MultiMatch

However the format of the scanpath is slightly different so we need to adjust the code accordingly.
MM: [x, y, duration], (pixel, pixel, second)
RQA: [x, y, duration], (pixel, pixel, millisecond)
"""

from RqaDur import RqaDur
from tqdm import tqdm
import pandas as pd
from collections import defaultdict
import os


# ---Global Variables for RQA---
linelength = 2
radius = 64
mincluster = 8
d = defaultdict((lambda: defaultdict(dict)))

def exract_RQA_features(filepath, participant, stimuli):

    # Example 1:
    # The input consists of a n x 3 matrix of fixations in (x,y) coordinates.
    # plus fixation durations
    df = pd.read_csv(filepath, delimiter='\t')
    df["duration"] = df["duration"] * 1000
    fixation_duration = df.values.tolist()
    

    fixations = [[fd[0],fd[1]] for fd in fixation_duration]
    durations = [fd[2] for fd in fixation_duration]

    param = {}
    param['linelength'] = linelength
    param['radius'] = radius
    param['mincluster'] = mincluster

    result = RqaDur(fixations, durations, param)
    result['recmat']='suppressed'
    for key, value in result.items():
        d[participant][stimuli][key] = value
    

def save_RQA_features(filepath):
    pass

# ----------------------------------------------------------------------
# Program Start
# ----------------------------------------------------------------------

if __name__ == "__main__":
    input_dir = './Preprocess/FreeViewing/Scanpath/MultiMatch'
    name_list = [name for name in os.listdir(input_dir) if not name.startswith('.')]
    for name in tqdm(name_list):
        name_dir = os.path.join(input_dir, name)    
        file_list = [file for file in os.listdir(name_dir) if not file.startswith('.')]
        for file in file_list:
            file_path = os.path.join(name_dir, file)
            participant = name
            stimuli = file.split('_')[1] + '_' + file.split('_')[2]
            exract_RQA_features(file_path, participant, stimuli)
            
    
    print(d.keys())