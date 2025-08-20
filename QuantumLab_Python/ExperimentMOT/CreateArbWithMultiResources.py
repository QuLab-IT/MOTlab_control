# -*- coding: utf-8 -*-
"""
Created on Fri May 10 13:02:37 2019

@author: ruggero

Used to Create and Trigger Arbitrary Waveform with the AWGs.
For the MOT experiments use 'ExperimentMOT.py': this script
allows the user to set both AWGs and Cameras parameters and
to control them during the experiment.

ALWAYS CHECK VOLTAGE LIMITS AND LOADS!!!

"""

import time
from MultiResources import (
    ResourceManagerCreator,
    AWGSession,
    CreateArbitraryWaveformVectorFromCSVFile,
    SelectWaveform,
)

# %% INITIALISATION
""" Just those AWGs whose channels are in AWGChannelsToBeUsed are opened. """
ExperimentDuration = 15  ### Experiment Duration in seconds.
AWGChannelsToBeUsed = ["AWG1_1", "AWG1_2", "AWG2_1"]
# -----------------------------------------------------------------------------
WaveformList = []
Headers = []
Mg = ResourceManagerCreator()  ### Create Resource Manager
if ("AWG1_1" or "AWG1_2") in AWGChannelsToBeUsed:
    DS_AWG1 = AWGSession(Mg, "AWG1", "Captain")  ### DS: DeviceSession
if ("AWG2_1" or "AWG2_2") in AWGChannelsToBeUsed:
    DS_AWG2 = AWGSession(Mg, "AWG2")
Mg.WhoIsUp()
time.sleep(0.5)


# %% PREPARE AWGs' OUTPUTS
### Import arbitrary waveforms.
### The RowNumber indicates the number of different waveform you want to upload (columns in the .csv file).
### Headers are the name of the imported waveforms. Make sure that those names matches the 'value' names of
### the Mg.ResourceNameToJob[] for the correct device channel you want to switch on.
WaveformList, Headers = CreateArbitraryWaveformVectorFromCSVFile(
    "output/ProvaCSV.csv", RowNumber=4
)
time.sleep(1)

if "AWG1_1" in AWGChannelsToBeUsed:
    FunctionName = Mg.ResourceNameToJob["AWG1_1"]
    FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
    DS_AWG1.AddArbitraryWaveformToChannelVolatileMemory(
        FunctionVector, AWGChannelNum="1", FuncName=FunctionName
    )
    # DS_AWG1.SetSyncOn('1', '300', 'NORM') ### Sync Output
    DS_AWG1.SetBurstOuputArbitraryWaveform(
        "50",
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
        VHigh="2.5",
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
        VHigh="2",
        VLow="0",
    )

# %% TRIGGER (Not to be modified in common experiments, unless the 'Captain' has changed).

### AWG Error printing
if "AWG1" in Mg.OpenedResourceNames:
    DS_AWG1.PrintError()
if "AWG2" in Mg.OpenedResourceNames:
    DS_AWG2.PrintError()
time.sleep(0.5)

### Trigger AWG. Just the 'Captain' can be triggered;
### the others AWGs ('Gunners') are triggered by the 'Captain'.
TRG = input("Do you want to trigger (y/n)? ")
if TRG == "y":
    DS_AWG1.Trigger()
    time.sleep(ExperimentDuration)  ### Wait for the experiment to end
    print(
        "The experiment has been allowed to run for ",
        ExperimentDuration,
        " seconds.",
        sep="",
    )
    print("Experiment concluded.", "\n")
else:
    print("As requested, trigger hasn't been performed", "\n")
time.sleep(1)

# %% CLOSE DEVICES (Not to be modified in common experiments)

if "AWG1" in Mg.OpenedResourceNames:
    DS_AWG1.OffAndCloseAWG(Mg)
if "AWG2" in Mg.OpenedResourceNames:
    DS_AWG2.OffAndCloseAWG(Mg)

Mg.WhoIsUp()
if Mg.OpenedResources == 0:
    Mg.CloseResourceManager()
