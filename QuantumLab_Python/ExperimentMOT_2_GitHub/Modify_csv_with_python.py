# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 14:23:24 2020

@author: MOT_User
"""
import copy
import csv


# %% Function
def ModifyCSV(FileName, device, start, exposure, value):
    """
    Modify FileName specified column (device).
    Pay Attention to the folder_path.
    """
    folder_path = r"C:\Users\MOT_USER\Documents\Python Scripts\QuantumLabPython\ExperimentMOT_special_2"
    Data = []
    with open(folder_path + "\\" + FileName, "r") as file:
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
    with open(folder_path + "\\" + FileName, "w") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerows(NewData)
        print("Data overwritten " + FileName + " " + device + "\n")
    return None


# %% Application Example
# ModifyCSV(FileName = 'output/Background.csv', device = 'Rep_switch', start = 3, exposure = 3, value = 1)
# ModifyCSV(FileName = 'output/Background.csv', device = 'MOT_switch', start = 31, exposure = 10, value = 1)
"""
Exposure  = 200
ModifyCSV(FileName = 'output/Background.csv', device = 'MOT_switch', start = 31, exposure = Exposure//10, value = 1)
ModifyCSV(FileName = 'output/Background.csv', device = 'Rep_switch', start = 31, exposure = Exposure//10, value = 0)   
ModifyCSV(FileName = 'output/Background.csv', device = 'Probe_switch', start = 251, exposure = Exposure//10, value = 0.111) 
"""
