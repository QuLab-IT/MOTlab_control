# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 10:36:15 2019

@author: ruggero

Code that is used to run the experiment.
Controls AWGs, oscilloscopes and cameras.

This script allows to determine the optimal detuning for the repump laser.
It uses Pump_and_Probe.csv but with no pumping.

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
import gc
from tqdm import tqdm
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
folder_path = r'C:\Users\MOT_USER\Documents\Python Scripts\QuantumLabPython\ExperimentMOT_special_2\Output' + '\\' + 'Repump_detuning'
        
#%% BACKGROUND
'''
Set exposure time here and others Cam parameters in Background_capture
'''
AWGBaseConfiguration()
No_MOT()
time.sleep(1.5)
###
Bkg_probe_ctrl = Background_capture(MeasType = 'Probe', Camera = 'Cam0', Exposure = 150, folder_path = folder_path)

#%% PRIMING
AWGBaseConfiguration()

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
ExperimentDuration = 0.005 ### Experiment Duration in seconds. 
number_of_experiments = 5 ### Number of experiments performed
AWGChannelsToBeUsed = ['AWG1_1', 'AWG2_1', 'AWG3_2', 'AWG5_2']
Captain_to_trigger = 'AWG1'
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
        'Cam0' : 1,
        'Cam1' : 0,
        'Cam2' : 0,
        }
NumOfConnectedCameras = 3 
ListOfCamerasToBeTriggered = ['Cam0']
#-----------------------------------------------------------------------------
if ListOfCamerasToBeTriggered:
    TLF = TransportLayerCreator() ### Create Transport Layer
    MCS = MultipleCameraSession(TLF, NumOfCamsConnected = NumOfConnectedCameras)
    time.sleep(0.1)

# %% PREPARE AWGs' OUTPUTS
'''
Import arbitrary waveforms.
The RowNumber indicates the number of different waveform you want to upload (columns in the .csv file).
Headers are the name of the imported waveforms. Make sure that those names matches the 'value' names of
the Mg.ResourceNameToJob[] for the correct device channel you want to switch on.
NOTE: values in the arbitrary waveform have to be comprised in [0, 1]
NOTE: the last value of an arbitrary waveform is kept at the end of the waveform
and is as well output before the waveform start by SetBurstOuputArbitraryWaveform()!!!
'''


WaveformList, Headers = CreateArbitraryWaveformVectorFromCSVFile('Pump_and_Probe.csv', RowNumber = 10)

if 'AWG1_1' in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob['AWG1_1']
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG1.AddArbitraryWaveformToChannelVolatileMemory(FunctionVector, AWGChannelNum = '1', FuncName = FunctionName)
    #DS_AWG1.SetSyncOn('1', '300', 'NORM') ### Sync Output
    DS_AWG1.SetBurstOuputArbitraryWaveform('1000', FuncName = FunctionName, AWGChannelNum = '1', SampleRate = '100000', VHigh = '9', VLow = '0')

if 'AWG2_1' in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob['AWG2_1']
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG2.AddArbitraryWaveformToChannelVolatileMemory(FunctionVector, AWGChannelNum = '1', FuncName = FunctionName)
    DS_AWG2.SetBurstOuputArbitraryWaveform('1000', FuncName = FunctionName, AWGChannelNum = '1', SampleRate = '100000', VHigh = '5', VLow = '0')
    
if 'AWG3_2' in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob['AWG3_2']
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG3.AddArbitraryWaveformToChannelVolatileMemory(FunctionVector, AWGChannelNum = '2', FuncName = FunctionName)
    DS_AWG3.SetBurstOuputArbitraryWaveform('1000', FuncName = FunctionName, AWGChannelNum = '2', SampleRate = '100000', VHigh = '9', VLow = '0')
    
if 'AWG5_2' in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob['AWG5_2']
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG5.AddArbitraryWaveformToChannelVolatileMemory(FunctionVector, AWGChannelNum = '2', FuncName = FunctionName)
    DS_AWG5.SetBurstOuputArbitraryWaveform('INF', FuncName = FunctionName, AWGChannelNum = '2', SampleRate = '100000', VHigh = '5', VLow = '0')
time.sleep(0.1)

