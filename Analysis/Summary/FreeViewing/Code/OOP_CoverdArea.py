"""
In this code, we will directly read the scanpath data prepared for the MultiMatch
For each fixation, we will draw a circle with a radius of 73 pixels (2 degrees) around the fixation point.
Then we will calculate the proportion of the area covered by the circles.
"""

from tqdm import tqdm
import pandas as pd
from collections import defaultdict
import os
import numpy as np

# ------------Parameters of Radius------------
radius = 73
x_offset = 160
y_offset = 90
image_width = 1600
image_height = 900

result = defaultdict((lambda: defaultdict(dict)))

def CalculateCoverdArea(filepath, participant, stimuli, result):
    df = pd.read_csv(filepath, delimiter='\t')
    df["start_x"] = df["start_x"] - x_offset
    df["start_y"] = df["start_y"] - y_offset
    grid = [[False] * image_height for _ in range(image_width)]
    covered_cnt = 0
    for idx, row in df.iterrows():
        x, y = int(row["start_x"]), int(row["start_y"])
        for dx in range(radius):
            for dy in range(radius):
                if dx**2 + dy**2 <= radius**2:
                    for sgnx in [-1, 1]:
                        for sgny in [-1, 1]:
                            nx = x + sgnx * dx
                            ny = y + sgny * dy
                            if 0 <= nx < image_width and 0 <= ny < image_height:
                                if not grid[nx][ny]:
                                    grid[nx][ny] = True
                                    covered_cnt += 1
                                    
    covered_proportion = covered_cnt / (image_width * image_height)
    result[participant][stimuli]["CoveredArea"] = covered_proportion
        
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
            print(f"Now processing {participant}, {stimuli}")
            CalculateCoverdArea(file_path, participant, stimuli, result)
        break
    
    print(result)