import os
import pandas as pd
import re
from datetime import datetime, timedelta    

psychopy_to_datetime = lambda s: datetime.strptime(s, '%Y-%m-%d_%Hh%M.%S.%f')
def str_to_datetime(s):
    try: return datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError: return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

class DataSynchronization:
    def __init__(self, psychopy_data_path, em_data_path, target_file_path):
        self.psychopy_data_path = psychopy_data_path
        self.em_data_path = em_data_path
        self.target_dir = "./synced"
        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)
        self.target_file_path = target_file_path
        self.psychopy_data = pd.read_csv(self.psychopy_data_path)
        self.em_data = pd.read_csv(self.em_data_path)
        self.ExpTime = self.psychopy_data["date"].iloc[0]
        self.ExpTime = str_to_datetime(self.ExpTime)
        self.stimulus_duration = 2.0
        # tmp = [19, 42, 61, 81, 100] 
        # self.start_idx = {0, 19, 42, 61, 81}
        # self.end_idx = {18, 41, 60, 80, 99}
        tmp = eval(self.psychopy_data["randomSequence"].iloc[0])
        self.start_idx = {0}
        self.end_idx = {tmp[0]-1}
        for i in range(len(tmp)-1):
            self.start_idx.add(tmp[i])
            self.end_idx.add(tmp[i+1]-1)
        
    def sync_data(self):
        self.pending_data = []
        state_tmp = []
        start_time = []
        end_time = []
        stimuli_idx = 0
        # This will iterate over the psychopy data once
        for _, row in self.psychopy_data.iterrows():
            if not row["stimulus"] or pd.isna(row["stimulus"]): continue
            if row["prob_resp.keys"] and not pd.isna(row["prob_resp.keys"]): state_tmp.append(row["prob_resp.keys"])
            
            if stimuli_idx in self.start_idx:
                start_time.append(self.ExpTime + timedelta(seconds=row["text_2.started"]))
            if stimuli_idx in self.end_idx:
                end_time.append(self.ExpTime + timedelta(seconds=row["text_2.started"] + self.stimulus_duration))
                
            stimulus = row["stimulus"]
            stimulus_resp_corr = int(row["stimulus_resp.corr"])
            stimulus_resp_rt = row["stimulus_resp.rt"]
            stimulus_started_time = self.ExpTime + timedelta(seconds=row["text_2.started"])
            stimulus_stopped_time = stimulus_started_time + timedelta(seconds=self.stimulus_duration)
            self.pending_data.append((stimulus, stimulus_resp_corr, stimulus_resp_rt, stimulus_started_time, stimulus_stopped_time))
            stimuli_idx += 1
        
        
        # state_tmp = [4, 4, 4, 6, 6]
        # start_time = [t1, t2, t3, t4, t5]
        # end_time = [t1, t2, t3, t4, t5]
        self.pending_state = []
        for state, start, end in zip(state_tmp, start_time, end_time):
            self.pending_state.append((state, start, end))
        
        # Then iterate over the eye-tracking data to sync the data (state excluded)
        self.started_time = []
        self.stopped_time = []
        self.stimuli_data = []
        self.stimuli_resp_corr = []
        self.stimuli_resp_rt = []
        stimuli_idx = 0
        for _, row in self.em_data.iterrows():
            timestamp = str_to_datetime(row["timestamp"])
            stimulus, stimulus_resp_corr, stimulus_resp_rt, stimulus_started_time, stimulus_stopped_time = self.pending_data[stimuli_idx]
            if timestamp < stimulus_started_time:
                self.stimuli_data.append(None)
                self.stimuli_resp_corr.append(None)
                self.stimuli_resp_rt.append(None)
                self.started_time.append(None)
                self.stopped_time.append(None)
            elif stimulus_started_time <= timestamp <= stimulus_stopped_time:
                self.stimuli_data.append(stimulus)
                self.stimuli_resp_corr.append(stimulus_resp_corr)
                # OOOOOのときだけrtを計算する
                if pd.isna(stimulus_resp_rt):
                    self.stimuli_resp_rt.append(None)
                else:
                    self.stimuli_resp_rt.append((self.ExpTime + timedelta(seconds=stimulus_resp_rt) - stimulus_started_time).total_seconds())
                self.started_time.append(stimulus_started_time)
                self.stopped_time.append(stimulus_stopped_time)
            else:
                stimuli_idx += 1
                if stimuli_idx >= len(self.pending_data):
                    break
                self.stimuli_data.append(None)
                self.stimuli_resp_corr.append(None)
                self.stimuli_resp_rt.append(None)
                self.started_time.append(None)
                self.stopped_time.append(None)
                
                
        # 残りをNoneで埋める
        for _ in range(max(0, self.em_data.shape[0] - len(self.stimuli_data))):
            self.stimuli_data.append(None)
            self.stimuli_resp_corr.append(None)
            self.stimuli_resp_rt.append(None)
            self.started_time.append(None)
            self.stopped_time.append(None)
            
        # We have to iterate over the em again to sync the state
        self.state = []
        state_idx = 0
        for _, row in self.em_data.iterrows():
            timestamp = str_to_datetime(row["timestamp"])
            state, start, end = self.pending_state[state_idx]
            if timestamp < start:
                self.state.append(None)
            elif start <= timestamp <= end:
                self.state.append(state)
            else:
                state_idx += 1
                if state_idx >= len(self.pending_state):
                    break
                self.state.append(None)
        for _ in range(max(0, self.em_data.shape[0] - len(self.state))):
            self.state.append(None)
            
        
        self.em_data["stimuli"] = self.stimuli_data
        self.em_data["stimuli_resp_corr"] = self.stimuli_resp_corr
        self.em_data["stimuli_resp_rt"] = self.stimuli_resp_rt
        self.em_data["state"] = self.state
        self.em_data["started_time"] = self.started_time
        self.em_data["stopped_time"] = self.stopped_time
            
            
    def save_data(self):
        self.em_data.to_csv(self.target_file_path, index=False)
    
    def run(self):
        self.sync_data()
        self.save_data()