# %% AWG ERROR PRINTING
print('RESUME:')
print('AWG channels to be controlled in the experiment: ', AWGChannelsToBeUsed)
print('Number of experiments to be performed: ', number_of_experiments)
print('Duration of each experiment [s]: ', ExperimentDuration)
print('Ouput to file: ', Output_file)
if 'AWG1' in Mg.OpenedResourceNames: DS_AWG1.PrintError()
if 'AWG2' in Mg.OpenedResourceNames: DS_AWG2.PrintError()
if 'AWG3' in Mg.OpenedResourceNames: DS_AWG3.PrintError()
if 'AWG4' in Mg.OpenedResourceNames: DS_AWG4.PrintError()
if 'AWG5' in Mg.OpenedResourceNames: DS_AWG5.PrintError()
if Bkg_probe_ctrl == 'Y':
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
       
    if 'Cam0' in ListOfCamerasToBeTriggered:
        MCS.Set_BurstTrigger('Cam0', 'Off')
        MCS.Set_AcquisitionMode_FrameTrigger('Cam0', 'On', TrgDelay = 70)
        MCS.Set_Gain_Exposure('Cam0', CamGain = 0, CamExposure = 150)
        MCS.Set_ROI('Cam0',  CamBinning = 1, PixelWidth = 208, PixelHeight = 208, OffX = 955, OffY = 850) 
        MCS.EnableTimeStamp('Cam0') 
    
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
        for det in tqdm(np.arange(0, 4, 0.25)):       
            det_value = 3.5 + det
            print('Probe detuning [V]: ', str(det_value))
            DS_AWG2.ApplyDCVoltage(Load ='1000', AWGChannelNum = '2', Volt = str(det_value))
            time.sleep(5) ### LOAD
            list_of_dictionaries = [] ### Each element is a dictionary. The list length is the number of experiments.
            for i in range(number_of_experiments): 
                print('Experiment', i)
                if ListOfCamerasToBeTriggered:
                    MCS.ReadyForTrigger(CamNameToPicNum, ListOfCamerasToBeTriggered) ### Cameras Ready for trigger  
                ###--------------------------------------
                time.sleep(1.2) ### FIXED PRE-LOAD
                ###--------------------------------------
                eval('DS_%s.Trigger()' %Captain_to_trigger)  ### TRIGGER
                time.sleep(ExperimentDuration) ### Wait for the experiment to end
                if ListOfCamerasToBeTriggered:
                    MCS.RetrievePictures(CamNameToPicNum, ListOfCamerasToBeTriggered) ### Retrieve Pictures form Buffer
                    list_of_dictionaries.append(MCS.CamNameToImageList)
                #print('The experiment has been allowed to run for ', ExperimentDuration, ' seconds.', sep = '')
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
   for l in range(0, 16, 1):
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

# %% Check PICTURES   
if TRG_performed == 'y':
    ### Check dark background
    Bkg_probe_mx = Image_Matrix(ImageName = 'Cam0_0_1.bmp', folder_path = folder_path + '\\' + 'Background')      
    Bkg_probe_dark_mx = Image_Matrix(ImageName = 'Cam0_0_0.bmp', folder_path = folder_path + '\\' + 'Background')                 
                        
    for i in range(0, 16, 4):                                                             
        ### Probe
        Abs_probe_mx = Image_Matrix(ImageName = 'Cam0_%d_0_0.bmp' %i, folder_path = folder_path)
        Probe_abs_I = SubtractImgs(SubtractImgs(Bkg_probe_mx.image, Bkg_probe_dark_mx.image), 
                                   SubtractImgs(Abs_probe_mx.image, Bkg_probe_dark_mx.image))
        Probe_opt = LogImg(DivideImgs(SubtractImgs(Bkg_probe_mx.image, Bkg_probe_dark_mx.image), 
                                      SubtractImgs(Abs_probe_mx.image, Bkg_probe_dark_mx.image)))
        ### Plot
        plt.figure() 
        plt.subplot(121)
        plt.tight_layout()
        plt.title('Probe Absorbed Intensity')
        plt.imshow(Probe_abs_I, cmap= 'rainbow')
        plt.colorbar()
        plt.ylabel('row [pixel]')
        plt.xlabel('col [pixel]')     
        plt.subplot(122)
        plt.tight_layout()
        plt.title('Probe Optical Thickness')
        plt.imshow(Probe_opt, cmap= 'rainbow')
        plt.colorbar()
        plt.ylabel('row [pixel]')
        plt.xlabel('col [pixel]') 
        plt.show(block = False)
        plt.savefig(folder_path + '\\' + 'Panshot_' + str(i) + '.pdf', format='pdf')

