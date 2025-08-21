# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 10:36:15 2019

@author: ruggero

Code that is used to run the experiment.
Controls AWGs, oscilloscopes and cameras.

"""

import csv
import gc
import sys
import time

### Standard library imports
import matplotlib.pyplot as plt
import numpy as np
from AnalysysBMP_Exp import Image_Matrix, SubtractImgs, std_dev
from CameraResources import MultipleCameraSession, TransportLayerCreator
from Modify_csv_with_python import ModifyCSV

### Local application imports
from MultiResources import CreateArbitraryWaveformVectorFromCSVFile, SelectWaveform
from PIL import Image
from tqdm import tqdm

# from Start import AWGBaseConfiguration, No_MOT, ClearAllVolatiles, AWGSafeConfiguration, CloseEverythingSafely, Background_capture

# %% FOLDER REFERENCE
folder_path = (
    r"C:\Users\MOT_USER\Documents\Python Scripts\QuantumLabPython\ExperimentMOT_special_2\Output"
    + "\\"
    + "MOT_detuning"
)
Wait = 300  ### Wait before scattering measurement, after unloading the MOT, us
Exposure = 180  ### us

ModifyCSV(
    FileName="MOT_detuning.csv",
    device="MOT_switch",
    start=31 + Wait // 10,
    exposure=Exposure // 10,
    value=0.111,
)
ModifyCSV(
    FileName="MOT_detuning.csv", device="AWG5_2", start=31, exposure=Wait // 10, value=1
)

# %% BACKGROUND
"""
Set exposure time here and others Cam parameters in Background_capture
"""
AWGBaseConfiguration()
No_MOT()
time.sleep(1.5)
###
Bkg_Cam2_ctrl = Background_capture(
    MeasType="Scattering", Camera="Cam2", Exposure=Exposure, folder_path=folder_path
)
AWGBaseConfiguration()

# %%  INITIALISATION VISA devices (AWGs, Oscilloscopes)
""" 
ALWAYS CHECK VOLTAGE LIMITS AND LOADS!!! 
NOTE: define a Mg just if it hasn't been created yet by another script!!!
NOTE: 
The AWG that has been selected as 'Captain' should be initialised as 'Captain'
and Captain_to_trigger should contain its name. 
There can be just one Captain.
The Captain CH_1 needs to be triggered during the experiment.
Assumes Resource Mangaer alredy created and resources already opened.
"""
ExperimentDuration = 0.007  ### Experiment Duration in seconds.
number_of_experiments = 5  ### Number of experiments performed
AWGChannelsToBeUsed = ["AWG1_1", "AWG1_2", "AWG2_1", "AWG5_2"]
Captain_to_trigger = "AWG1"
Output_file = "y"  ### 'y' or 'n': if you want the cameras output in a file
# -----------------------------------------------------------------------------
TRG_performed = "n"  ### Variable that controls if trigger has been performed ['n','y']
WaveformList = []
Headers = []

# %%  INITIALISATION PYLON devices (Cameras)
""" All the Cameras are Opened. Just those in ListOfCamerasToBeTriggered
are triggered.
DO NOT open Pylon Viewer when the cameras are managed by PyPylon!
"""
CamNameToPicNum = {
    "Cam0": 0,
    "Cam1": 0,
    "Cam2": 1,
}
NumOfConnectedCameras = 3
ListOfCamerasToBeTriggered = ["Cam2"]
# -----------------------------------------------------------------------------
if ListOfCamerasToBeTriggered:
    TLF = TransportLayerCreator()  ### Create Transport Layer
    MCS = MultipleCameraSession(TLF, NumOfCamsConnected=NumOfConnectedCameras)
    time.sleep(0.1)

# %% PREPARE AWGs' OUTPUTS
"""
Import arbitrary waveforms.
The RowNumber indicates the number of different waveform you want to upload (columns in the .csv file).
Headers are the name of the imported waveforms. Make sure that those names matches the 'value' names of
the Mg.ResourceNameToJob[] for the correct device channel you want to switch on.
NOTE: values in the arbitrary waveform have to be comprised in [0, 1]
NOTE: the last value of an arbitrary waveform is kept at the end of the waveform
and is as well output before the waveform start by SetBurstOuputArbitraryWaveform()!!!
"""
WaveformList, Headers = CreateArbitraryWaveformVectorFromCSVFile(
    "MOT_detuning.csv", RowNumber=10
)

if "AWG1_1" in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob["AWG1_1"]
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG1.AddArbitraryWaveformToChannelVolatileMemory(
        FunctionVector, AWGChannelNum="1", FuncName=FunctionName
    )
    # DS_AWG1.SetSyncOn('1', '300', 'NORM') ### Sync Output
    DS_AWG1.SetBurstOuputArbitraryWaveform(
        "1000",
        FuncName=FunctionName,
        AWGChannelNum="1",
        SampleRate="100000",
        VHigh="9",
        VLow="0",
    )

if "AWG1_2" in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob["AWG1_2"]
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG1.AddArbitraryWaveformToChannelVolatileMemory(
        FunctionVector, AWGChannelNum="2", FuncName=FunctionName
    )
    DS_AWG1.SetBurstOuputArbitraryWaveform(
        "1000",
        FuncName=FunctionName,
        AWGChannelNum="2",
        SampleRate="100000",
        VHigh="9",
        VLow="0",
    )

if "AWG2_1" in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob["AWG2_1"]
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG2.AddArbitraryWaveformToChannelVolatileMemory(
        FunctionVector, AWGChannelNum="1", FuncName=FunctionName
    )
    DS_AWG2.SetBurstOuputArbitraryWaveform(
        "1000",
        FuncName=FunctionName,
        AWGChannelNum="1",
        SampleRate="100000",
        VHigh="5",
        VLow="0",
    )

if "AWG5_1" in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob["AWG5_1"]
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG5.AddArbitraryWaveformToChannelVolatileMemory(
        FunctionVector, AWGChannelNum="1", FuncName=FunctionName
    )
    DS_AWG5.SetBurstOuputArbitraryWaveform(
        "INF",
        FuncName=FunctionName,
        AWGChannelNum="1",
        SampleRate="100000",
        VHigh="5",
        VLow="0",
    )

if "AWG5_2" in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob["AWG5_2"]
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG5.AddArbitraryWaveformToChannelVolatileMemory(
        FunctionVector, AWGChannelNum="2", FuncName=FunctionName
    )
    DS_AWG5.SetBurstOuputArbitraryWaveform(
        "INF",
        FuncName=FunctionName,
        AWGChannelNum="2",
        SampleRate="100000",
        VHigh="5",
        VLow="0",
    )
time.sleep(0.1)

# %% AWG ERROR PRINTING
print("RESUME:")
print("AWG channels to be controlled in the experiment: ", AWGChannelsToBeUsed)
print("Number of experiments to be performed: ", number_of_experiments)
print("Duration of each experiment [s]: ", ExperimentDuration)
print("Ouput to file: ", Output_file)
if "AWG1" in Mg.OpenedResourceNames:
    DS_AWG1.PrintError()
if "AWG2" in Mg.OpenedResourceNames:
    DS_AWG2.PrintError()
if "AWG3" in Mg.OpenedResourceNames:
    DS_AWG3.PrintError()
if "AWG4" in Mg.OpenedResourceNames:
    DS_AWG4.PrintError()
if "AWG5" in Mg.OpenedResourceNames:
    DS_AWG5.PrintError()
if Bkg_Cam2_ctrl == "Y":
    print("Background correctly acquired")
else:
    print("Background NOT correctly acquired!!!")
TRG = input("Do you want to trigger (y/n)? ")
time.sleep(0.1)

# %%% OUTPUT TO FILE
"""Choose the file name where you want to store the log of the experiment."""
if Output_file == "y":
    orig_stdout = sys.stdout
    print("\n Output to file \n")
    Output_destination = folder_path + "\\" + "output.txt"
    f = open(Output_destination, "w")
    sys.stdout = f

# %% PREPARE CAMERAS
try:
    if ListOfCamerasToBeTriggered:
        MCS.SetAllCamerasToDefaultConfiguration()

    if "Cam2" in ListOfCamerasToBeTriggered:
        MCS.Set_BurstTrigger("Cam2", "Off")
        MCS.Set_AcquisitionMode_FrameTrigger("Cam2", "On", TrgDelay=0)
        MCS.Set_Gain_Exposure("Cam2", CamGain=6, CamExposure=Exposure)
        MCS.Set_ROI(
            "Cam2", CamBinning=1, PixelWidth=144, PixelHeight=144, OffX=1170, OffY=710
        )
        MCS.EnableTimeStamp("Cam2")

except Exception as excep:
    if Output_file == "y":
        sys.stdout = orig_stdout
        f.close()
        print("\n Output to console \n")
    print(excep)
    print(" \n !!! Something went wrong with Cameras!")
    TRG = "n"
time.sleep(0.1)

# %% TRIGGER EXPERIMENT
if TRG == "y":
    print("START EXPERIMENTS: ", "\n")
    time.sleep(5)  ### LOAD
    try:
        list_of_detunings = []
        for det in tqdm(np.arange(0, 4, 0.25)):
            ###------------------------------------------------------------
            det_value = 5 + det
            print("MOT scattering detuning [V]: ", str(det_value))
            ModifyCSV(
                FileName="MOT_detuning.csv",
                device="MOT_2pass",
                start=31,
                exposure=Exposure // 10 + Wait // 10,
                value=round(det_value / 9, 3),
            )
            WaveformList, Headers = CreateArbitraryWaveformVectorFromCSVFile(
                "MOT_detuning.csv", RowNumber=10
            )
            if "AWG1_2" in AWGChannelsToBeUsed:
                DS_AWG1.ClearVolatileMemory("2")
                FunctionName = Mg.ResourceNameToJob["AWG1_2"]
                FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
                DS_AWG1.AddArbitraryWaveformToChannelVolatileMemory(
                    FunctionVector, AWGChannelNum="2", FuncName=FunctionName
                )
                DS_AWG1.SetBurstOuputArbitraryWaveform(
                    "1000",
                    FuncName=FunctionName,
                    AWGChannelNum="2",
                    SampleRate="100000",
                    VHigh="9",
                    VLow="0",
                )
            ###------------------------------------------------------------
            list_of_dictionaries = (
                []
            )  ### Each element is a dictionary. The list length is the number of experiments.
            for i in range(number_of_experiments):
                print("Experiment", i)
                if ListOfCamerasToBeTriggered:
                    MCS.ReadyForTrigger(
                        CamNameToPicNum, ListOfCamerasToBeTriggered
                    )  ### Cameras Ready for trigger
                ###--------------------------------------
                time.sleep(2)  ### FIXED PRE-LOAD
                ###--------------------------------------
                eval("DS_%s.Trigger()" % Captain_to_trigger)  ### TRIGGER
                time.sleep(ExperimentDuration)  ### Wait for the experiment to end
                if ListOfCamerasToBeTriggered:
                    MCS.RetrievePictures(
                        CamNameToPicNum, ListOfCamerasToBeTriggered
                    )  ### Retrieve Pictures form Buffer
                    list_of_dictionaries.append(MCS.CamNameToImageList)
                # print('The experiment has been allowed to run for ', ExperimentDuration, ' seconds.', sep = '')
                print("Experiment concluded.", "\n")
                TRG_performed = "y"
            list_of_detunings.append(list_of_dictionaries)
    except Exception as excep:
        if Output_file == "y":
            sys.stdout = orig_stdout
            f.close()
            print("\n Output to console \n")
        print(excep)
        print("\n !!! Something went wrong!")
        TRG_performed = "n"
else:
    print("As requested, trigger hasn't been performed", "\n")
time.sleep(0.1)

# %% OUTPUT TO STANDARD OUTPUT
if Output_file == "y":
    if sys.stdout != orig_stdout:
        sys.stdout = orig_stdout
        f.close()
        print("\n Output to console \n")
    if TRG_performed == "y":
        print("Experiment concluded.", "\n")

# %% SAVE PICTURES TO FILE
if TRG_performed == "y":
    print("...Saving Pictures... \n")
    for l in range(0, 16, 1):
        for j in range(number_of_experiments):
            for i in ListOfCamerasToBeTriggered:
                for k in range(CamNameToPicNum[i]):
                    im = Image.fromarray(list_of_detunings[l][j][i][k])
                    img_name_tosave = (
                        folder_path
                        + "\\"
                        + i
                        + "_"
                        + str(l)
                        + "_"
                        + str(j)
                        + "_"
                        + str(k)
                        + ".bmp"
                    )
                    im.save(img_name_tosave)

# %% CLOSE DEVICES AND GO BACK TO NORMAL CONFIGURATION
ModifyCSV(
    FileName="MOT_detuning.csv",
    device="MOT_switch",
    start=31 + Wait // 10,
    exposure=Exposure // 10,
    value=1,
)
ModifyCSV(
    FileName="MOT_detuning.csv",
    device="AWG5_2",
    start=31,
    exposure=Exposure // 10 + Wait // 10,
    value=0,
)
ModifyCSV(
    FileName="MOT_detuning.csv",
    device="MOT_2pass",
    start=31,
    exposure=Exposure // 10 + Wait // 10,
    value=0.444,
)

AWGBaseConfiguration()

if ListOfCamerasToBeTriggered:
    MCS.SetAllCamerasToDefaultConfiguration()
    MCS.CloseAllCameras()  ###Always close the cameras!

# %% Check PICTURES
""" A panshot for each detuning"""

if TRG_performed == "y":
    index_plot = 231
    Bkg_Cam2_mx = Image_Matrix(
        ImageName="Cam2_0_0.bmp", 
        folder_path=folder_path + "\\" + "Background",
    )
    plt.figure()
    plt.show(block=False)
    plt.title("Cam2 MOT detuning Panshot")
    ax = plt.subplot(index_plot)
    plt.tight_layout()
    ax.set_title("Background")
    plt.imshow(Bkg_Cam2_mx.image, cmap="gray")
    plt.colorbar()
    plt.ylabel("row [pixel]")
    plt.xlabel("col [pixel]")

    for i in range(3, 16, 3):
        index_plot += 1
        Cam2_mx = Image_Matrix(ImageName="Cam2_%d_0_0.bmp" % i, folder_path=folder_path)
        plt.subplot(index_plot)
        plt.tight_layout()
        plt.imshow(SubtractImgs(Cam2_mx.image, Bkg_Cam2_mx.image), cmap="rainbow")
        plt.colorbar()
        plt.ylabel("row [pixel]")
        plt.xlabel("col [pixel]")

# %% IMPORT MOT 2-PASS AOM EFFICIENCY CURVE
Data = []
with open(
    r"C:\Users\MOT_USER\Documents\Python Scripts\QuantumLabPython\ExperimentMOT_special_2\MOT_AOM_curve.csv",
    "r",
) as file:
    j = 1
    for row in csv.reader(file):
        if j <= 33:
            Data.append([float(i) for i in row])
            j += 1
detunings = [round(Data[i][0], 3) for i in range(0, len(Data))]  # from 1V to 9V
AOM_curve = [round(Data[i][2], 3) for i in range(0, len(Data))]

# %% SCATTERED INTENSITY vs. DETUNING
""" Detuning plot obtained summing over pixel intensities and averaging over the number of 
experiment. Errors bars refer to the population distribution of different
experiments.
"""
if TRG_performed == "y":
    Bkg_Cam2_mx = Image_Matrix(
        ImageName="Cam2_0_0.bmp", folder_path=folder_path + "\\" + "Background"
    )
    Exp_mean_Cam2_list = []
    Exp_std_Cam2_list = []

    for j in range(0, 16, 1):
        Cam2_imgs = [
            (SubtractImgs(list_of_detunings[j][i]["Cam2"][0], Bkg_Cam2_mx.image))
            for i in range(number_of_experiments)
        ]
        Px_Cam2_list = [
            [
                Cam2_imgs[i][m, n]
                for m in range(0, Bkg_Cam2_mx.image.shape[0])
                for n in range(0, Bkg_Cam2_mx.image.shape[1])
            ]
            for i in range(number_of_experiments)
        ]
        Px_sum_Cam2_list = [
            sum(Px_Cam2_list[i]) / 1000 for i in range(number_of_experiments)
        ]
        Exp_mean_Cam2_list.append(np.mean(Px_sum_Cam2_list))
        Exp_std_Cam2_list.append(std_dev(Px_sum_Cam2_list))

    AOM_curve_reduced = [AOM_curve[i] for i in range(16, 32, 1)]
    detunings_reduced = [detunings[i] for i in range(16, 32, 1)]
    AOM_norm_Cam2_array = np.array(AOM_curve_reduced) * np.array(Exp_mean_Cam2_list)
    AOM_norm_Cam2_std_array = np.array(AOM_curve_reduced) * np.array(Exp_std_Cam2_list)

    fig = plt.figure()
    plt.subplot(121)
    plt.tight_layout()
    plt.title("Intensity Cam2")
    plt.xlabel("Detuning [V]")
    plt.errorbar(
        [i for i in np.arange(5, 9, 0.25)],
        Exp_mean_Cam2_list,
        fmt="o",
        yerr=Exp_std_Cam2_list,
        xerr=None,
    )
    plt.grid()
    plt.subplot(122)
    plt.tight_layout()
    plt.title("Intensity Cam2 Normalised")
    plt.xlabel("Detuning [V]")
    plt.errorbar(
        detunings_reduced,
        AOM_norm_Cam2_array,
        fmt="o",
        yerr=AOM_norm_Cam2_std_array,
        xerr=None,
    )
    plt.grid()
    plt.show(block=False)
    plt.savefig(folder_path + "\\" + "MOT_Detuning.pdf", format="pdf")

# %% Release Memory
if TRG == "y":
    del list_of_detunings, list_of_dictionaries, Cam2_imgs, Px_Cam2_list
    gc.collect()