if __name__ == "__main__":
    freeviewing_raw_dir = "./Data_Collection/SART/Raw"
    target_file_dir = "./Preprocess/SART/Data"
    name_list = list(os.listdir(freeviewing_raw_dir))
    for name in name_list:
        psychopy_folder_path = os.path.join(freeviewing_raw_dir, name, "data")
        em_folder_path = os.path.join(freeviewing_raw_dir, name, "em")
        data_list = [file_name for file_name in os.listdir(psychopy_folder_path) if file_name.endswith(".csv")]
        em_list = [file_name for file_name in os.listdir(em_folder_path) if file_name.endswith(".csv")]
        sorted_data_list = sorted(data_list, key=lambda x: int(re.search(r'(\d+)\.csv$', x).group(1)))
        sorted_em_list = sorted(em_list, key=lambda x: re.search(r'(\d{12})', x).group())

        for psychopy_data_name, em_data_name in zip(sorted_data_list, sorted_em_list):
            print(f"Synchronizing {psychopy_data_name} and {em_data_name}")
            psychopy_data_path = os.path.join(psychopy_folder_path, psychopy_data_name)
            em_data_path = os.path.join(em_folder_path, em_data_name)
            target_file_path = os.path.join(target_file_dir, psychopy_data_name)
            ds = DataSynchronization(psychopy_data_path=psychopy_data_path, em_data_path=em_data_path, target_file_path=target_file_path)
            ds.run()
            # ds.em_dataの中身がsyncされたデータ
            print(f"Finished Synchronizing {psychopy_data_name} and {em_data_name}")
            print("==============================================================================================")
    print("All files have been synchronized!")
    print("==============================================================================================")