#%% OPT DENSITY vs. DETUNING
''' Detuning plot obtained averaging pixels and averaging over the number of 
experiment. Errors bars refer to the population distribution of different
experiments.
'''  
if TRG_performed == 'y':    
    row_lims  = [121,124]
    col_lims  = [85,88]
    Exp_mean_list = []
    Exp_std_list = []
    Bkg_probe_mx = Image_Matrix(ImageName = 'Cam0_0_1.bmp', folder_path = folder_path + '\\' + 'Background')      
    Bkg_probe_dark_mx = Image_Matrix(ImageName = 'Cam0_0_0.bmp', folder_path = folder_path + '\\' + 'Background')     
    
    for j in range(0, 16, 1):                
        Probe_imgs = [list_of_detunings[j][i]['Cam0'][0] for i in range(number_of_experiments)]        
        Probe_opt_imgs = [LogImg(DivideImgs(SubtractImgs(Bkg_probe_mx.image, Bkg_probe_dark_mx.image), \
                                            SubtractImgs(Probe_imgs[i], Bkg_probe_dark_mx.image))) \
                                            for i in range(number_of_experiments)]
        Px_list = [[Probe_opt_imgs[i][m,n] for m in range(*row_lims) for n in range(*col_lims)] \
                    for i in range(number_of_experiments)]
        Px_mean_list = [np.mean(Px_list[i]) for i in range(number_of_experiments)]
        Exp_mean_list.append(np.mean(Px_mean_list))
        Exp_std_list.append(std_dev(Px_mean_list))
    
    fig = plt.figure()
    plt.title('Optical Density')
    plt.xlabel('Repump detuning [V]')
    plt.errorbar([i for i in np.arange(3.5, 7.5, 0.25)], Exp_mean_list, fmt = 'o', yerr=Exp_std_list, xerr=None)
    #plt.yscale('log')
    plt.grid()
    plt.show(block = False)
    plt.savefig(folder_path + '\\' + 'Repump_Detuning.pdf', format='pdf')
    
#%% FIXED DETUNING, OPT DENSITY vs. # OF EXPERIMENTS  
''' Optical Density vs. number of experiments to check if the loading time is correct.
Error bar refers to the confidence interval of an average over pixels.
''' 
'''    
if TRG_performed == 'y':
    row_lims  = [140,143]
    col_lims  = [106,109]
    Pix_num = (row_lims[1] - row_lims[0])*(col_lims[1] - col_lims[0])
                
    Bkg_probe_mx = Image_Matrix(ImageName = 'Cam0_0_1.bmp', folder_path = folder_path + '\\' + 'Background')   
    Bkg_probe_dark_mx = Image_Matrix(ImageName = 'Cam0_0_0.bmp', folder_path = folder_path + '\\' + 'Background')   
    Probe_imgs = [list_of_detunings[0][i]['Cam0'][0] for i in range(number_of_experiments)]
    
    Probe_opt_imgs = [LogImg(DivideImgs(SubtractImgs(Bkg_probe_mx.image, Bkg_probe_dark_mx.image), SubtractImgs(Probe_imgs[i],Bkg_probe_dark_mx.image))) for i in range(number_of_experiments)]
    Px_list = [[Probe_opt_imgs[i][m,n] for m in range(*row_lims) for n in range(*col_lims)] for i in range(number_of_experiments)]
    Px_mean_list = [np.mean(Px_list[i]) for i in range(number_of_experiments)]
    Px_std_list = [std_dev(Px_list[i]) for i in range(number_of_experiments)]
    Px_std_avg_list = [std_dev(Px_list[i])/np.sqrt(Pix_num) for i in range(number_of_experiments)]
    
    fig = plt.figure()
    plt.title('Pixel Averaged Optical Density')
    plt.xlabel('Experiment number')
    plt.errorbar([i for i in range(number_of_experiments)], Px_mean_list, fmt = 'o', yerr=Px_std_avg_list, xerr=None)
    #plt.yscale('log')
    plt.ylim(0, 5)
    plt.grid()
    plt.show(block = False)
    plt.savefig(folder_path + '\\' + 'OptDens_vs_NumOfExperiments.pdf', format='pdf')
'''
#%% Release Memory
if TRG == 'y':
    del list_of_detunings, list_of_dictionaries, Probe_imgs, Probe_opt_imgs, Px_list
    gc.collect()





















