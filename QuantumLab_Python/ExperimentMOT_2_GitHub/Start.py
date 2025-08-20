# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 10:36:15 2019

@author: ruggero

Code that is used to run the experiment.
Controls AWGs, oscilloscopes and cameras.

"""

import os
import sys
import time

### Standard library imports
import matplotlib.pyplot as plt
from AnalysysBMP_Exp import Image_Matrix
from CameraResources import MultipleCameraSession, TransportLayerCreator
from Modify_csv_with_python import ModifyCSV

### Local application imports
from MultiResources import (
    AWGSession,
    CreateArbitraryWaveformVectorFromCSVFile,
    ResourceManagerCreator,
    SelectWaveform,
)
from PIL import Image

# %% INITIALISATION   ### DS: DeviceSession.
Mg = ResourceManagerCreator()  ### Create Manager.

DS_AWG1 = AWGSession(Mg, "AWG1", "Captain")
DS_AWG2 = AWGSession(Mg, "AWG2")
DS_AWG3 = AWGSession(Mg, "AWG3")
DS_AWG4 = AWGSession(Mg, "AWG4")
DS_AWG5 = AWGSession(Mg, "AWG5")

"""
DS_AWG1 = AWGSession(Mg, 'AWG1')   
DS_AWG2 = AWGSession(Mg, 'AWG2')
DS_AWG3 = AWGSession(Mg, 'AWG3')
DS_AWG4 = AWGSession(Mg, 'AWG4')
DS_AWG5 = AWGSession(Mg, 'AWG5')

