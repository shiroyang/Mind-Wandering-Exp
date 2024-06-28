import os
import pandas as pd

# Define the folder containing the CSV files
folder_path = './Analysis/Summary/FreeViewing/Data/'

# Loop through all files in the folder
for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        # Construct the full file path
        file_path = os.path.join(folder_path, filename)
        
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)
        
        # Drop the specified columns if they exist
        columns_to_drop = ['rec_num', 'rec_dur', 'rec', 'nrec']
        df.drop(columns=[col for col in columns_to_drop if col in df.columns], inplace=True)
        
        # Save the modified DataFrame back to the same file
        df.to_csv(file_path, index=False)
        
print("Columns 'rec_num' and 'rec_dur' have been deleted from all CSV files.")
