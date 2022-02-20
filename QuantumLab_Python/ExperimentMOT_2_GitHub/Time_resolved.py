# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 10:36:15 2019

@author: ruggero

Code that is used to run the experiment.
Controls AWGs, oscilloscopes and cameras.

"""

### Standard library imports
import matplotlib.pyplot as plt
import time
import sys
import numpy as np
import csv
from struct import unpack
from PIL import Image
from scipy import ndimage, optimize
import cv2
import random
import os
import gc
### Third party imports
from pypylon import pylon
from pypylon import genicam
import pyvisa as visa
### Local application imports
from MultiResources import ResourceManagerCreator, ResourceSession, AWGSession, OscilloscopeSession, CreateArbitraryWaveformVectorFromCSVFile, SelectWaveform
from CameraResources import TransportLayerCreator, MultipleCameraSession
from AnalysysBMP_Exp import Gauss, FlatTopGauss, SaturatedExp, std_dev, SubtractImgs, LogImg, DivideImgs, PanShotAbsorption, PanShotAbsorptionReduced, Image_Matrix
from Modify_csv_with_python import ModifyCSV
#from Start import AWGBaseConfiguration, No_MOT, ClearAllVolatiles, AWGSafeConfiguration, CloseEverythingSafely, Background_capture

#%% FOLDER REFERENCE
dirName = 'Exp0' 
#-----------------------------------------------------------------------------
folder_path = r'C:\Users\MOT_USER\Documents\Python Scripts\QuantumLabPython\ExperimentMOT_special_2\Output'  + '\\' + 'Time_resolved'
if not os.path.exists(folder_path + '\\' + dirName):
    os.mkdir(folder_path + '\\' + dirName)
    print("Directory " , dirName ,  " Created ")
else:    
    print("Directory " , dirName ,  " already exists")
folder_path = folder_path + '\\' + dirName    
    
#%%    
### Define exposures for background and experiment (200-500 us)
Exposure_Cam2 = 500
det_value = 3.25

#%% BACKGROUND
'''
Set exposure time here and others Cam parameters in Background_capture
'''
AWGBaseConfiguration()
No_MOT()
time.sleep(1.5)
###
Bkg_scatt_2_ctrl = Background_capture(MeasType = 'Scattering', Camera = 'Cam2', Exposure = Exposure_Cam2, folder_path = folder_path)

#%% PRIMING
AWGBaseConfiguration()
No_MOT()

# %%  INITIALISATION VISA devices (AWGs, Oscilloscopes)
''' 
ALWAYS CHECK VOLTAGE LIMITS AND LOADS!!! 
NOTE: define a Mg just if it hasn't been created yet by another script!!!
NOTE: 
The AWG that has been selected as 'Captain' should be initialised as 'Captain'
and Captain_to_trigger should contain its name. 
There can be just one Captain.
The Captain CH_1 needs to be triggered during the experiment.
Assumes Resource Mangaer alredy created and resources already opened.
'''
ExperimentDuration = 31 ### Experiment Duration in seconds. 
number_of_experiments = 1 ### Number of experiments performed
Output_file = 'y' ### 'y' or 'n': if you want the cameras output in a file
#-----------------------------------------------------------------------------
TRG_performed = 'n' ### Variable that controls if trigger has been performed ['n','y']
WaveformList = []
Headers = []

# %%  INITIALISATION PYLON devices (Cameras)
''' All the Cameras are Opened. Just those in ListOfCamerasToBeTriggered
are triggered.
DO NOT open Pylon Viewer when the cameras are managed by PyPylon!
'''
CamNameToPicNum = {
        'Cam0' : 0,
        'Cam1' : 0,
        'Cam2' : 20000,
        }
NumOfConnectedCameras = 3 
ListOfCamerasToBeTriggered = ['Cam2']
#-----------------------------------------------------------------------------
if ListOfCamerasToBeTriggered:
    TLF = TransportLayerCreator() ### Create Transport Layer
    MCS = MultipleCameraSession(TLF, NumOfCamsConnected = NumOfConnectedCameras)
    time.sleep(0.1)

# %% AWG ERROR PRINTING
print('RESUME:')
print('Number of experiments to be performed: ', number_of_experiments)
print('Duration of each experiment [s]: ', ExperimentDuration)
print('Ouput to file: ', Output_file)
if 'AWG1' in Mg.OpenedResourceNames: DS_AWG1.PrintError()
if 'AWG2' in Mg.OpenedResourceNames: DS_AWG2.PrintError()
if 'AWG3' in Mg.OpenedResourceNames: DS_AWG3.PrintError()
if 'AWG4' in Mg.OpenedResourceNames: DS_AWG4.PrintError()
if 'AWG5' in Mg.OpenedResourceNames: DS_AWG5.PrintError()
if Bkg_scatt_2_ctrl == 'Y':
    print('Background correctly acquired')
else: print('Background NOT correctly acquired!!!')
TRG = input('Do you want to trigger (y/n)? ')
time.sleep(0.1)

#%%% OUTPUT TO FILE
'''Choose the file name where you want to store the log of the experiment.'''
if Output_file == 'y':
    orig_stdout = sys.stdout
    print('\n Output to file \n')
    Output_destination = folder_path + '\\' + 'output.txt'
    f = open(Output_destination, 'w')
    sys.stdout = f
    
# %% PREPARE CAMERAS   
try: 
    if ListOfCamerasToBeTriggered:
        MCS.SetAllCamerasToDefaultConfiguration()
          
    if 'Cam2' in ListOfCamerasToBeTriggered:
        MCS.Set_BurstTrigger('Cam2', 'Off')
        MCS.Set_AcquisitionMode_FrameTrigger('Cam2', 'Off', TrgDelay = 0)
        MCS.Set_Gain_Exposure('Cam2', CamGain = 6, CamExposure = Exposure_Cam2)
        MCS.Set_ROI('Cam2', CamBinning = 1, PixelWidth = 144, PixelHeight = 144, OffX = 1150, OffY = 720)
        MCS.EnableTimeStamp('Cam2')

except Exception as excep: 
    if Output_file == 'y':
        sys.stdout = orig_stdout
        f.close()
        print('\n Output to console \n')
    print(excep)
    print(' \n !!! Something went wrong with Cameras!') 
    TRG = 'n'
time.sleep(0.1)

# %% TRIGGER EXPERIMENT  
if TRG == 'y':
    print('START EXPERIMENTS: ', '\n')
    try: 
        list_of_detunings = []
        for det in range(0, 1, 1):       
            print('MOT detuning [V]: ', str(det_value))
            DS_AWG1.ApplyDCVoltage(Load ='1000', AWGChannelNum = '2', Volt = str(det_value))
            DS_AWG1.ApplyDCVoltage(Load ='1000', AWGChannelNum = '1', Volt = '1')   
            DS_AWG2.ApplyDCVoltage(Load ='1000', AWGChannelNum = '1', Volt = '5')
            DS_AWG5.ApplyDCVoltage(Load ='INF', AWGChannelNum = '1', Volt = '5')
            time.sleep(6) ### LOAD       
            list_of_dictionaries = [] ### Each element is a dictionary. The list length is the number of experiments.
            for i in range(number_of_experiments): 
                print('Experiment', i)
                if ListOfCamerasToBeTriggered:
                    MCS.ReadyForTrigger(CamNameToPicNum, ListOfCamerasToBeTriggered) ### Cameras Ready for trigger  
                #time.sleep(ExperimentDuration) ### Wait for the experiment to end                  
                if ListOfCamerasToBeTriggered:
                    MCS.RetrievePictures(CamNameToPicNum, ListOfCamerasToBeTriggered) ### Retrieve Pictures from Buffer
                    list_of_dictionaries.append(MCS.CamNameToImageList)
                print('Experiment concluded.', '\n')
                TRG_performed = 'y'
            list_of_detunings.append(list_of_dictionaries)
    except Exception as excep: 
        if Output_file == 'y':
            sys.stdout = orig_stdout
            f.close()
            print('\n Output to console \n')
        print(excep)
        print('\n !!! Something went wrong!')
        TRG_performed = 'n'
else: print('Trigger hasn\'t been performed', '\n')
time.sleep(0.1)

#%% OUTPUT TO STANDARD OUTPUT
if Output_file == 'y':
    if sys.stdout != orig_stdout:
        sys.stdout = orig_stdout
        f.close()
        print('\n Output to console \n')
    if TRG_performed == 'y':
        print('Experiment concluded.', '\n')
        
#%% SAVE PICTURES TO FILE
if TRG_performed == 'y':
   print('...Saving Pictures... \n')
   for l in range(0, 1, 1):
        for j in range(number_of_experiments):
            for i in ListOfCamerasToBeTriggered:
                for k in range(CamNameToPicNum[i]):
                    im = Image.fromarray(list_of_detunings[l][j][i][k])
                    img_name_tosave = folder_path + '\\' + i + '_' + str(l) + '_' + str(j) + '_' + str(k) + '.bmp'
                    im.save(img_name_tosave)
                    
# %% CLOSE DEVICES AND GO BACK TO NORMAL CONFIGURATION   
AWGBaseConfiguration()

if ListOfCamerasToBeTriggered:
    MCS.SetAllCamerasToDefaultConfiguration()
    MCS.CloseAllCameras() ###Always close the cameras!
                    
#%% CHECK FIRST AND LAST PICTURES
if TRG_performed == 'y':
    for i in ListOfCamerasToBeTriggered:
        Bkg_Cam2_mx = Image_Matrix(ImageName = i + '_0_0.bmp', folder_path = folder_path + '\\' + 'Background')  
        Cam2_mx = Image_Matrix(ImageName = i + '_0_0_0.bmp', folder_path = folder_path)
        Cam2_img = SubtractImgs(Cam2_mx.image, Bkg_Cam2_mx.image)
        Cam2_last_mx = Image_Matrix(ImageName = i + '_0_0_%d.bmp' %(CamNameToPicNum[i]-1), folder_path = folder_path)
        Cam2_last_img = SubtractImgs(Cam2_last_mx.image, Bkg_Cam2_mx.image)
        
        ### PLOTS
        plt.figure()     
        plt.subplot(131)
        plt.tight_layout()
        plt.title(i + ' first picture')
        plt.imshow(Cam2_img, cmap= 'rainbow')
        plt.colorbar()
        plt.ylabel('row [pixel]')
        plt.xlabel('col [pixel]')     
        plt.subplot(132)
        plt.tight_layout()
        plt.title(i + ' last picture')
        plt.imshow(Cam2_last_img, cmap= 'rainbow')
        plt.colorbar()
        plt.ylabel('row [pixel]')
        plt.xlabel('col [pixel]') 
        plt.subplot(133)
        plt.tight_layout()
        plt.title(i + ' Background')
        plt.imshow(Bkg_Cam2_mx.image, cmap= 'rainbow')
        plt.colorbar()
        plt.ylabel('row [pixel]')
        plt.xlabel('col [pixel]') 
        plt.show(block = False)
        plt.savefig(folder_path + '\\' + 'panshot.pdf', format='pdf')

#%% Release Memory
if TRG == 'y':
    del list_of_detunings, list_of_dictionaries
    gc.collect()




















