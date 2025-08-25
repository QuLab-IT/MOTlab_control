# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 10:36:15 2019

@author: ruggero

Code that is used to run the experiment.
Controls AWGs, oscilloscopes and cameras.

"""

import gc
import sys
import time

### Standard library imports
import matplotlib.pyplot as plt
import numpy as np
from QuantumLab_Python.ExperimentMOT_2_GitHub.utils.AnalysysBMP_Exp import Image_Matrix, SaturatedExp, SubtractImgs
from QuantumLab_Python.ExperimentMOT_2_GitHub.utils.CameraResources import MultipleCameraSession
### Third party imports
### Local application imports
from QuantumLab_Python.ExperimentMOT_2_GitHub.utils.MultiResources import (CreateArbitraryWaveformVectorFromCSVFile,
                            SelectWaveform)
from PIL import Image
from scipy import optimize
from scipy.fftpack import fft

#from Start import AWGBaseConfiguration, No_MOT, ClearAllVolatiles, AWGSafeConfiguration, CloseEverythingSafely, Background_capture

#%% FOLDER REFERENCE
folder_path = r'C:\Users\MOT_USER\Documents\Python Scripts\QuantumLabPython\ExperimentMOT_special_2\Output' + '\\' + 'Pressure_measurements'
Exposure = 250 
        
#%% BACKGROUND
'''
Set exposure time here and others Cam parameters in Background_capture
'''
AWGBaseConfiguration()
No_MOT()
time.sleep(1.5)
###
#Bkg_Cam0_ctrl = Background_capture(MeasType = 'Scattering', Camera = 'Cam0', Exposure = Exposure , folder_path = folder_path)
Bkg_Cam2_ctrl = Background_capture(MeasType = 'Scattering', Camera = 'Cam2', Exposure = Exposure , folder_path = folder_path)

### Magnetic Field on
if 'AWG5' in Mg.OpenedResourceNames: DS_AWG5.ApplyDCVoltage(Load ='INF', AWGChannelNum = '1', Volt = '5')

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
ExperimentDuration = 2.5 ### Experiment Duration in seconds. 
number_of_experiments = 1 ### Number of experiments performed
AWGChannelsToBeUsed = ['AWG1_1', 'AWG2_1', 'AWG5_2']
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
        'Cam0' : 0,
        'Cam1' : 0,
        'Cam2' : 500,
        }
NumOfConnectedCameras = 3 
ListOfCamerasToBeTriggered = ['Cam2']
#-----------------------------------------------------------------------------
if ListOfCamerasToBeTriggered:
    MCS = MultipleCameraSession(NumOfCamsConnected = NumOfConnectedCameras)
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
WaveformList, Headers = CreateArbitraryWaveformVectorFromCSVFile('Pressure_measurements.csv', RowNumber = 10)

if 'AWG1_1' in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob['AWG1_1']
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG1.AddArbitraryWaveformToChannelVolatileMemory(FunctionVector, AWGChannelNum = '1', FuncName = FunctionName)
    #DS_AWG1.SetSyncOn('1', '300', 'NORM') ### Sync Output
    DS_AWG1.SetBurstOuputArbitraryWaveform('1000', FuncName = FunctionName, AWGChannelNum = '1', SampleRate = '1000', VHigh = '9', VLow = '0')

if 'AWG1_2' in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob['AWG1_2']
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG1.AddArbitraryWaveformToChannelVolatileMemory(FunctionVector, AWGChannelNum = '2', FuncName = FunctionName)
    DS_AWG1.SetBurstOuputArbitraryWaveform('1000', FuncName = FunctionName, AWGChannelNum = '2', SampleRate = '1000', VHigh = '9', VLow = '0')

if 'AWG2_1' in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob['AWG2_1']
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG2.AddArbitraryWaveformToChannelVolatileMemory(FunctionVector, AWGChannelNum = '1', FuncName = FunctionName)
    DS_AWG2.SetBurstOuputArbitraryWaveform('1000', FuncName = FunctionName, AWGChannelNum = '1', SampleRate = '1000', VHigh = '5', VLow = '0')
    
if 'AWG5_2' in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob['AWG5_2']
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG5.AddArbitraryWaveformToChannelVolatileMemory(FunctionVector, AWGChannelNum = '2', FuncName = FunctionName)
    DS_AWG5.SetBurstOuputArbitraryWaveform('INF', FuncName = FunctionName, AWGChannelNum = '2', SampleRate = '1000', VHigh = '5', VLow = '0')
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
if Bkg_Cam2_ctrl == 'Y':
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
        MCS.Set_AcquisitionMode_FrameTrigger('Cam2', 'On', TrgDelay = 0)
        MCS.Set_Gain_Exposure('Cam2', CamGain = 6, CamExposure = Exposure )
        MCS.Set_ROI('Cam2', CamBinning = 1, PixelWidth = 144, PixelHeight = 144, OffX = 1170, OffY = 720)
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
            list_of_dictionaries = [] ### Each element is a dictionary. The list length is the number of experiments.
            for i in range(number_of_experiments): 
                print('Experiment', i)
                if ListOfCamerasToBeTriggered:
                    MCS.ReadyForTrigger(CamNameToPicNum, ListOfCamerasToBeTriggered) ### Cameras Ready for trigger  
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
    for l in range (0, 1, 1):
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
''' Panshot first and last pictures'''
if TRG_performed == 'y':                               
    for cam in ListOfCamerasToBeTriggered:    
        Cam_first_mx = Image_Matrix(ImageName = '%s_0_0_0.bmp' %cam, folder_path = folder_path)
        Cam_last_mx = Image_Matrix(ImageName = '%s_0_0_499.bmp' %cam, folder_path = folder_path)
        Bkg_Cam_mx = Image_Matrix(ImageName = '%s_0_0.bmp' %cam, folder_path = folder_path + '\\' + 'Background')
        ### Plot
        plt.figure() 
        plt.subplot(121)
        plt.tight_layout()
        plt.title('%s first picture' %cam)
        plt.imshow(SubtractImgs(Cam_first_mx.image, Bkg_Cam_mx.image), cmap= 'rainbow')
        plt.colorbar() 
        plt.ylabel('row [pixel]')
        plt.xlabel('col [pixel]')    
        plt.subplot(122)
        plt.tight_layout()
        plt.title('%s last picture' %cam)
        plt.imshow(SubtractImgs(Cam_last_mx.image, Bkg_Cam_mx.image), cmap= 'rainbow')
        plt.colorbar() 
        plt.ylabel('row [pixel]')
        plt.xlabel('col [pixel]')    
        plt.show(block = False)
        
#%% LOADING TIME PLOT
if TRG_performed == 'y':  
    for cam in ListOfCamerasToBeTriggered:
        Bkg_Cam_mx = Image_Matrix(ImageName = '%s_0_0.bmp' %cam, folder_path = folder_path + '\\' + 'Background')
        Cam_imgs = [(SubtractImgs(list_of_detunings[0][0][cam][i], Bkg_Cam_mx.image)) for i in range(CamNameToPicNum[cam])] 
        Px_Cam_list = [[Cam_imgs[i][m,n] for m in range(0, Bkg_Cam_mx.image.shape[0]) for n in range(0, Bkg_Cam_mx.image.shape[1])] for i in range(CamNameToPicNum[cam])]
        Px_sum_cam_list = [(sum(Px_Cam_list[i])/1000) for i in range(CamNameToPicNum[cam])]
        time_base = np.array([i for i in np.arange(0, 2.5, 0.005)])
        ### FIT
        popt, pcov = optimize.curve_fit(SaturatedExp, time_base, Px_sum_cam_list, method = 'trf')
        print('Fit Parameters [a,x0,sigma, c] %s:' %cam, popt) ### [a,x0,sigma, c]
        fit_array = SaturatedExp(time_base, *popt)        
        ###PLOT
        plt.figure() 
        plt.tight_layout()
        plt.title('%s Loading Time' %cam)
        plt.plot(time_base, Px_sum_cam_list, '.')
        plt.plot(time_base, fit_array, '-')
        plt.ylabel('Pixel integrated Intensity [a.u.]')
        plt.xlabel('t [s]')     
        plt.savefig(folder_path + '\\' + 'LoadingTime_%s' %cam + '.pdf', format='pdf')
        plt.show(block = False)

        ### Fourier Transform of raw intensity
        plt.figure()
        I_fft_arr = fft(np.array(Px_sum_cam_list))
        tf = np.linspace(0, int(len(I_fft_arr)/(2*ExperimentDuration)), int(len(I_fft_arr)/2))  
        plt.plot(tf[10:], (2.0/len(I_fft_arr)) * np.abs(I_fft_arr[10:len(I_fft_arr)//2]))
        plt.xlabel('Frequency [Hz]')
        plt.ylabel('Intensity [a.u.]')
        plt.tight_layout()
        plt.grid()
        plt.savefig(folder_path + '\\' + 'LoadingTime_Fourier_%s' %cam + '.pdf', format='pdf')
        plt.show(block = False)
        
        ### Fourier Transform Log plot
        plt.figure()
        plt.plot(tf[0:], (2.0/len(I_fft_arr)) * np.log(np.abs(I_fft_arr[0:len(I_fft_arr)//2])))
        plt.xlabel('Frequency [Hz]')
        plt.ylabel('Intensity Log [a.u.]')
        plt.tight_layout()
        plt.grid()
        plt.show(block = False)
    
#%% Release Memory
if TRG == 'y':
    del list_of_detunings, list_of_dictionaries, Cam_imgs, Px_Cam_list
    gc.collect()






















