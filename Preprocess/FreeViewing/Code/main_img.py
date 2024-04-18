import os
import pandas as pd
from math import tan, pi, sqrt
import ast
import re
from datetime import datetime, timedelta    
from OOP_sync_img import DataSynchronization, psychopy_to_datetime, str_to_datetime
from OOP_preprocess_img import EyeMovement

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
            em = EyeMovement(target_file_path)
            em.run()
            print(f"Finished Synchronizing {psychopy_data_name} and {em_data_name}")
            print("==============================================================================================")
    print("All files have been synchronized!")
    print("==============================================================================================")