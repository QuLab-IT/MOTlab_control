# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 10:36:15 2019

@author: ruggero

Code that is used to run the experiment.
Controls AWGs, oscilloscopes and cameras.

"""

### Standard library imports
import time
import sys
from PIL import Image

### Third party imports
### Local application imports
from MultiResources import (
    AWGSession,
    CreateArbitraryWaveformVectorFromCSVFile,
    SelectWaveform,
)
from CameraResources import TransportLayerCreator, MultipleCameraSession


# %%  INITIALISATION VISA devices (AWGs, Oscilloscopes)
""" 
ALWAYS CHECK VOLTAGE LIMITS AND LOADS!!! 
NOTE: define a Mg just if it hasn't been created yet by another script!!!
NOTE: 
The AWG that has been selected as 'Captain' should be initialised as 'Captain'
and Captain_to_trigger should contain its name. 
There can be just one Captain.
The Captain CH_1 needs to be triggered during the experiment.
"""
# Mg = ResourceManagerCreator() ### Create Resource Manager
ExperimentDuration = 1.3  ### Experiment Duration in seconds.
number_of_experiments = 1  ### Number of experiments performed
AWGChannelsToBeUsed = ["AWG1_1", "AWG4_1", "AWG4_2"]
Captain_to_trigger = "AWG1"
Output_file = "y"  ### 'y' or 'n': if you want the cameras ouptu in a file
# -----------------------------------------------------------------------------
TRG_performed = "n"  ### Variable that controls if trigger has been performed ['n','y']
WaveformList = []
Headers = []
if "AWG1_1" in AWGChannelsToBeUsed or "AWG1_2" in AWGChannelsToBeUsed:
    if "AWG1" not in Mg.OpenedResourceNames:
        DS_AWG1 = AWGSession(Mg, "AWG1", "Captain")  ### DS: DeviceSession
if "AWG2_1" in AWGChannelsToBeUsed or "AWG2_2" in AWGChannelsToBeUsed:
    if "AWG2" not in Mg.OpenedResourceNames:
        DS_AWG2 = AWGSession(Mg, "AWG2")  ### DS: DeviceSession
if "AWG3_1" in AWGChannelsToBeUsed or "AWG3_2" in AWGChannelsToBeUsed:
    if "AWG3" not in Mg.OpenedResourceNames:
        DS_AWG3 = AWGSession(Mg, "AWG3")  ### DS: DeviceSession
if "AWG4_1" in AWGChannelsToBeUsed or "AWG4_2" in AWGChannelsToBeUsed:
    if "AWG4" not in Mg.OpenedResourceNames:
        DS_AWG4 = AWGSession(Mg, "AWG4")  ### DS: DeviceSession
if "AWG5_1" in AWGChannelsToBeUsed or "AWG5_2" in AWGChannelsToBeUsed:
    if "AWG5" not in Mg.OpenedResourceNames:
        DS_AWG5 = AWGSession(Mg, "AWG5")  ### DS: DeviceSession
Mg.WhoIsUp()
time.sleep(0.5)

# %%  INITIALISATION PYLON devices (Cameras)
""" All the Cameras are Opened. Just those in ListOfCamerasToBeTriggered
are triggered.
DO NOT open Pylon Viewer when the cameras are managed by PyPylon!
"""
CamNameToPicNum = {
    "Cam0": 3,
    "Cam1": 3,
    "Cam2": 3,
}
NumOfConnectedCameras = 3
ListOfCamerasToBeTriggered = ["Cam0", "Cam1", "Cam2"]
# -----------------------------------------------------------------------------
if ListOfCamerasToBeTriggered:
    TLF = TransportLayerCreator()  ### Create Transport Layer
    MCS = MultipleCameraSession(TLF, NumOfCamsConnected=NumOfConnectedCameras)
    time.sleep(0.5)

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
    "output/ProvaCSV.csv", RowNumber=10
)

if "AWG1_1" in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob["AWG1_1"]
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG1.AddArbitraryWaveformToChannelVolatileMemory(
        FunctionVector, AWGChannelNum="1", FuncName=FunctionName
    )
    # DS_AWG1.SetSyncOn('1', '300', 'NORM') ### Sync Output
    DS_AWG1.SetBurstOuputArbitraryWaveform(
        "INF",
        FuncName=FunctionName,
        AWGChannelNum="1",
        SampleRate="100",
        VHigh="5",
        VLow="0",
    )

if "AWG1_2" in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob["AWG1_2"]
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG1.AddArbitraryWaveformToChannelVolatileMemory(
        FunctionVector, AWGChannelNum="2", FuncName=FunctionName
    )
    DS_AWG1.SetBurstOuputArbitraryWaveform(
        "INF",
        FuncName=FunctionName,
        AWGChannelNum="2",
        SampleRate="100",
        VHigh="5",
        VLow="0",
    )

if "AWG2_1" in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob["AWG2_1"]
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG2.AddArbitraryWaveformToChannelVolatileMemory(
        FunctionVector, AWGChannelNum="1", FuncName=FunctionName
    )
    DS_AWG2.SetBurstOuputArbitraryWaveform(
        "INF",
        FuncName=FunctionName,
        AWGChannelNum="1",
        SampleRate="100",
        VHigh="5",
        VLow="0",
    )

if "AWG2_2" in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob["AWG2_2"]
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG2.AddArbitraryWaveformToChannelVolatileMemory(
        FunctionVector, AWGChannelNum="2", FuncName=FunctionName
    )
    DS_AWG2.SetBurstOuputArbitraryWaveform(
        "INF",
        FuncName=FunctionName,
        AWGChannelNum="2",
        SampleRate="100",
        VHigh="5",
        VLow="0",
    )

if "AWG3_1" in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob["AWG3_1"]
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG3.AddArbitraryWaveformToChannelVolatileMemory(
        FunctionVector, AWGChannelNum="1", FuncName=FunctionName
    )
    DS_AWG3.SetBurstOuputArbitraryWaveform(
        "INF",
        FuncName=FunctionName,
        AWGChannelNum="1",
        SampleRate="100",
        VHigh="5",
        VLow="0",
    )

if "AWG3_2" in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob["AWG3_2"]
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG3.AddArbitraryWaveformToChannelVolatileMemory(
        FunctionVector, AWGChannelNum="2", FuncName=FunctionName
    )
    DS_AWG3.SetBurstOuputArbitraryWaveform(
        "INF",
        FuncName=FunctionName,
        AWGChannelNum="2",
        SampleRate="100",
        VHigh="5",
        VLow="0",
    )

if "AWG4_1" in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob["AWG4_1"]
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG4.AddArbitraryWaveformToChannelVolatileMemory(
        FunctionVector, AWGChannelNum="1", FuncName=FunctionName
    )
    DS_AWG4.SetBurstOuputArbitraryWaveform(
        "INF",
        FuncName=FunctionName,
        AWGChannelNum="1",
        SampleRate="100",
        VHigh="5",
        VLow="0",
    )

if "AWG4_2" in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob["AWG4_2"]
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG4.AddArbitraryWaveformToChannelVolatileMemory(
        FunctionVector, AWGChannelNum="2", FuncName=FunctionName
    )
    DS_AWG4.SetBurstOuputArbitraryWaveform(
        "INF",
        FuncName=FunctionName,
        AWGChannelNum="2",
        SampleRate="100",
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
        SampleRate="100",
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
        SampleRate="100",
        VHigh="5",
        VLow="0",
    )

# %% AWG ERROR PRINTING
time.sleep(0.2)
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
time.sleep(0.2)

# %%% OUTPUT TO FILE
"""Choose the file name where you want to store the log of the experiment."""
if Output_file == "y":
    orig_stdout = sys.stdout
    print("\n Output to file")
    f = open(r"Output\output.txt", "w")
    sys.stdout = f

# %% PREPARE CAMERAS
try:
    if ListOfCamerasToBeTriggered:
        MCS.SetAllCamerasToDefaultConfiguration()

    if "Cam0" in ListOfCamerasToBeTriggered:
        MCS.Set_BurstTrigger("Cam0", "Off")
        MCS.Set_AcquisitionMode_FrameTrigger("Cam0", "On")
        MCS.Set_Gain_Exposure("Cam0", CamExposure=1000)
        MCS.Set_ROI(
            "Cam0", CamBinning=2, PixelWidth=56, PixelHeight=56, OffX=648, OffY=348
        )
        MCS.EnableTimeStamp("Cam0")

    if "Cam1" in ListOfCamerasToBeTriggered:
        MCS.Set_BurstTrigger("Cam1", "Off")
        MCS.Set_AcquisitionMode_FrameTrigger("Cam1", "On")
        MCS.Set_Gain_Exposure("Cam1", CamExposure=2000)
        MCS.Set_ROI(
            "Cam1", CamBinning=2, PixelWidth=72, PixelHeight=72, OffX=522, OffY=280
        )
        MCS.EnableTimeStamp("Cam1")

    if "Cam2" in ListOfCamerasToBeTriggered:
        MCS.Set_BurstTrigger("Cam2", "Off")
        MCS.Set_AcquisitionMode_FrameTrigger("Cam2", "On")
        MCS.Set_Gain_Exposure("Cam2", CamExposure=1000)
        MCS.Set_ROI(
            "Cam2", CamBinning=2, PixelWidth=56, PixelHeight=56, OffX=598, OffY=364
        )
        MCS.EnableTimeStamp("Cam2")
except Exception as excep:
    if Output_file == "y":
        sys.stdout = orig_stdout
        f.close()
        print("\n Output to console \n")
    print(excep)
    print(" \n !!! Something went wrong!")

time.sleep(0.2)

# %% TRIGGER EXPERIMENT
TRG = input("Do you want to trigger (y/n)? ")
if TRG == "y":
    try:
        list_of_dictionaries = (
            []
        )  ### Each element is a dictionary. The list length is the number of experiments.
        for i in range(number_of_experiments):
            print("Experiment", i)
            if ListOfCamerasToBeTriggered:
                MCS.ReadyForTrigger(
                    CamNameToPicNum, ListOfCamerasToBeTriggered
                )  ### Cameras Ready for trigger
            time.sleep(0.2)
            eval("DS_%s.Trigger()" % Captain_to_trigger)
            time.sleep(ExperimentDuration)  ### Wait for the experiment to end
            if ListOfCamerasToBeTriggered:
                MCS.RetrievePictures(
                    CamNameToPicNum, ListOfCamerasToBeTriggered
                )  ### Retrieve Pictures form Buffer
                list_of_dictionaries.append(MCS.CamNameToImageList)
            print(
                "The experiment has been allowed to run for ",
                ExperimentDuration,
                " seconds.",
                sep="",
            )
            print("Experiment concluded.", "\n")
            TRG_performed = "y"
    except Exception as excep:
        if Output_file == "y":
            sys.stdout = orig_stdout
            f.close()
            print("\n Output to console \n")
        print(excep)
        print("\n !!! Something went wrong!")
else:
    print("As requested, trigger hasn't been performed", "\n")
time.sleep(0.2)

# %% OUTPUT TO STANDARD OUTPUT
if Output_file == "y":
    if sys.stdout != orig_stdout:
        sys.stdout = orig_stdout
        f.close()
        print("\n Output to console \n")
    if TRG_performed == "y":
        print("Experiment concluded.", "\n")

# %% SHOW PICTURES
"""
camera = 'Cam2'
for j in  range(number_of_experiments): 
    for i in range(len(list_of_dictionaries[j][camera])):
        plt.figure()
        plt.gray()
        plt.imshow(list_of_dictionaries[j][camera][i])
