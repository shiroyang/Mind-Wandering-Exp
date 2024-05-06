"""
We will create a summary of the free viewing data.
|Participant|Stimuli|Attention|NumFix|AvgFixDur|NumBlink|AvgBlinkDur|AvgPupDia|VarPupDia|OffStimFram|
"""

import os
import pandas as pd
import numpy as np
import re
from collections import defaultdict
from tqdm import tqdm

def extract_number(filename):
    match = re.search(r'(\d+)', filename)  
    return int(match.group(0)) if match else float('inf')  

class FreeViewingSummary:
    def __init__(self, input_file_path, target_file_path, window_size):
        self.input_file_path = input_file_path
        self.target_file_path = target_file_path
        self.window_size = window_size
        self.window_frames = self.window_size * 60
    
    def transform_coordinate(self, p):
        return (6/5 * p[0] - 1/10, 9/8 * p[1] - 1/16)
    
    def is_off_stimuli_coordinate(self, p):
        return (p[0] < 0 or p[0] > 1 or p[1] < 0 or p[1] > 1)
        
    def read_data(self):
        self.data = pd.read_csv(self.input_file_path, low_memory=False)
        self.participant = self.input_file_path.split("/")[-1].split("_")[0]
        self.single_participant_data = defaultdict(list)

    def create_summary_for_each_stimuli(self):
        if len(self.pending_data) < self.window_frames: 
            if self.stimuli: print(f"Data for {self.stimuli} is not enough")
            return
        self.pending_data = self.pending_data[-self.window_frames:]
        self.pupil_diameter = self.pupil_diameter[-self.window_frames:]
        # We will take the last window_size minutes of the data first and remove the nan values
        self.pupil_diameter = pd.Series(self.pupil_diameter).dropna()
        self.average_pupil_diameter = self.pupil_diameter.mean()
        self.variance_pupil_diameter = self.pupil_diameter.var()
        
        # Iterate through the pending_data once 
        # record number of fixations, average fixation duration, number of blinks, average pupil diameter, variance of pupil diameter, and number of frames off stimuli
        idx = 0
        self.off_stimuli_frames = 0
        self.number_of_fixations = 0
        self.fixation_frames = 0
        self.number_of_blinks = 0
        self.blink_frames = 0
        
        while idx < len(self.pending_data):
            eye_state, gaze_point_on_display_area = self.pending_data[idx]
            gaze_point_on_display_area = eval(gaze_point_on_display_area)
            # Assume that during off-stim, we still calculate the number of fixations, etc.
            if not pd.isna(gaze_point_on_display_area[0]) and not pd.isna(gaze_point_on_display_area[1]) and self.is_off_stimuli_coordinate(self.transform_coordinate(gaze_point_on_display_area)):
                self.off_stimuli_frames += 1
            
            if eye_state == "Fixation":
                j = idx
                while j < len(self.pending_data) and self.pending_data[j][0] == "Fixation":
                    j += 1
                self.number_of_fixations += 1
                self.fixation_frames += j - idx
                idx = j
            
            elif eye_state == "Blink":
                j = idx
                while j < len(self.pending_data) and self.pending_data[j][0] == "Blink":
                    j += 1
                self.number_of_blinks += 1
                self.blink_frames += j - idx
                idx = j
            
            else:
                idx += 1
        
        self.average_fixation_duration = self.fixation_frames / self.number_of_fixations if self.number_of_fixations > 0 else 0
        self.average_blink_duration = self.blink_frames / self.number_of_blinks if self.number_of_blinks > 0 else 0

        self.single_participant_data["Participant"].append(self.participant)
        self.single_participant_data["Stimuli"].append(self.stimuli)
        self.single_participant_data["Attention"].append(self.attention)
        self.single_participant_data["NumFix"].append(self.number_of_fixations)
        self.single_participant_data["AvgFixDur"].append(self.average_fixation_duration)
        self.single_participant_data["NumBlink"].append(self.number_of_blinks)
        self.single_participant_data["AvgBlinkDur"].append(self.average_blink_duration)
        self.single_participant_data["AvgPupDia"].append(self.average_pupil_diameter)
        self.single_participant_data["VarPupDia"].append(self.variance_pupil_diameter)
        self.single_participant_data["OffStimFram"].append(self.off_stimuli_frames)
        
        
    def create_summary(self):
        self.recorded_stimuli = set()
        self.pending_data = []
        self.pupil_diameter = []
        self.stimuli = None
        # Extarct the data for each stimuli
        for idx, row in self.data.iterrows():
            if pd.isna(row["stimuli"]): continue
            if row["stimuli"] not in self.recorded_stimuli: 
                self.create_summary_for_each_stimuli()

                # pending_data will record (eye_state, {eye_to_use}_gaze_point_on_display_area, {eye_to_use}_pupil_diameter) for each stimuli
                self.pending_data = []
                self.pupil_diameter = []
                self.recorded_stimuli.add(row["stimuli"])
                self.stimuli = row["stimuli"]
                self.attention = 1 if row["state"] == "num_4" else 0
                self.eye_to_use = row["eye_to_use"]
            
            self.pending_data.append((row["eye_state"], row[f"{self.eye_to_use}_gaze_point_on_display_area"]))
            self.pupil_diameter.append(row[f"{self.eye_to_use}_pupil_diameter"])
        # Process the last stimuli
        self.create_summary_for_each_stimuli()
            

    def save_data(self):
        self.single_participant_data = pd.DataFrame(self.single_participant_data)
        df = pd.read_csv(self.target_file_path) if os.path.exists(self.target_file_path) else pd.DataFrame()
        df = pd.concat([df, self.single_participant_data], ignore_index=True) 
        df.to_csv(self.target_file_path, index=False)
    
    def run(self):
        self.read_data()
        self.create_summary()
        self.save_data()
        

if __name__ == '__main__':
    # window size in seconds
    window_size = 5
    input_dir = './Preprocess/FreeViewing/Data'
    target_file_dir = './Analysis/Summary/FreeViewing/Data'
    target_file_path = os.path.join(target_file_dir, "FreeViewing_Summary_{}sec.csv".format(window_size))
    if not os.path.exists(target_file_dir):
        os.makedirs(target_file_dir)
    name_list = sorted(list(os.listdir(input_dir)), key=extract_number)
    for name in tqdm(name_list):
        if name.startswith("."): continue
        input_file_path = os.path.join(input_dir, name)
        summary = FreeViewingSummary(input_file_path, target_file_path, window_size)
        summary.run()
    print("All Done!")
    print("==========================================================")