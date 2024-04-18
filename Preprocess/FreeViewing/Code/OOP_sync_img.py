import os
import pandas as pd
import re
from datetime import datetime, timedelta    

psychopy_to_datetime = lambda s: datetime.strptime(s, '%Y-%m-%d_%Hh%M.%S.%f')
str_to_datetime = lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')

class DataSynchronization:
    def __init__(self, psychopy_data_path, em_data_path, target_file_path):
        self.psychopy_data_path = psychopy_data_path
        self.em_data_path = em_data_path
        self.target_file_path = target_file_path
        self.psychopy_data = pd.read_csv(self.psychopy_data_path)
        self.em_data = pd.read_csv(self.em_data_path)
        self.ExpTime = self.psychopy_data["date"].iloc[0]
        self.ExpTime = str_to_datetime(self.ExpTime)

    def sync_data(self):
        self.pending_data = []
        # This will iterate over the psychopy data once
        for idx, row in self.psychopy_data.iterrows():
            if pd.isna(row["imagepath"]): continue
            image_path = row["imagepath"]
            image_name = image_path.split("\\")[-1].split(".")[0]
            image_started_time = self.ExpTime + timedelta(seconds=row["image.started"])
            image_duration = row["image.rt"]
            image_stopped_time = image_started_time + timedelta(seconds=image_duration)
            state = row["probe_resp.keys"]
            self.pending_data.append((image_name, state, image_started_time, image_stopped_time))
        
        # Then iterate over the eye-tracking data once
        self.started_time = []
        self.stopped_time = []
        self.stimuli_data = []
        self.state = []
        img_idx = 0
        for _, row in self.em_data.iterrows():
            timestamp = str_to_datetime(row["timestamp"])
            image_name, state, image_started_time, image_stopped_time = self.pending_data[img_idx]
            if timestamp < image_started_time:
                self.stimuli_data.append(None)
                self.state.append(None)
                self.started_time.append(None)
                self.stopped_time.append(None)
            elif image_started_time <= timestamp <= image_stopped_time:
                self.stimuli_data.append(image_name)
                self.state.append(state)
                self.started_time.append(image_started_time)
                self.stopped_time.append(image_stopped_time)
            else:
                img_idx += 1
                if img_idx >= len(self.pending_data):
                    break
                self.stimuli_data.append(None)
                self.state.append(None)
                self.started_time.append(None)
                self.stopped_time.append(None)             
                
                
        # 残りをNoneで埋める
        for _ in range(max(0, self.em_data.shape[0] - len(self.stimuli_data))):
            self.stimuli_data.append(None)
            self.state.append(None)
            self.started_time.append(None)
            self.stopped_time.append(None)
        
        self.em_data["stimuli"] = self.stimuli_data
        self.em_data["state"] = self.state
        self.em_data["started_time"] = self.started_time
        self.em_data["stopped_time"] = self.stopped_time
        
    def save_data(self):
        self.em_data.to_csv(self.target_file_path, index=False)
    
    def run(self):
        self.sync_data()
        self.save_data()

if __name__ == "__main__":
    freeviewing_raw_dir = "./Data_Collection/FreeViewing/Raw"
    target_file_dir = "./Preprocess/FreeViewing/Data"
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