"""

# %% SAVE PICTURE TO FILE
if TRG_performed == "y":
    for j in range(number_of_experiments):
        for i in ListOfCamerasToBeTriggered:
            for k in range(CamNameToPicNum[i]):
                im = Image.fromarray(list_of_dictionaries[j][i][k])
                img_name_tosave = (
                    r"C:\Users\MOT_User\Documents\MOT\QuantumLabPython\ExperimentMOT\Output\exp_pictures"
                    + "\\"
                    + i
                    + "_"
                    + str(j)
                    + "_"
                    + str(k)
                    + ".bmp"
                )
                im.save(img_name_tosave)

# %% CLOSE DEVICES AND GO BACK TO NORMAL CONFIGURATION

if "AWG1" in Mg.OpenedResourceNames:
    DS_AWG1.Clear()
    DS_AWG1.ApplyDCVoltage(Load="1000", AWGChannelNum="1", Volt="1")
    DS_AWG1.ApplyDCVoltage(Load="1000", AWGChannelNum="2", Volt="3.7")
if "AWG2" in Mg.OpenedResourceNames:
    DS_AWG2.Clear()
    DS_AWG2.ApplyDCVoltage(Load="1000", AWGChannelNum="1", Volt="5")
    DS_AWG2.ApplyDCVoltage(Load="1000", AWGChannelNum="2", Volt="6")
if "AWG3" in Mg.OpenedResourceNames:
    DS_AWG3.Clear()
    DS_AWG3.ApplyDCVoltage(Load="1000", AWGChannelNum="1", Volt="3")
    DS_AWG3.ApplyDCVoltage(Load="1000", AWGChannelNum="2", Volt="0")
if "AWG4" in Mg.OpenedResourceNames:
    DS_AWG4.Clear()
    DS_AWG4.ApplyDCVoltage(Load="50", AWGChannelNum="1", Volt="0")
    DS_AWG4.ApplyDCVoltage(Load="1000", AWGChannelNum="2", Volt="8")
if "AWG5" in Mg.OpenedResourceNames:
    DS_AWG5.Clear()
    DS_AWG5.ApplyDCVoltage(Load="INF", AWGChannelNum="1", Volt="5")
    DS_AWG5.ApplyDCVoltage(Load="INF", AWGChannelNum="2", Volt="0")

"""
### OUTPUTS do not get to 0 at the end of the arb waveform.
if 'AWG1' in Mg.OpenedResourceNames: DS_AWG1.OffAndCloseAWG(Mg)
if 'AWG2' in Mg.OpenedResourceNames: DS_AWG2.OffAndCloseAWG(Mg)
if 'AWG3' in Mg.OpenedResourceNames: DS_AWG3.OffAndCloseAWG(Mg)
if 'AWG4' in Mg.OpenedResourceNames: DS_AWG4.OffAndCloseAWG(Mg)
if 'AWG5' in Mg.OpenedResourceNames: DS_AWG5.OffAndCloseAWG(Mg)

Mg.WhoIsUp()
if Mg.OpenedResources == 0: Mg.CloseResourceManager()  
"""

if ListOfCamerasToBeTriggered:
    MCS.SetAllCamerasToDefaultConfiguration()
    MCS.CloseAllCameras()  ###Always close the cameras!