DS_AWG1 = AWGSession(Mg, 'AWG1', 'Captain')    
DS_AWG2 = AWGSession(Mg, 'AWG2', 'Captain') 
DS_AWG3 = AWGSession(Mg, 'AWG3', 'Captain') 
DS_AWG4 = AWGSession(Mg, 'AWG4', 'Captain') 
DS_AWG5 = AWGSession(Mg, 'AWG5', 'Captain')                 
"""


# %% Function
def AWGSafeConfiguration():
    if "AWG1" in Mg.OpenedResourceNames:
        DS_AWG1.ApplyDCVoltage(Load="1000", AWGChannelNum="1", Volt="1")
        DS_AWG1.ApplyDCVoltage(Load="1000", AWGChannelNum="2", Volt="4")
    if "AWG2" in Mg.OpenedResourceNames:
        DS_AWG2.ApplyDCVoltage(Load="1000", AWGChannelNum="1", Volt="5")
        DS_AWG2.ApplyDCVoltage(Load="1000", AWGChannelNum="2", Volt="5")
    if "AWG3" in Mg.OpenedResourceNames:
        DS_AWG3.ApplyDCVoltage(Load="1000", AWGChannelNum="1", Volt="6.25")
        DS_AWG3.ApplyDCVoltage(Load="1000", AWGChannelNum="2", Volt="9")
    if "AWG4" in Mg.OpenedResourceNames:
        DS_AWG4.ApplyDCVoltage(Load="50", AWGChannelNum="1", Volt="0")
        DS_AWG4.ApplyDCVoltage(Load="1000", AWGChannelNum="2", Volt="7.75")
    if "AWG5" in Mg.OpenedResourceNames:
        DS_AWG5.ApplyDCVoltage(Load="INF", AWGChannelNum="1", Volt="0")
        DS_AWG5.ApplyDCVoltage(Load="INF", AWGChannelNum="2", Volt="0")
    return None


def AWGBaseConfiguration():
    ### used at the beginning of every experiment
    if "AWG1" in Mg.OpenedResourceNames:
        DS_AWG1.Clear()
        DS_AWG1.ApplyDCVoltage(Load="1000", AWGChannelNum="1", Volt="1")
        DS_AWG1.ApplyDCVoltage(Load="1000", AWGChannelNum="2", Volt="4")
    if "AWG2" in Mg.OpenedResourceNames:
        DS_AWG2.Clear()
        DS_AWG2.ApplyDCVoltage(Load="1000", AWGChannelNum="1", Volt="5")
        DS_AWG2.ApplyDCVoltage(Load="1000", AWGChannelNum="2", Volt="5")
    if "AWG3" in Mg.OpenedResourceNames:
        DS_AWG3.Clear()
        DS_AWG3.ApplyDCVoltage(Load="1000", AWGChannelNum="1", Volt="6.25")
        DS_AWG3.ApplyDCVoltage(Load="1000", AWGChannelNum="2", Volt="9")
    if "AWG4" in Mg.OpenedResourceNames:
        DS_AWG4.Clear()
        DS_AWG4.ApplyDCVoltage(Load="50", AWGChannelNum="1", Volt="0")
        DS_AWG4.ApplyDCVoltage(Load="1000", AWGChannelNum="2", Volt="7.75")
    if "AWG5" in Mg.OpenedResourceNames:
        DS_AWG5.Clear()
        DS_AWG5.ApplyDCVoltage(Load="INF", AWGChannelNum="1", Volt="5")
        DS_AWG5.ApplyDCVoltage(Load="INF", AWGChannelNum="2", Volt="0")
    return None


def No_MOT():
    if "AWG1" in Mg.OpenedResourceNames:
        DS_AWG1.ApplyDCVoltage(Load="1000", AWGChannelNum="1", Volt="9")
    if "AWG2" in Mg.OpenedResourceNames:
        DS_AWG2.ApplyDCVoltage(Load="1000", AWGChannelNum="1", Volt="0")
    if "AWG5" in Mg.OpenedResourceNames:
        DS_AWG5.ApplyDCVoltage(Load="INF", AWGChannelNum="1", Volt="0")
    return None


def ClearAllVolatiles():
    if "AWG1" in Mg.OpenedResourceNames:
        DS_AWG1.ClearVolatileMemory("1")
        DS_AWG1.ClearVolatileMemory("2")
    if "AWG2" in Mg.OpenedResourceNames:
        DS_AWG2.ClearVolatileMemory("1")
        DS_AWG2.ClearVolatileMemory("2")
    if "AWG3" in Mg.OpenedResourceNames:
        DS_AWG3.ClearVolatileMemory("1")
        DS_AWG3.ClearVolatileMemory("2")
    if "AWG4" in Mg.OpenedResourceNames:
        DS_AWG4.ClearVolatileMemory("1")
        DS_AWG4.ClearVolatileMemory("2")
    if "AWG5" in Mg.OpenedResourceNames:
        DS_AWG5.ClearVolatileMemory("1")
        DS_AWG5.ClearVolatileMemory("2")
    return None


def CloseEverythingSafely():
    if "AWG1" in Mg.OpenedResourceNames:
        DS_AWG1.OffAndCloseAWG(Mg)
    if "AWG2" in Mg.OpenedResourceNames:
        DS_AWG2.OffAndCloseAWG(Mg)
    if "AWG3" in Mg.OpenedResourceNames:
        DS_AWG3.OffAndCloseAWG(Mg)
    if "AWG4" in Mg.OpenedResourceNames:
        DS_AWG4.OffAndCloseAWG(Mg)
    if "AWG5" in Mg.OpenedResourceNames:
        DS_AWG5.OffAndCloseAWG(Mg)
    Mg.WhoIsUp()
    if Mg.OpenedResources == 0:
        Mg.CloseResourceManager()
    return None


def Background_capture(MeasType, Camera, Exposure, folder_path):
    """
    NOTE: check that the camera configuration corresponds to the one in the
    script used to call this function.
    Assumes Resource Manager alredy created and resources already opened.
    Detunings have to be chosen beforehand, in the main script.
    Exposure is a int (us exposure).
    MeasType = ['Scattering', 'Pump', 'Probe'].
    If exposure is less than 50 us, camera exposure time is set to 50. All the rest is
    changed to the requested exposure time.
    """
    if Exposure <= 50:
        exp_cam = 50
    else:
        exp_cam = Exposure

    print("\n ... Acquiring Background", MeasType, Camera, "...")

    ### Create Directory
    dirName = "Background"
    if not os.path.exists(folder_path + "\\" + dirName):
        os.mkdir(folder_path + "\\" + dirName)
        print("Directory ", dirName, " Created ")
    else:
        print("Directory ", dirName, " already exists")

    ### INITIALISATION
    ExperimentDuration = 0.02  ### Experiment Duration in seconds.
    number_of_experiments = 1  ### Number of experiments performed
    MeasType_to_channel = {
        "Scattering": ["AWG1_1", "AWG2_1", "AWG5_2"],
        "Pump": ["AWG1_1", "AWG2_1", "AWG3_1", "AWG4_1", "AWG5_2"],
        "Probe": ["AWG1_1", "AWG2_1", "AWG3_2", "AWG5_2"],
    }
    AWGChannelsToBeUsed = MeasType_to_channel[MeasType]
    Captain_to_trigger = "AWG1"
    Output_file = "y"  ### 'y' or 'n': if you want the cameras output in a file
    TRG_performed = (
        "n"  ### Variable that controls if trigger has been performed ['n','y']
    )
    Status = "OK"
    WaveformList = []
    Headers = []
    if MeasType == "Scattering":
        CamNameToPicNum = {
            "Cam0": 1,
            "Cam1": 1,
            "Cam2": 1,
        }
    if MeasType == "Pump":
        CamNameToPicNum = {
            "Cam0": 0,
            "Cam1": 2,
            "Cam2": 0,
        }
    if MeasType == "Probe":
        CamNameToPicNum = {
            "Cam0": 2,
            "Cam1": 0,
            "Cam2": 0,
        }
    NumOfConnectedCameras = 3
    ListOfCamerasToBeTriggered = [Camera]
    TLF = TransportLayerCreator()  ### Create Transport Layer
    MCS = MultipleCameraSession(TLF, NumOfCamsConnected=NumOfConnectedCameras)

    """Choose the file name where you want to store the log of the experiment."""
    if Output_file == "y":
        orig_stdout = sys.stdout
        print("\n Output to file")
        Output_destination = folder_path + "\\" + "Background" + "\\" + "output.txt"
        f = open(Output_destination, "w")
        sys.stdout = f

    ### EXCEL MODIFICATION
    ### NOTE: 'Probe_2pass' of Probe has to be stated outside Background_capture, as well as 'AWG4_2' for the Pump
    if MeasType == "Scattering":
        ModifyCSV(
            FileName="output/Background.csv",
            device="MOT_switch",
            start=31,
            exposure=Exposure // 10,
            value=0.111,
        )
        ModifyCSV(
            FileName="output/Background.csv",
            device="Rep_switch",
            start=31,
            exposure=Exposure // 10,
            value=1,
        )
    if MeasType == "Pump":
        ModifyCSV(
            FileName="output/Background.csv",
            device="MOT_switch",
            start=31,
            exposure=Exposure // 10,
            value=1,
        )
        ModifyCSV(
            FileName="output/Background.csv",
            device="Rep_switch",
            start=31,
            exposure=Exposure // 10,
            value=0,
        )
        ModifyCSV(
            FileName="output/Background.csv",
            device="AWG4_1",
            start=1051,
            exposure=Exposure // 10,
            value=1,
        )
        ModifyCSV(
            FileName="output/Background.csv",
            device="Probe_2pass",
            start=1050,
            exposure=Exposure // 10 + 1,
            value=0.444,
        )
    if MeasType == "Probe":
        ModifyCSV(
            FileName="output/Background.csv",
            device="MOT_switch",
            start=31,
            exposure=Exposure // 10,
            value=1,
        )
        ModifyCSV(
            FileName="output/Background.csv",
            device="Rep_switch",
            start=31,
            exposure=Exposure // 10,
            value=0,
        )
        ModifyCSV(
            FileName="output/Background.csv",
            device="Probe_switch",
            start=1051,
            exposure=Exposure // 10,
            value=0.111,
        )

    ### PREPARATION
    WaveformList, Headers = CreateArbitraryWaveformVectorFromCSVFile(
        "output/Background.csv", RowNumber=10
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
    if "AWG3_2" in AWGChannelsToBeUsed:
        FunctionName = Mg.ResourceNameToJob["AWG3_1"]
        FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
        DS_AWG3.AddArbitraryWaveformToChannelVolatileMemory(
            FunctionVector, AWGChannelNum="1", FuncName=FunctionName
        )
        DS_AWG3.SetBurstOuputArbitraryWaveform(
            "1000",
            FuncName=FunctionName,
            AWGChannelNum="1",
            SampleRate="100000",
            VHigh="9",
            VLow="0",
        )
    if "AWG3_2" in AWGChannelsToBeUsed:
        FunctionName = Mg.ResourceNameToJob["AWG3_2"]
        FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
        DS_AWG3.AddArbitraryWaveformToChannelVolatileMemory(
            FunctionVector, AWGChannelNum="2", FuncName=FunctionName
        )
        DS_AWG3.SetBurstOuputArbitraryWaveform(
            "1000",
            FuncName=FunctionName,
            AWGChannelNum="2",
            SampleRate="100000",
            VHigh="9",
            VLow="0",
        )
    if "AWG4_1" in AWGChannelsToBeUsed:
        FunctionName = Mg.ResourceNameToJob["AWG4_1"]
        FunctionVector = SelectWaveform(Headers, WaveformList, FunctionName)
        DS_AWG4.AddArbitraryWaveformToChannelVolatileMemory(
            FunctionVector, AWGChannelNum="1", FuncName=FunctionName
        )
        DS_AWG4.SetBurstOuputArbitraryWaveform(
            "50",
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

    print("RESUME:")
    print("Background of " + MeasType + " " + Camera)
    print("AWG channels to be controlled in the experiment: ", AWGChannelsToBeUsed)
    print("Exposure [us]: ", Exposure)
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
    # TRG = input('Do you want to trigger the background (y/n)? ')
    print("\n")
    TRG = "y"
    time.sleep(0.1)

    try:
        if ListOfCamerasToBeTriggered:
            MCS.SetAllCamerasToDefaultConfiguration()
        if "Cam0" in ListOfCamerasToBeTriggered:
            MCS.Set_BurstTrigger("Cam0", "Off")
            MCS.Set_AcquisitionMode_FrameTrigger("Cam0", "On", TrgDelay=0)
            MCS.Set_Gain_Exposure("Cam0", CamGain=0, CamExposure=exp_cam)
            MCS.Set_ROI(
                "Cam0",
                CamBinning=1,
                PixelWidth=208,
                PixelHeight=208,
                OffX=920,
                OffY=880,
            )
            MCS.EnableTimeStamp("Cam0")
        if "Cam1" in ListOfCamerasToBeTriggered:
            MCS.Set_BurstTrigger("Cam1", "Off")
            MCS.Set_AcquisitionMode_FrameTrigger("Cam1", "On", TrgDelay=0)
            MCS.Set_Gain_Exposure("Cam1", CamGain=1, CamExposure=exp_cam)
            MCS.Set_ROI(
                "Cam1",
                CamBinning=1,
                PixelWidth=384,
                PixelHeight=384,
                OffX=870,
                OffY=800,
            )
            MCS.EnableTimeStamp("Cam1")
        if "Cam2" in ListOfCamerasToBeTriggered:
            MCS.Set_BurstTrigger("Cam2", "Off")
            MCS.Set_AcquisitionMode_FrameTrigger("Cam2", "On", TrgDelay=0)
            MCS.Set_Gain_Exposure("Cam2", CamGain=6, CamExposure=exp_cam)
            MCS.Set_ROI(
                "Cam2",
                CamBinning=1,
                PixelWidth=144,
                PixelHeight=144,
                OffX=1170,
                OffY=710,
            )
            MCS.EnableTimeStamp("Cam2")

    except Exception as excep:
        if Output_file == "y":
            sys.stdout = orig_stdout
            f.close()
            print("\n Output to console \n")
        print(" \n !!! Something went wrong with cameras! \n")
        print(excep)
        Status = "NOT_OK"
    time.sleep(0.1)

    ### TRIGGER
    if TRG == "y" and Status == "OK":
        try:
            list_of_dictionaries = (
                []
            )  ### Each element is a dictionary. The list length is the number of experiments.
            for i in range(number_of_experiments):
                print("Background of " + MeasType + " " + Camera)
                if ListOfCamerasToBeTriggered:
                    MCS.ReadyForTrigger(
                        CamNameToPicNum, ListOfCamerasToBeTriggered
                    )  ### Cameras Ready for trigger
                time.sleep(0.1)
                eval("DS_%s.Trigger()" % Captain_to_trigger)
                time.sleep(ExperimentDuration)  ### Wait for the experiment to end
                if ListOfCamerasToBeTriggered:
                    MCS.RetrievePictures(
                        CamNameToPicNum, ListOfCamerasToBeTriggered
                    )  ### Retrieve Pictures from Buffer
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
            print("\n !!! Something went wrong when triggering!")
            Status = "NOT_OK"
    else:
        Status = "NOT_OK"
        print("Trigger hasn't been performed", "\n")
    time.sleep(0.1)

    ### SAVE PICTURES TO FILE
    if TRG_performed == "y":
        for j in range(number_of_experiments):
            for i in ListOfCamerasToBeTriggered:
                for k in range(CamNameToPicNum[i]):
                    im = Image.fromarray(list_of_dictionaries[j][i][k])
                    img_name_tosave = (
                        folder_path
                        + "\\"
                        + "Background"
                        + "\\"
                        + i
                        + "_"
                        + str(j)
                        + "_"
                        + str(k)
                        + ".bmp"
                    )
                    im.save(img_name_tosave)

    ### OUTPUT TO STANDARD OUTPUT
    if Output_file == "y":
        if sys.stdout != orig_stdout:
            sys.stdout = orig_stdout
            f.close()
            print("\n Output to console \n")
        if TRG_performed == "y":
            print("Background acquired.", "\n")

    ### BASE CONFIGURATION (for switch signals)
    if MeasType == "Scattering":
        ModifyCSV(
            FileName="output/Background.csv",
            device="MOT_switch",
            start=31,
            exposure=Exposure // 10,
            value=1,
        )
        ModifyCSV(
            FileName="output/Background.csv",
            device="Rep_switch",
            start=31,
            exposure=Exposure // 10,
            value=0,
        )
    if MeasType == "Pump":
        ModifyCSV(
            FileName="output/Background.csv",
            device="AWG4_1",
            start=1051,
            exposure=Exposure // 10,
            value=0,
        )
    if MeasType == "Probe":
        ModifyCSV(
            FileName="output/Background.csv",
            device="Probe_switch",
            start=1051,
            exposure=Exposure // 10,
            value=1,
        )

    ### CLOSE CAMERAS
    if ListOfCamerasToBeTriggered:
        MCS.SetAllCamerasToDefaultConfiguration()
        MCS.CloseAllCameras()  ###Always close the cameras!

    ### SHOW PICTURES
    if TRG_performed == "y":
        if MeasType == "Probe":
            Bkg_probe_mx = Image_Matrix(
                ImageName=Camera + "_0_1.bmp",
                folder_path=folder_path + "\\" + "Background",
            )
            Bkg_probe_dark_mx = Image_Matrix(
                ImageName=Camera + "_0_0.bmp",
                folder_path=folder_path + "\\" + "Background",
            )
            plt.figure()
            plt.subplot(121)
            plt.tight_layout()
            plt.title("Probe Dark Backgroung, \n exposure: " + str(Exposure))
            plt.imshow(Bkg_probe_dark_mx.image, cmap="rainbow")
            plt.colorbar()
            plt.ylabel("row [pixel]")
            plt.xlabel("col [pixel]")
            plt.subplot(122)
            plt.tight_layout()
            plt.title("Probe Backgroung, \n exposure: " + str(Exposure))
            plt.imshow(Bkg_probe_mx.image, cmap="rainbow")
            plt.colorbar()
            plt.ylabel("row [pixel]")
            plt.xlabel("col [pixel]")

    if TRG_performed == "y":
        if MeasType == "Pump":
            Bkg_pump_mx = Image_Matrix(
                ImageName=Camera + "_0_1.bmp",
                folder_path=folder_path + "\\" + "Background",
            )
            Bkg_pump_dark_mx = Image_Matrix(
                ImageName=Camera + "_0_0.bmp",
                folder_path=folder_path + "\\" + "Background",
            )
            plt.figure()
            plt.subplot(121)
            plt.tight_layout()
            plt.title("Pump Dark Backgroung, \n exposure: " + str(Exposure))
            plt.imshow(Bkg_pump_dark_mx.image, cmap="rainbow")
            plt.colorbar()
            plt.ylabel("row [pixel]")
            plt.xlabel("col [pixel]")
            plt.subplot(122)
            plt.tight_layout()
            plt.title("Pump Backgroung, \n exposure: " + str(Exposure))
            plt.imshow(Bkg_pump_mx.image, cmap="rainbow")
            plt.colorbar()
            plt.ylabel("row [pixel]")
            plt.xlabel("col [pixel]")

    if Status == "OK":
        return "Y"
    else:
        return "N"


# %% TRIAL

# folder_path = r'C:\Users\MOT_User\Documents\MOT\QuantumLabPython\ExperimentMOT_special_2\Output' + '\\' + 'Pump_and_Probe'
# a = Background_capture(MeasType = 'Scattering', Camera = 'Cam2', Exposure = 200, folder_path = folder_path)

# folder_path = r'C:\Users\MOT_User\Documents\MOT\QuantumLabPython\ExperimentMOT_special_2\Output\Pump_detuning'
# Background_capture(MeasType = 'Probe', Camera = 'Cam0', Exposure = 150, folder_path = folder_path)
