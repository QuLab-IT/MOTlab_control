# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 14:23:24 2020

@author: MOT_User
"""
import copy
import csv
import os


# %% Function
def ModifyCSVNew(file_name, device, start, exposure, value):
    """
    Modify a specified column in a CSV file by setting values to `value` in a range of rows.
    
    This function reads a CSV file, finds the specified column (device), and modifies
    a consecutive range of rows in that column with the given value. The modified
    data is then written back to the same file.
    
    Args:
        file_name (str): Name of the CSV file to modify. The file should be located
            in the same directory as this script.
        device (str): Name of the column to modify. Must match exactly one of the
            column headers in the CSV file.
        start (int): Starting row number (1-indexed) where modifications begin.
            Must be >= 1.
        exposure (int): Number of consecutive rows to modify starting from the
            start row. Must be >= 1.
        value (float | int | str): The value to set in the specified cells.
            Will be converted to string when written to CSV.
    
    Raises:
        ValueError: If the specified device column is not found in the CSV file.
            The error message will include the list of available columns.
        FileNotFoundError: If the specified CSV file cannot be found.
        IndexError: If start + exposure exceeds the number of data rows in the file.
    
    Returns:
        None
    
    Example:
        >>> # Set MOT_switch to 1 for rows 31-40 in Background.csv
        >>> ModifyCSV('Background.csv', 'MOT_switch', start=31, exposure=10, value=1)
        Data overwritten Background.csv MOT_switch
        
        >>> # Set Probe_switch to 0.111 for rows 251-270
        >>> ModifyCSV('Background.csv', 'Probe_switch', start=251, exposure=20, value=0.111)
        Data overwritten Background.csv Probe_switch
    
    Note:
        - The function modifies the original file in place
        - Row numbering is 1-indexed (first data row after header is row 1)
        - If start + exposure exceeds available rows, only existing rows are modified
        - All values are stored as strings in the CSV file
    """
    folder_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(folder_path, file_name)

    with open(file_path, "r") as file:
        reader = csv.DictReader(file)
        data = list(reader)
        fieldnames = reader.fieldnames
    
    # Throw exception if device column not found
    if device not in fieldnames:
        raise ValueError(f"Column '{device}' not found in CSV file '{file_name}'. Available columns: {list(fieldnames)}")
    
    # Modify the specified rows directly (no copy needed)
    for i in range(start - 1, min(start - 1 + exposure, len(data))):
        data[i][device] = str(value)
    
    # Write back using DictWriter
    with open(file_path, "w", newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        print(f"Data overwritten {file_name} {device}\n")
    
    return None

def ModifyCSVOld(FileName, device, start, exposure, value):
    """
    Modify FileName specified column (device).
    Pay Attention to the folder_path.
    """
    folder_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(folder_path, FileName)
    Data = []
    with open(file_path, "r") as file:
        for row in csv.reader(file):
            Data.append(row)
    Header = Data[0]
    count = 0
    for dev in Header:
        if dev == device:
            col = count
        count = count + 1
    NewData = copy.deepcopy(Data)
    for i in range(start - 1, start - 1 + exposure):
        NewData[i][col] = value
    with open(file_path, "w") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerows(NewData)
        print("Data overwritten " + FileName + " " + device + "\n")
    return None

def ModifyCSV(FileName, device, start, exposure, value):
    ModifyCSVNew(FileName, device, start-1, exposure, value)
    # ModifyCSVNew(FileName, device, start, exposure, value)

if __name__ == "__main__":
    ModifyCSV(
        FileName = "Background.csv",
        device = "MOT_switch",
        start = 31,
        exposure = 10,
        value = 1,
    )
# %% Application Example
# ModifyCSV(FileName = 'output/Background.csv', device = 'Rep_switch', start = 3, exposure = 3, value = 1)
# ModifyCSV(FileName = 'output/Background.csv', device = 'MOT_switch', start = 31, exposure = 10, value = 1)
"""
Exposure  = 200
ModifyCSV(FileName = 'output/Background.csv', device = 'MOT_switch', start = 31, exposure = Exposure//10, value = 1)
ModifyCSV(FileName = 'output/Background.csv', device = 'Rep_switch', start = 31, exposure = Exposure//10, value = 0)   
ModifyCSV(FileName = 'output/Background.csv', device = 'Probe_switch', start = 251, exposure = Exposure//10, value = 0.111) 
"""


# %%
