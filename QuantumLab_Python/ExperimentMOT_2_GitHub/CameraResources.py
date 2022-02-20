# -*- coding: utf-8 -*-
"""
Created on Tue May 28 14:47:48 2019

@author: ruggero
"""

from pypylon import pylon
from pypylon import genicam
import numpy
import time
import sys

### All the method input parameters are meant to be passed in string format unless differently specified. 
### 'Name' variables are always strings.
### Descriptions of function and classes are also accessible through docstrings.

class TransportLayerCreator():
    ''' Gets the transport layer factory. '''
    def __init__(self):
        self.tlFactory = pylon.TlFactory.GetInstance()
        ### Get all attached devices and exit application if no device is found.
        self.devices = self.tlFactory.EnumerateDevices()
        if len(self.devices) == 0:
            raise pylon.RUNTIME_EXCEPTION("No camera present.")
        #print('available devices: ', devices)
        print('Camera devices found:', len(self.devices))
    
class MultipleCameraSession():
    ''' Gets the cameras ready and allows to define all the necessary 
    parameters to trigger those cameras.
    '''
    def __init__(self, TLCrt, NumOfCamsConnected):
        ### TLCrt is an instance of TransportLayerCreator.
        ### NumOfCamsConnected is a integer that represents the number of connected cameras.
        self.cam_number = NumOfCamsConnected
        self.SerialNumToName = {
                ### insert the serial number of you camera. 
                '12345670' : 'Cam0',
                '12345671' : 'Cam1',
                '12345672' : 'Cam2', 
                }
        self.NameToObject = {}  ### From camera name to 'camera' object.
        self.CameraSerialNumber = []
        self.cameras = pylon.InstantCameraArray(self.cam_number)
        ### Create and attach all Pylon Devices.
        print('Attaching devices to cameras and opening them: ')
        for i, CamObj in enumerate(self.cameras): ### Enumerate is a python function. CamObj is a 'camera' object.
            CamObj.Attach(TLCrt.tlFactory.CreateDevice(TLCrt.devices[i]))
            CameraInfo = CamObj.GetDeviceInfo().GetPropertyValue('SerialNumber')
            #print('camera info: ' + CameraInfo[1])
            ### You do not know in which order cameras are attached. So you need to create the list CameraSerialNumber.
            self.CameraSerialNumber.append(CameraInfo[1])            
            if self.CameraSerialNumber[i] in self.SerialNumToName: 
                print("SerialNumber", self.CameraSerialNumber[i], self.SerialNumToName [self.CameraSerialNumber[i]])
                ### Disable pylon's default configuration handler which otherwise would configure
                ### the camera back to not using an external trigger.
                CamObj.RegisterConfiguration(pylon.ConfigurationEventHandler(), pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_Delete) 
                ### Register an image event handler that accesses the chunk data.
                CamObj.RegisterImageEventHandler(pylon.ImageEventHandler(), pylon.RegistrationMode_Append, pylon.Cleanup_Delete)
                CamObj.Open()  ### !!! this should be after registering camera configuration.
                self.NameToObject[self.SerialNumToName[self.CameraSerialNumber[i]]] = CamObj
            else:
                print('The device is not one of your cameras')
        print('\n')
            
    def CloseAllCameras(self):
        ''' Close all cameras. '''
        for i in range(0, self.cam_number):  
            print("Closing", self.SerialNumToName[self.CameraSerialNumber[i]] )
            self.cameras[i].Close()
        self.cameras.DetachDevice()
        if self.cameras.IsPylonDeviceAttached() == False: print('All cameras have been closed and detached \n')
        if self.cameras.IsPylonDeviceAttached() == True: print('Cameras closed but not detached \n')
        
    def SetAllCamerasToDefaultConfiguration(self):
        for i in range(0, self.cam_number):  
            self.cameras[i].UserSetSelector.SetValue('Default');
            self.cameras[i].UserSetLoad.Execute()
            
    def Set_BurstTrigger(self, CameraName, Status, TrgActivation = 'FallingEdge', TrgDelay = 0):
        ''' Set Burst trigger preferences. '''
        ### Keep it off when using ReadyForTrigger()
        cam = self.NameToObject[CameraName]
        cam.TriggerSelector.SetValue('FrameBurstStart')
        cam.TriggerSource.SetValue('Line3') ### We are using line 3 (pins 1,6).
        cam.TriggerActivation.SetValue(TrgActivation) ### 'RisingEdge' or 'FallingEdge'.
        cam.TriggerDelay.SetValue(TrgDelay) ### Trigger delay in us.
        cam.TriggerMode.SetValue(Status) ### 'Status': 'On' or 'Off'.
        print(CameraName + ' Burst trigger:')
        print('Trigger Selector =', cam.TriggerSelector.GetValue(), '/ Trigger Mode =', cam.TriggerMode.GetValue())
        print('Trigger Source =', cam.TriggerSource.GetValue(), '/ Trigger Activation =', cam.TriggerActivation.GetValue(), '/ Trigger Delay =', str(cam.TriggerDelay.GetValue()), '\n')

    def Set_AcquisitionMode_FrameTrigger(self, CameraName, Status, TrgActivation = 'FallingEdge', TrgDelay = 0):
        ''' Set acquisition Mode, Frame trigger preferences. '''
        ### CameraName is a string. It is interpreted by the NameToObject dictionary 
        ### according to the names in SerialNumToName.
        cam = self.NameToObject[CameraName]
        cam.AcquisitionMode.SetValue('Continuous') ### Necessary to accumulate more than one picture 
        ### in the computer buffer before the application retrieve them and make them available to the user.
        ### Frame trigger enabled. pag 114 basler user USB 3.0 manual.
        cam.TriggerSelector.SetValue('FrameStart') ### 'FrameStart' or 'FrameBurstStart'.
        cam.TriggerSource.SetValue('Line3') ### We are using line 3 (pins 1,6).
        cam.TriggerActivation.SetValue(TrgActivation) ### 'RisingEdge' or 'FallingEdge'.
        cam.TriggerDelay.SetValue(TrgDelay) ### Trigger delay in us.
        cam.TriggerMode.SetValue(Status) ### 'Status': 'On' or 'Off'. If 'Off': FreeRun Mode
        print(CameraName + ' Acquisition Mode and Frame trigger:')
        print('Acquisition Mode =', cam.AcquisitionMode.GetValue())
        print('Trigger Selector =', cam.TriggerSelector.GetValue(), '/ Trigger Mode =', cam.TriggerMode.GetValue())
        print('Trigger Source =', cam.TriggerSource.GetValue(), '/ Trigger Activation =', cam.TriggerActivation.GetValue(), '/ Trigger Delay =', str(cam.TriggerDelay.GetValue()), '\n')
    
    def Set_ROI(self, CameraName, CamBinning = 1, PixelWidth = 2048, PixelHeight = 2048, OffX = 0, OffY = 0):
        ''' Set Region Of Interest. PixelWidth must be divisible by 8 (Note Pixel Heigth).
        Pixel Heigth affects Frame Rate Significantly.
        When binning, every pixel quantity has to be divided by two.'''
        cam = self.NameToObject[CameraName]
        ### Zero offset is in the cornet top-left.
        cam.BinningHorizontal.SetValue(CamBinning)
        cam.BinningVertical.SetValue(CamBinning)
        cam.Width.SetValue(PixelWidth)
        cam.Height.SetValue(PixelHeight)
        cam.OffsetX.SetValue(OffX)
        cam.OffsetY.SetValue(OffY)
        print(CameraName + ' ROI:')
        print('Width =', cam.Width.GetValue(), '/ Height =', cam.Height.GetValue(), '/ OffX =', cam.OffsetX.GetValue(), '/ OffY =', cam.OffsetY.GetValue())
        print('Cam Binning Horizontal  =',  cam.BinningHorizontal.GetValue(), '. Cam Binning Vertical =', cam.BinningVertical.GetValue() )
        print('Pixel Format = ' + cam.PixelFormat.GetValue()) ### The less bits the faster.
        print('Sensor readout time [us] =', cam.SensorReadoutTime.GetValue(), '\n')
    
    def Set_Gain_Exposure(self, CameraName, CamGain = 0, CamExposure = 10000):
        ''' Exposure time and Gain. '''
        cam = self.NameToObject[CameraName]
        cam.Gain.SetValue(CamGain)
        cam.ExposureMode.SetValue('Timed') ### 'Timed' or 'TriggerWidth'.
        cam.ExposureTime.SetValue(CamExposure) ### Exposure Time in us.
        print(CameraName + ' Gain and Exposure:')
        print('Gain =', cam.Gain.GetValue(), '/ Exposure Mode =', cam.ExposureMode.GetValue(), '/ Exposure time [us] =', cam.ExposureTime.GetValue(), '\n')        
        
    def EnableTimeStamp(self, CameraName):
        ''' Enable Time Stamp. Good to check the order of captured pictures.
        '''
        cam = self.NameToObject[CameraName]
            ### Enable chunks in general.
        if genicam.IsWritable(cam.ChunkModeActive):
            cam.ChunkModeActive = True
        else:
            raise pylon.RUNTIME_EXCEPTION("The camera doesn't support chunk features")
        cam.ChunkSelector.SetValue('Timestamp')
        #cam.ChunkEnable.SetValue('true')
        cam.ChunkEnable.SetValue(True)
        print(CameraName, ' ', cam.ChunkSelector.GetValue(), ': ', cam.ChunkEnable.GetValue(), '\n', sep = '')        
    
    def ReadyForTrigger(self, CamNameToPicNum, ListOfCamToBeTriggered):
        ''' Set Cameras ready for trigger. 
        Overlapped exposure depend just on the trigger timing, 
        it is not a parameter of the camera.
        FreeRunMode: set Burst trigger 'On' and Frame trigger 'Off'. # of picture defined in AcquisitionBurstFrameCount (max = 255)
        FreeRunMode software trigger: set Burst trigger 'Off' and Frame trigger 'Off'.
        Trigger image after image: set Frame trigger 'On'.
        '''
        ### CamNameToPicNum is a dictionary with the number of pictures to be acquired
        ### for each camera specified as integers.
        ### ListOfCamToBeTriggered is list with the cameras you want to use to take pictures.
        cam_list = ListOfCamToBeTriggered
        cam_to_pic = CamNameToPicNum
        self.CamNameToImageList = {} ### Dict that contains the images: for each camera provides a list of arrray (imgs).
        for cam_name in cam_list:
            cam = self.NameToObject[cam_name] ### cam is now a 'camera' object.
            cam.MaxNumBuffer = cam_to_pic[cam_name] + 2
            #cam.AcquisitionBurstFrameCount.SetValue(cam_to_pic[cam_name]) 
            cam.StartGrabbingMax(cam_to_pic[cam_name])            
        print(*cam_list, 'waiting for trigger', '\n')
        ### StartGrabbingMax() talks with the RetrieveResult() of each camera. 
        ### RetrieveResult automatically stop the grabbing 
        ### when the max number of pictures have been reached.
                
    def RetrievePictures(self, CamNameToPicNum, ListOfCamToBeTriggered):
        ''' Retrieve the pictures available in the buffer. 
        Pictures are available in the buffer after ReadyForTrigger() has been 
        called and trigger are performed.
        '''
        cam_list = ListOfCamToBeTriggered
        cam_to_pic = CamNameToPicNum
        self.CamNameToImageList = {} ### Dict that contains the images: for each camera provides a list of arrray (imgs).
        for cam_name in cam_list:
            cam = self.NameToObject[cam_name] ### cam is now a 'camera' object.
            self.CamNameToImageList[cam_name] = [] ### Prepare the dictionary that contains the image list for each camera.
            for Imagenum in range(0, cam_to_pic[cam_name]):
                grabResult = cam.RetrieveResult(50000, pylon.TimeoutHandling_ThrowException) ### Timeout of 50000 ms. 
                if grabResult.GrabSucceeded():   
                    img = grabResult.Array
                    cam.ChunkSelector.SetValue('Timestamp')
                    if cam.ChunkEnable.GetValue():
                        if genicam.IsReadable(grabResult.ChunkTimestamp):                
                            if Imagenum == 0: 
                                last_timestamp = grabResult.ChunkTimestamp.Value
                                time_elapsed_us = 0
                            else:
                                time_elapsed_us = int((grabResult.ChunkTimestamp.Value - last_timestamp)/1000)  
                                last_timestamp = grabResult.ChunkTimestamp.Value
                            print('Picture number ', Imagenum, ', ', cam_name, '. Max Intensity: ', numpy.amax(img), '. us since last picture: ', time_elapsed_us,  sep = '')
                    else:
                        print('Picture number ', Imagenum, ', ', cam_name, '. Max Intensity: ', numpy.amax(img), sep = '')
                    self.CamNameToImageList[cam_name].append(img) 
                else:
                    print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
                    grabResult.Release()           
            print('Images acquired ', cam_name, ': ', len(self.CamNameToImageList[cam_name]), '/', cam_to_pic[cam_name], '\n', sep = '')
            
              

        
                
    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
    