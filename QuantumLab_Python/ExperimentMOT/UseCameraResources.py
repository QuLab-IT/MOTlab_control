# -*- coding: utf-8 -*-
"""
Created on Wed May 29 16:17:41 2019

@author: ruggero
"""

from CameraResources import TransportLayerCreator, MultipleCameraSession
import time

CamNameToPicNum = {
        'Cam0' : 0,
        'Cam1' : 3,
        'Cam2' : 3,
        }
ListOfCamerasToBeTriggered = ['Cam2']
NumOfConnectedCameras = 1

### After using the cameras close them and reset the variables (%reset). 
### DO NOT open Pylon Viewer when the cameras are on!

### Camera Initialisation.
TLF = TransportLayerCreator()
MCS = MultipleCameraSession(TLF, NumOfCamsConnected = NumOfConnectedCameras)
time.sleep(1)

### Setting Camera Parameteres.
MCS.Set_BurstTrigger('Cam2', 'Off')
MCS.Set_AcquisitionMode_FrameTrigger('Cam2', 'On')
MCS.Set_ROI('Cam2')
MCS.Set_Gain_Exposure('Cam2')
MCS.EnableTimeStamp('Cam2')

'''
MCS.Set_BurstTrigger('Cam1', 'On')
MCS.Set_AcquisitionMode_FrameTrigger('Cam1', 'Off')
MCS.Set_ROI('Cam1')
MCS.Set_Gain_Exposure('Cam1')
MCS.EnableTimeStamp('Cam1')
'''

### Acquisition.

time.sleep(1)
MCS.ReadyForTrigger(CamNameToPicNum, ListOfCamerasToBeTriggered)
time.sleep(1)
MCS.RetrievePictures(CamNameToPicNum, ListOfCamerasToBeTriggered)


### Display all the pictures of one camera.
'''
camera = 'Cam2'
for i in range(len(MCS.CamNameToImageList[camera])):
    plt.figure()
    plt.gray()
    plt.imshow(MCS.CamNameToImageList[camera][i])
'''

#MCS.CloseAllCameras()
#%reset











