"""
We will create a summary of the free viewing data.
|Participant|Stimuli|Attention|NumFix|AvgFixDur|NumBlink|AvgBlinkDur|AvgPupDia|VarPupDia|OffStimFram|AvgSacAmp|AvgFixDisp|

Attention: 1 if the participant is looking at the stimuli, 0 otherwise
NumFix: int
AvgFixDur: float
NumBlink: int
AvgBlinkDur: float
AvgPupDia: float
VarPupDia: float
OffStimFram: int
AvgSacAmp: float
AvgFixDisp: float
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
    def __init__(self, input_file_path, target_file_path, window_size, fixation_classifier):
        self.input_file_path = input_file_path
        self.target_file_path = target_file_path
        self.window_size = window_size
        self.window_frames = self.window_size * 60
        self.fixation_classifier = fixation_classifier
        # Constants
        self.SCREEN_TO_EYE_DIST = 650  # mm
        self.SCREEN_SIZE_W = 596.7  # mm
        self.SCREEN_SIZE_H = 335.7  # mm
        self.frequency = 60  # Hz
        self.time_per_frame = 1000 / self.frequency  # ms
        
        
    def convert_to_physical_coordinate(self,p):
        return (p[0] * self.SCREEN_SIZE_W, p[1] * self.SCREEN_SIZE_H)
    
    # return the visual angle between two points, return in degrees
    def visual_angle_between_two_points(self, p1, p2):
        p1 = self.convert_to_physical_coordinate(p1)
        p2 = self.convert_to_physical_coordinate(p2)
        # Calculate the distance between the two points
        distance = np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        theta = np.arctan(distance / self.SCREEN_TO_EYE_DIST)
        theta = np.rad2deg(theta)
        return theta
        
    def transform_coordinate(self, p):
        return (6/5 * p[0] - 1/10, 6/5 * p[1] - 1/10)
    
    def is_off_stimuli_coordinate(self, p):
        return (p[0] < 0 or p[0] > 1 or p[1] < 0 or p[1] > 1)
        
    def read_data(self):
        self.df = pd.read_csv(self.input_file_path, low_memory=False)
        self.participant = self.input_file_path.split("/")[-1].split("_")[0]
        self.single_participant_data = defaultdict(list)

    def create_summary_for_each_stimuli(self):
        if len(self.data) < self.window_frames: 
            if self.stimuli: print(f"Data for {self.stimuli} is not enough")
            return
        self.pending_data = self.data[-self.window_frames:]
        self.pupil_diameter = self.pupil_diameter[-self.window_frames:]
        # We will take the last window_size minutes of the data first and remove the nan values
        self.pupil_diameter = pd.Series(self.pupil_diameter).dropna()
        self.average_pupil_diameter = self.pupil_diameter.mean()
        self.variance_pupil_diameter = self.pupil_diameter.var()
        
        # Iterate through the pending_data once 
        # record number of fixations, average fixation duration, number of blinks, average pupil diameter, variance of pupil diameter,
        # number of frames off stimuli, average saccade amplitude, average fixation dispersion, last fixation duration, last fixation duration difference
        idx = 0
        self.off_stimuli_frames = 0
        self.number_of_fixations = 0
        self.fixation_frames = 0
        self.fixation_frames_list = []
        self.fixation_centroid_list = []
        self.number_of_blinks = 0
        self.blink_frames = 0
        
        while idx < len(self.pending_data):
            eye_state, gaze_point_on_display_area, fixation_centroid = self.pending_data[idx]
            gaze_point_on_display_area = eval(gaze_point_on_display_area)
            fixation_centroid = eval(fixation_centroid)
            # Assume that during off-stim, we still calculate the number of fixations, etc.
            if not pd.isna(gaze_point_on_display_area[0]) and not pd.isna(gaze_point_on_display_area[1]) and self.is_off_stimuli_coordinate(self.transform_coordinate(gaze_point_on_display_area)):
                self.off_stimuli_frames += 1
            
            if eye_state == "Fixation":
                j = idx
                while j < len(self.pending_data) and self.pending_data[j][0] == "Fixation":
                    j += 1
                self.number_of_fixations += 1
                self.fixation_frames += j - idx
                self.fixation_frames_list.append(j - idx)
                self.fixation_centroid_list.append(fixation_centroid)
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
        
        self.average_fixation_duration = self.fixation_frames * self.time_per_frame / self.number_of_fixations if self.number_of_fixations > 0 else 0
        self.average_blink_duration = self.blink_frames * self.time_per_frame / self.number_of_blinks if self.number_of_blinks > 0 else 0

        # calculate the saccade amplitude
        self.saccade_amplitude = 0
        if len(self.fixation_centroid_list) > 1:
            for i in range(len(self.fixation_centroid_list)-1):
                p1, p2 = self.fixation_centroid_list[i], self.fixation_centroid_list[i+1]
                self.saccade_amplitude += self.visual_angle_between_two_points(p1, p2)
            self.saccade_amplitude /= len(self.fixation_centroid_list) - 1
        
        # calculate the average fixation dispersion
        self.average_fixation_dispersion = 0
        if len(self.fixation_centroid_list) > 0:
            x_sum, y_sum = 0, 0
            for i in range(len(self.fixation_centroid_list)):
                x, y = self.fixation_centroid_list[i]
                x_sum += x; y_sum += y
            x_mean, y_mean = x_sum / len(self.fixation_centroid_list), y_sum / len(self.fixation_centroid_list)
            for i in range(len(self.fixation_centroid_list)):
                x, y = self.fixation_centroid_list[i]
                self.average_fixation_dispersion += np.sqrt((x - x_mean)**2 + (y - y_mean)**2)
            self.average_fixation_dispersion /= len(self.fixation_centroid_list)

        # calculate the last fixation duration
        self.last_fixation_duration = 0
        if len(self.fixation_frames_list) > 0:
            self.last_fixation_duration = self.fixation_frames_list[-1] * self.time_per_frame
        
        # calculate the last fixation duration minus average fixation duration, (last fixation duration excluded)
        self.last_fixation_duration_diff = 0
        if self.number_of_fixations > 1:
            average_fixation_duration_last_fixation_excluded = (self.fixation_frames-self.fixation_frames_list[-1]) * self.time_per_frame / (self.number_of_fixations-1) 
            self.last_fixation_duration_diff = self.last_fixation_duration - average_fixation_duration_last_fixation_excluded

        self.single_participant_data["Participant"].append(self.participant)
        self.single_participant_data["Stimuli"].append(self.stimuli)
        self.single_participant_data["Attention"].append(self.attention)
        self.single_participant_data["MW"].append(self.MW)
        self.single_participant_data["NumFix"].append(self.number_of_fixations)
        self.single_participant_data["AvgFixDur"].append(self.average_fixation_duration)
        self.single_participant_data["NumBlink"].append(self.number_of_blinks)
        self.single_participant_data["AvgBlinkDur"].append(self.average_blink_duration)
        self.single_participant_data["AvgPupDia"].append(self.average_pupil_diameter)
        self.single_participant_data["VarPupDia"].append(self.variance_pupil_diameter)
        self.single_participant_data["OffStimFram"].append(self.off_stimuli_frames)
        self.single_participant_data["AvgSacAmp"].append(self.saccade_amplitude)
        self.single_participant_data["AvgFixDisp"].append(self.average_fixation_dispersion)
        self.single_participant_data["LastFixDur"].append(self.last_fixation_duration)
        self.single_participant_data["LastFixDurDiff"].append(self.last_fixation_duration_diff)
        
        
    def create_summary(self):
        self.recorded_stimuli = set()
        self.data = []
        self.pupil_diameter = []
        self.stimuli = None
        # Extarct the data for each stimuli
        for idx, row in self.df.iterrows():
            if pd.isna(row["stimuli"]): continue
            if row["stimuli"] not in self.recorded_stimuli: 
                self.create_summary_for_each_stimuli()

                # pending_data will record (eye_state, {eye_to_use}_gaze_point_on_display_area, {fixation_classifier}_fixation_centroid) for each stimuli
                self.data = []
                self.pupil_diameter = []
                self.recorded_stimuli.add(row["stimuli"])
                self.stimuli = row["stimuli"]
                self.attention = 1 if row["state"] == "num_4" else 0
                self.MW = 1 if self.attention == 0 else 0
                self.eye_to_use = row["eye_to_use"]
            
            self.data.append((row[f"{self.fixation_classifier}_state"], row[f"{self.eye_to_use}_gaze_point_on_display_area"], row[f"{self.fixation_classifier}_fixation_centroid"]))
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
    for window_size in tqdm(range(5, 41, 5)):
        fixation_classifier = "IVT"
        input_dir = './Preprocess/FreeViewing/Data'
        target_file_dir = './Analysis/Summary/FreeViewing/Data'
        target_file_path = os.path.join(target_file_dir, "FreeViewing_Summary_{}sec.csv".format(window_size))
        if not os.path.exists(target_file_dir):
            os.makedirs(target_file_dir)
        name_list = sorted(list(os.listdir(input_dir)), key=extract_number)
        for name in name_list:
            if name.startswith("."): continue
            input_file_path = os.path.join(input_dir, name)
            summary = FreeViewingSummary(input_file_path, target_file_path, window_size, fixation_classifier)
            summary.run()
    print("All Done!")
    print("==========================================================")