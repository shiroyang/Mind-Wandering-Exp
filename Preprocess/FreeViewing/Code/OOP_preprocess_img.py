"""
Step 3.

Please run this code after step 1 and step 2 in Data_Collection folder.
This code will process the eye tracking data and identify the eye state for each frame.

The result will be saved in the Data_Collection/Data/Processed folder.
"""

import os
import pandas as pd
import numpy as np
from math import tan, pi, sqrt
import ast
from functools import cache
    
# def get_matched_files():
#     files_input = os.listdir(EyeMovement.INPUT_DIR)
#     files_target = os.listdir(EyeMovement.TARGET_DIR)
#     # return the files that are in the input folder but not in the target folder
#     return list(set(files_input) - set(files_target))
    
class EyeMovement:
    SCREEN_SIZE_W = 596.7  # mm
    SCREEN_SIZE_H = 335.7  # mm
    SCREEN_TO_EYE_DIST = 650  # mm
    BLINK_THRESHOLD = 5  # 5 consecutive missing frames
    SAMPLING_RATE = 60  # Hz
    
    # IVT parameters
    IVT_SACCADE_THRESHOLD = np.deg2rad(20)  # 20 degree per second
    IVT_FIXATION_THRESHOLD = 6 # Fixation is at least 100ms
    
    #IDT parameters
    IDT_DISPERSION_THRESHOLD = np.deg2rad(0.5)  # 0.5 degree in radians
    IDT_WINDOW_SIZE = 6  # 100 ms window size
    IDT_FIXATION_THRESHOLD = 6  # Fixation is at least 100ms
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = self._load_data()
        self.eye_to_use = None
        self.col = None
        self.validity_col = None
        self.states = []
        self.blink = []

    def _convert_to_tuple(self, value):
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            # Handle the exception or return a default value
            return (None, None)

    def _load_data(self) -> pd.DataFrame:
        converters = {
            'left_gaze_point_on_display_area': self._convert_to_tuple,
            'right_gaze_point_on_display_area': self._convert_to_tuple
        }
        return pd.read_csv(self.filepath, converters=converters)
    
    def _calc_dis(self, p1, p2):
        return sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
    
    # Given two points, calculate the visual angle of two points, return radian
    def visual_angle_calculation(self, p1, p2):
        # Convert to actual coordinates on monitor
        x1, y1 = p1[0] * EyeMovement.SCREEN_SIZE_W, p1[1] * EyeMovement.SCREEN_SIZE_H
        x2, y2 = p2[0] * EyeMovement.SCREEN_SIZE_W, p2[1] * EyeMovement.SCREEN_SIZE_H
        p0 = ((x1+x2)/2, (y1+y2)/2)
        o = (1/2 * self.SCREEN_SIZE_W, 1/2 * self.SCREEN_SIZE_H)
        o_p0 = self._calc_dis(o, p0)
        e_o = self.SCREEN_TO_EYE_DIST
        e_p0 = sqrt(e_o ** 2 + o_p0 ** 2)
        p0_p1 = self._calc_dis(p0, p1)
        theta1 = np.arctan(p0_p1 / e_p0)
        p0_p2 = self._calc_dis(p0, p2)
        theta2 = np.arctan(p0_p2 / e_p0)
        theta = abs(theta1) + abs(theta2)
        return theta
        
            
    def decide_eye_to_use(self):
        left_valid = self.data['left_gaze_point_validity'].sum()
        right_valid = self.data['right_gaze_point_validity'].sum()
        self.eye_to_use = 'left' if left_valid > right_valid else 'right'
        self.col = f'{self.eye_to_use}_gaze_point_on_display_area'
        self.validity_col = f'{self.eye_to_use}_gaze_point_validity'
        self.data['eye_to_use'] = self.eye_to_use


    def interpolate_coordinates(self):
        idx = 0
        while idx < len(self.data):
            # If the current point is missing
            if self.data.at[idx, self.validity_col] == 0:
                start_idx = idx
                while idx < len(self.data) and self.data.at[idx, self.validity_col] == 0:
                    idx += 1
                end_idx = idx
                
                # Check if the count of missing points is 4 or fewer
                if 1 <= (end_idx - start_idx) <= 4:
                    # Ensure that both bounding points are valid for interpolation
                    if start_idx > 0 and end_idx < len(self.data):
                        x1, y1 = self.data.at[start_idx - 1, self.col]
                        x2, y2 = self.data.at[end_idx, self.col]
                        
                        # Linear interpolation for each missing point
                        for j in range(start_idx, end_idx):
                            alpha = (j - start_idx + 1) / (end_idx - start_idx + 1)
                            x = x1 + alpha * (x2 - x1)
                            y = y1 + alpha * (y2 - y1)
                            self.data.at[j, self.col] = (x, y)
                            # set validity to 2 to indicate that the point is interpolated
                            self.data.at[j, self.validity_col] = 2
            else:
                idx += 1


    def identify_blink(self):
        idx = 0
        total_rows = len(self.data)

        while idx < total_rows:
            # Check if both eyes' data is missing at the current index
            if self.data.at[idx, self.validity_col] == 0:
                blink_start_idx = idx
                while (idx < total_rows and self.data.at[idx, self.validity_col] == 0):
                    idx += 1
                blink_end_idx = idx

                # Check if the consecutive missing frames count as a blink or just error states
                if blink_end_idx - blink_start_idx >= EyeMovement.BLINK_THRESHOLD:
                    self.blink.extend(['Blink'] * (blink_end_idx - blink_start_idx))
                else:
                    self.blink.extend(['Error'] * (blink_end_idx - blink_start_idx))
            else:
                self.blink.append(None)
                idx += 1
                
                
    def IVT(self):
        """
        Calculate the distance between each consecutive point, 
        if the distance is greater than the threshold, then it is a saccade
        identify saccade -> identify fixation -> compute center point -> add error state
        """
        self.IVT = self.blink[:]
        
        # identify saccade
        col = f'{self.eye_to_use}_gaze_point_on_display_area'
        for i in range(len(self.data) - 1):
            if self.IVT[i]:  # Skip already identified states
                continue
            
            p1 = self.data.at[i, col]
            p2 = self.data.at[i+1, col]
            # Ignore the point where value is missing
            if p1[0] is None or p2[0] is None or p1[1] is None or p2[1] is None: continue
        
            # Calculate the velocity, pixel/sec
            v = self.visual_angle_calculation(p1, p2) * EyeMovement.SAMPLING_RATE # 60 Hz sampling rate
            if v >= EyeMovement.IVT_SACCADE_THRESHOLD:
                self.IVT[i] = 'Saccade'
        
        # identify fixation
        for i, state in enumerate(self.IVT):
            if not state:
                self.IVT[i] = 'Fixation'

        # add state to the dataframe
        self.data['IVT_state'] = self.IVT
        
        # compute center point
        fixation_start = None
        self.data['IVT_fixation_center'] = [(None, None)] * len(self.data)
        IVT_states = self.IVT + ['End']
        
        for i, state in enumerate(IVT_states):
            if state == 'Fixation':
                if fixation_start is None:
                    fixation_start = i
            # Fixation has ended, check if it was longer or equal to 6 frames
            elif fixation_start is not None:
                if i - fixation_start >= EyeMovement.IVT_FIXATION_THRESHOLD:
                    fixation_points = self.data[col][fixation_start:i]
                    x_center = fixation_points.apply(lambda p: p[0]).mean()
                    y_center = fixation_points.apply(lambda p: p[1]).mean()
                    center_point = (x_center, y_center)
                    for j in range(fixation_start, i):
                        self.data.at[j, 'IVT_fixation_center'] = center_point
                fixation_start = None
        
        # add error state
        for i in range(len(self.data)):
            if self.IVT[i] == 'Fixation' and self.data.at[i, 'IVT_fixation_center'] == (None, None):
                self.IVT[i] = 'Error'
                
        
    def IDT(self):
        """
        Calculate the dispersion of the eye gaze points within a window size
        if the dispersion is greater than the threshold, then it is a saccade
        Dispersion = x_max - x_min + y_max - y_min
        identify fixation -> identify saccade -> compute center point -> add error state
        """
        
        self.IDT = self.blink[:]
        col = f'{self.eye_to_use}_gaze_point_on_display_area'
        
        # identify fixation using two pointers
        l = 0
        r = l + EyeMovement.IDT_WINDOW_SIZE
        while r < len(self.data):
            points = self.data[col][l:r]
            x_min = np.min(points.apply(lambda p: p[0]))
            x_max = np.max(points.apply(lambda p: p[0]))
            y_min = np.min(points.apply(lambda p: p[1]))
            y_max = np.max(points.apply(lambda p: p[1]))
            bottom_left = (x_min, y_min)
            top_right = (x_max, y_max)
            if self.visual_angle_calculation(bottom_left, top_right) <= EyeMovement.IDT_DISPERSION_THRESHOLD:
                while r < len(self.data) and self.visual_angle_calculation(bottom_left, top_right) <= EyeMovement.IDT_DISPERSION_THRESHOLD:
                    r += 1
                    new_point = self.data.at[r, col]
                    x_min = min(x_min, new_point[0]); x_max = max(x_max, new_point[0])
                    y_max = max(y_max, new_point[1]); y_min = min(y_min, new_point[1])
                    bottom_left = (x_min, y_min)
                    top_right = (x_max, y_max)
                
                for i in range(l, r):
                    self.IDT[i] = 'Fixation'
                
                l = r
                r = l + EyeMovement.IDT_WINDOW_SIZE
            
            else:
                l += 1
                r = l + EyeMovement.IDT_WINDOW_SIZE
        
        
        # identify saccade
        for i, state in enumerate(self.IDT):
            if not state:
                self.IDT[i] = 'Saccade'
                
        # add state to the dataframe
        self.data['IDT_state'] = self.IDT
        
        # compute center point
        fixation_start = None
        self.data['IDT_fixation_center'] = [(None, None)] * len(self.data)
        IDT_states = self.IDT + ['End']
        
        for i, state in enumerate(IDT_states):
            if state == 'Fixation':
                if fixation_start is None:
                    fixation_start = i
            # Fixation has ended, check if it was longer or equal to 6 frames
            elif fixation_start is not None:
                if i - fixation_start >= EyeMovement.IDT_FIXATION_THRESHOLD:
                    fixation_points = self.data[col][fixation_start:i]
                    x_center = fixation_points.apply(lambda p: p[0]).mean()
                    y_center = fixation_points.apply(lambda p: p[1]).mean()
                    center_point = (x_center, y_center)
                    for j in range(fixation_start, i):
                        self.data.at[j, 'IDT_fixation_center'] = center_point
                fixation_start = None
        
        # add error state
        for i in range(len(self.data)):
            if self.IDT[i] == 'Fixation' and self.data.at[i, 'IDT_fixation_center'] == (None, None):
                self.IDT[i] = 'Error'


    def add_state_to_csv(self):
        self.data.to_csv(self.filepath, index=False)


    def run(self):
        self.decide_eye_to_use()
        self.interpolate_coordinates()
        self.identify_blink()
        self.IVT()
        self.IDT()
        self.add_state_to_csv()


if __name__ == "__main__":
    # ds.em_data が同期したdataframe
    filepath = None
    em = EyeMovement(filepath=filepath)
    em.run()