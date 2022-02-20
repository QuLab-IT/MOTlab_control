# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 15:20:46 2019

@author: ruggero
"""

import numpy as np
#import visa (deprecated)
import pyvisa as visa
import csv
from struct import unpack

### All the method input parameters are meant to be passed in string format unless differently specified. 
### 'Name' variables are always strings.
### Descriptions of function and classes are also accessible through docstrings.

### GENERAL FUNCTIONS
def CreateArbitraryWaveformVectorFromCSVFile(FileName, RowNumber = 1):
    ''' Extract a list of waveforms which are meant to be passed to 
    AddArbitraryWaveformToChannelVolatileMemory() as FuncVect 
    FileName should be a string in the form 'Something.csv'. The first line of 
    the .csv file is considered as header.'RowNumber' is an integer 
    representing the number of waveforms you want to get from the .csv file.
    RULES:
    1) If you are using Excel to create the .csv alwayws save in CSV (MS-DOS).
    2) All the columns must have the same length
    3) Values in the arbitrary waveform have to be comprised in [0, 1]. 
    4) Values 0 and 1 should always be there.
    5) Before outputting the waveform, the AWG sets its output as the last value
    of the uploaded waveform and ouptput it.
    '''
    Data = []
    WaveVect = []
    WaveVectors = []
    Header = []
    with open(FileName, 'r') as file:
        for row in csv.reader(file):
            Data.append(row)
    Header = Data.pop(0)
    for j in range(RowNumber):
        WaveVect = [float(i[j]) for i in Data]
        WaveVectors.append(WaveVect)
    return WaveVectors, Header

def SelectWaveform(Headers, WaveVectors, VectName):
    ''' Select the waveform in Wavevectors corresponding to VectName Header.
    Wavevetors and Header are the ouputs of 
    CreateArbitraryWaveformVectorFromCSVFile().
    '''
    for i in range(len(Headers)):
        if Headers[i] == VectName: 
            return WaveVectors[i]
    print('No match found in Headers for ' + VectName)
         
### CLASSES
class ResourceManagerCreator():
    ''' Create ResourceManager. '''    
    def __init__(self):
        self.rm = visa.ResourceManager() ### self.rm is a ResourceManager
        self.resource_list = self.rm.list_resources()
        self.OpenedResources = 0
        self.OpenedResourceNames = []
        print("\n Available VISA Resources:")
        print(self.resource_list)
        print('\n')
        ### Resource Names internally defined in the code for the actual Identity string.
        ### If the 'key' has to be changed, change it even in the other dictionaries in this class.
        self.ResourceNameToResourceIdentityString = {
                ### insert the identity strings of your instruments
                'AWG1' : 'USB0::0x0957::0x2807::MY58000111::INSTR',
                'AWG2' : 'USB0::0x0957::0x2807::MY58000112::INSTR',
                'AWG3' : 'USB0::0x0957::0x2807::MY58000113::INSTR',
                'AWG4' : 'USB0::0x0957::0x2807::MY58000114::INSTR',
                'AWG5' : 'USB0::0x0957::0x2807::MY58000115::INSTR',
                'OSC_MDO3024' : 'USB0::0x0699::0x0408::C053116::INSTR',
                }  
        ### Used to translate AWG channels to the name of the device they are connected to ('job'). 
        ### the dictionary key is the AWG channel name. It is not supposed to be changed in different experiments.
        ### If the 'key' has to be changed, to be consistent change it even in ResourceNameToResourceIdentityString.
        ### Dictionary value' is the device name driven by the channel named in the corresponding 'key'.
        ### The name of the devices driven by the AWGs are the same of the columns 
        ### of the .csv file used to define arbitrary waveforms.
        ### If the dictionary value is the same of the dictionary key, the device is supposed  
        ### not to be connected to any device of the experiment. 
        self.ResourceNameToJob = {
                'AWG1_1' : 'MOT_switch',
                'AWG1_2' : 'MOT_2pass',
                'AWG2_1' : 'Rep_switch',
                'AWG2_2' : 'Rep_2pass',
                'AWG3_1' : 'Probe_2pass',
                'AWG3_2' : 'Probe_switch',
                'AWG4_1' : 'AWG4_1',
                'AWG4_2' : 'AWG4_2',
                'AWG5_1' : 'AWG5_1',
                'AWG5_2' : 'AWG5_2',
                }       
        
    def AddResourceToTheIndex(self, ResourceName):
        ''' Add an opened Resource to the list of open resources.
        It is called automatically by every Resource Session initialised.
        '''
        self.OpenedResources = self.OpenedResources + 1
        self.OpenedResourceNames.append(ResourceName)
    
    def RemoveResourceFromTheIndex(self, ResourceName):
        ''' Remove a closed Resource from the list of open resources.
        It is called automatically by CloseResource().
        '''
        self.OpenedResources = self.OpenedResources - 1
        self.OpenedResourceNames.remove(ResourceName)
        
    def WhoIsUp(self):
        ''' Finds out which resources are open looking into 
        OpenedResourceNames. 
        '''
        if self.OpenedResources != 0: 
            print('List of open resources: ')
            print(*self.OpenedResourceNames, sep = ", ")
            print('\n')
        else: print('There are no open resources', '\n')
        
    def CloseResourceManager(self):
        ''' Close Resource Manager. '''
        self.rm.close()
        print('Resource Manager Session closed', '\n')
            
class ResourceSession():
    ''' Add Resource (instrument) session. '''  
    def __init__(self, ResMgCrt, ResourceName):
        ### ResMgCrt is an instance (object) of ResourceManagerCreator. ResourceName has to be chosen
        ### among those in the ResourceNameToResourceIdentityString dictionary of ResourceManagerCreator().
        ### If the item doesn't exist yet, add it.
        self.resource = ResMgCrt.rm.open_resource(resource_name=ResMgCrt.ResourceNameToResourceIdentityString[ResourceName]) ### self.resource is a resource
        self.resource.timeout = 10000
        ### all the attributes or method of self.resource are derived from ResMgCrt.rm.open_resource() from PyVisa
        ### DO NOT add any attribute or method to this class
        self.session_number = str(self.resource.session)
        self.resource_identity_string = ResMgCrt.ResourceNameToResourceIdentityString[ResourceName]
        self.resource_name = ResourceName
        ResMgCrt.AddResourceToTheIndex(self.resource_name)
        print(' Open Resource')
        print('Resource ' + self.resource_identity_string + ' / session number: ' + self.session_number)
        print('Resource name:', self.resource_name)
        
      
    def CloseResource(self, ResMgCrt):
        ''' Close Resource session.  '''
        self.resource.close()
        print('Closing Resource: ', self.resource_name)
        ResMgCrt.RemoveResourceFromTheIndex(self.resource_name)
                  
class OscilloscopeSession(ResourceSession):
    ''' Add Oscilloscope session inheriting from ResourceSession. '''
    def __init__(self, ResMgCrt, ResourceName):
        ResourceSession.__init__(self, ResMgCrt, ResourceName)
        
    def SetResourceChannel(self, OscChannelNum):
        ''' Address the channel you wanna communicate with and initialise it. '''
        ### PAG 126 Programmer Manual
        channel_name = 'CH' + OscChannelNum
        print('Comunicating with channel ' + channel_name + ' of ' + self.resource_identity_string)
        self.resource.write('DAT:SOU ' + channel_name)
        self.resource.write('DAT:WIDTH 1') ### 1 byte per point
        self.resource.write('DAT:ENC RPB')  ### Sets the encoding. RPB, ASCI, ...
    
    def StartAcquiring(self):
        ''' Star acquisition. '''
        #print('Aquiring Parameters: ' + str(self.resource.query('ACQ?')))
        self.resource.write('ACQ:STATE ON')
        print('Acquiring State ' + self.resource_name + ': ' +  self.resource.query('ACQ:STATE?'))
        
    def StopAcquiring(self):
        ''' Stop Acquisition. '''
        #print('Aquiring Parameters: ' + str(self.resource.query('ACQ?')))
        self.resource.write('ACQ:STATE OFF')
        print('Acquiring State ' + self.resource_name + ': ' + self.resource.query('ACQ:STATE?'))
        
    def AutoSet(self):
        ''' Autoset. '''
        self.resource.write('AUTO')
        print('Autoset ' + self.resource_name)
         
    def read_data_single_channel(self, RecordLength = 10000): 
        ''' Read Data from a dingle channel. '''
        ### Set some parameters
        #self.resource.write('HORizontal:RECOrdlength '+ str(RecordLength))         
        ### Get some parameters from the resource
        self.ymult = float(self.resource.query('WFMOutpre:YMUlt?')) #waveform vertical scale factor
        self.yzero = float(self.resource.query('WFMOutpre:YZERO?')) #waveform vertical zero
        self.yoff = float(self.resource.query('WFMOutpre:YOFf?')) #waveform vertical position
        self.xincr = float(self.resource.query('WFMOutpre:XINC?')) #waveform horizontal sampling interval    
        ### Grabs data from scope
        self.resource.write('CURVE?')  ### It is a query basically: write + read_raw
        data = self.resource.read_raw()
        headerlen = 2 + int(data[1])
        #header = data[:headerlen] #
        ADC_wave = data[headerlen:-1]
        ADC_wave = np.array(unpack('%sB' % len(ADC_wave),ADC_wave))        
        ### creates the voltage and time values
        voltage_axis = (ADC_wave - self.yoff) * self.ymult  + self.yzero
        time_axis = np.arange(0, self.xincr * len(voltage_axis), self.xincr)  
        ### creates the dict
        scope_reading = dict()
        scope_reading['time'] = np.squeeze(time_axis)
        scope_reading['voltage'] = np.squeeze(voltage_axis)        
        ### return
        return scope_reading
    
    
class AWGSession(ResourceSession):
    ''' Add AWG session inheriting from ResourceSession. '''
    def __init__(self, ResMgCrt, ResourceName, Role = 'Gunner'):
        ResourceSession.__init__(self, ResMgCrt, ResourceName)
        ### 'Role' can be either 'Gunner' (default) or 'Captain'
        ### 'Captain' is the only one allowed to trigger the others. CHECK the hardware connections 
        ### to identify the 'Captain'. If a device stands alone, it has to be a 'Captain' to be triggered.
        ### IF AWG'S ESTERNAL TRIGGERS ARE PHYSICALLY CONNECTED THERE CAN BE JUST ONE CAPTAIN.
        self.role = Role
        self.triggersource = ''
        if self.role == 'Captain': 
            self.triggersource = 'BUS'
            self.resource.write('OUTP:TRIG ON')
        else: 
            self.triggersource = 'EXT'
            self.resource.write('OUTP:TRIG OFF') 
        print('Resource role: ' + self.role )
        if self.resource.query('OUTP1?'): 
            self.resource.write('OUTP1 OFF')
            print('Output1 :', self.resource.query('OUTP1?'), end = '')
        if self.resource.query('OUTP2?'): 
            self.resource.write('OUTP2 OFF')
            print('Output2 :', self.resource.query('OUTP2?'))
        if self.resource.query('OUTP:SYNC?'): self.resource.write('OUTP:SYNC OFF')
        self.resource.write('SOUR1:VOLT:LIM:STAT 0')
        self.resource.write('SOUR2:VOLT:LIM:STAT 0')  
    
    def ApplyBuiltinWaveform(self, Load, AWGChannelNum, FunctionType = 'SIN', Freq = '1e3', Vpp = '1', Offset = '0' ):
        ''' Apply a AWG built-in waveform. '''
        ### Automatically set trigger source to IMMediate.
        ### 'Vpp' is the peak-to-peak voltage in Volts and it is always positive.
        ### Freq is the frequency in hertz.
        self.resource.write('OUTP' + AWGChannelNum + ':' + 'LOAD' + ' ' + Load)  
        print(self.resource_name + ' Output ON -> ' + FunctionType + ' ,Vpp: ' + Vpp + ' V, Offset: ' + Offset +  ' V')
        ### waveform
        #if (float(Vpp)/2 + float(Offset)) <= 5.2 and (-float(Vpp)/2 + float(Offset)) >= -5.2:
        self.resource.write('SOUR' + AWGChannelNum + ':' + 'APPL' + ':' + FunctionType + ' ' + Freq + ' HZ, ' + Vpp + ' VPP, ' + Offset + ' V')
            
    def ApplyDCVoltage(self, Load, AWGChannelNum, Volt = '0' ):
        ''' Apply a DC voltage to a specified channel. '''
        ### Set trigger source to IMMediate.
        ### Set the Load (INF|MIN|MAX|DEF).
        self.resource.write('OUTP' + AWGChannelNum + ':' + 'LOAD' + ' ' + Load)  
        print(self.resource_name + ' CH' + AWGChannelNum + ' Output ON -> ' + 'DC: ' + Volt + ' V' + ' \n')
        ### waveform
        #if float(Volt) < 5.2 and float(Volt) > -5.2:
        self.resource.write('SOUR' + AWGChannelNum + ':' + 'APPL' + ':' + 'DC DEF, DEF, ' + Volt)
    
    def OutputOff(self, AWGChannelNum):
        ''' Set the output to off. '''
        if self.resource.query('OUTP' + AWGChannelNum + '?'): 
            self.resource.write('OUTP' + AWGChannelNum + ' OFF')
        print('Output ' + self.resource_name + ' channel ' + AWGChannelNum + ': ' + self.resource.query('OUTP' + AWGChannelNum + '?'))
    
    def SetLoad(self, AWGChannelNum, Load):
        ''' Set the Load (INF|MIN|MAX|DEF). '''
        self.resource.write('OUTP' + AWGChannelNum + ':' + 'LOAD' + ' ' + Load)
    
    def Clear(self):
        ''' Clear event register, error queue -when power is cycled-. '''
        self.resource.write('*CLS')
        self.resource.write('*WAI')
       
    def ClearVolatileMemory(self, AWGChannelNum):
        ''' Clear event register, error queue -when power is cycled-. '''
        self.resource.write('SOUR' + AWGChannelNum + ':' + 'DATA:VOL:CLE') ### Clear Volatile Memory
        self.resource.write('*WAI')
    
    def Reset(self):
        ''' Reset instrument to factory default state. Does not clear volatile memory. '''
        self.resource.write('*RST')
        self.resource.write('*WAI')
        
    def StopTrigger(self):
        ''' Stop any triggered action or sequences. 
        Then Turn the outputs off. 
        '''
        self.resource.write('ABORt')
        self.resource.write('OUTP1 OFF')
        self.resource.write('OUTP2 OFF')
        
    def SyncOn(self, AWGChannelNum, Mode = 'NORM'):
        ''' Switch on the Sync signal. '''
        ### 3.3 V, TTL compatible
        ### SYNC Source CH1 by default
        self.resource.write('OUTP' + AWGChannelNum + ':' + 'SYNC:MODE ' + Mode)
        self.resource.write('OUTP:SYNC ON')
        
    def SetSyncOn(self, AWGChannelNum, MarkerPosition, Polarity):
        ''' Set the Sync for arbitrary waveforms. 
        Just for Arbitrary waveforms. 3.3 V, TTL compatible.
        Sync Source CH1 by default.
        '''
        ### MarkerPosition (string) indicates the sample number at which Sync starts 
        ### Polarity can be either 'NORM' (from 1 to 0 at the marker position) or 'INV'
        #print('Selected Function: ' + self.resource.query('SOUR' + AWGChannelNum + ':FUNC?'))
        #print('Selected Arbitrary Function name: ' + self.resource.query('SOUR' + AWGChannelNum + ':FUNC:ARB?'))                               
        self.resource.write('OUTP' + AWGChannelNum + ':' + 'SYNC:MODE CARR')   
        self.resource.write('OUTP' + AWGChannelNum + ':' + 'SYNC:POL ' + Polarity)
        self.resource.write('SOUR' + AWGChannelNum + ':MARK:POIN ' + MarkerPosition)  
        self.resource.write('OUTP:SYNC ON') 
        #print('Sync Polarity: ' + self.resource.query('OUTP' + AWGChannelNum + ':' + 'SYNC:POL?'))
        #print('Marker Point: ' + self.resource.query('SOUR' + AWGChannelNum + ':MARK:POIN?'))
               
    def SyncOff(self):
        ''' Switch off the Sync signal. '''
        if self.resource.query('OUTP:SYNC?'):
            self.resource.write('OUTP:SYNC OFF')
        print('Output ' + self.resource_name + ': ' + self.resource.query('OUTP:SYNC?') + ' \n')
        
    def AddArbitraryWaveformToChannelVolatileMemory(self, FuncVect, AWGChannelNum, FuncName):
        ''' Store an arbitrary waveform saved in a list into an AWG channel 
        volatile memory.
        '''
        ### FuncVect is a list containing the voltage values (floating point) of the function. 
        ### FuncName is the name you wish to give to the uploaded arbitrary fuction, usually taken
        ### from the 'values' in ResourceNameToJob dictionary
        FuncVect = str(FuncVect)
        self.func_vect = str()
        for i in range(1, len(FuncVect)-1): self.func_vect = self.func_vect + FuncVect[i]
        self.resource.write('SOUR' + AWGChannelNum + ':' + 'DATA:VOL:CLE') ### Clear Volatile Memory
        self.resource.write('*WAI') ### Wait for the operation to be completed
        self.resource.write('SOUR' + AWGChannelNum + ':' + 'DATA:ARB ' + FuncName + ', ' + self.func_vect)
        self.resource.write('*WAI') ### Wait for the operation to be completed
        self.resource.write('SOUR' + AWGChannelNum + ':' + 'FUNC:ARB ' + FuncName) ### select the desired waveform 
               
    def ApplyArbitraryWaveform(self, FuncName, AWGChannelNum, SampleRate, Vpp = '2.5', Offset = '0'):
        ''' Turns the Output on after having defined all the parameters. 
        Keeps running the waveform. Sample rate is in Sa/s. 
        '''
        ### FuncName is the name of the function already in the volatile memory.
        ### It sets trigger source to IMMediate.
        self.resource.write('SOUR' + AWGChannelNum + ':' + 'FUNC:ARB ' + FuncName) ### select the desired waveform 
        self.resource.write('SOUR' + AWGChannelNum + ':' + 'APPL:ARB ' + SampleRate + ' HZ,' + Vpp + ' VPP,' + Offset + ' V')
        print('ARB apply: ' + self.resource.query('SOUR' + AWGChannelNum + ':' + 'APPL?'))
    
    def SetBurstOuputArbitraryWaveform(self, Load, FuncName, AWGChannelNum, SampleRate, VHigh = '2.5', VLow = '0'):
        ''' Set the arbitrary waveform stored in the channel volatile memory 
        in burst mode and let it wait for trigger.
        '''
        ### To start the arbitrary waveform you need to apply a trigger with Trigger()
        ### FuncName is the name of the function already in the volatile memory that you gave to 
        ### the uploaded arbitrary fuction as a parameter in AddArbitraryWaveformToChannelVolatileMemory()
        ### SampleRate in Sa/s
        ### All the values in the arbitrary waveform have to fall in the [-1, +1].
        ### Sets the proper trigger according to the Role
        if self.role == 'Captain': self.triggersource = 'BUS'
        else: self.triggersource = 'EXT'
        ### Write arbitrary function parameters
        self.resource.write('OUTP' + AWGChannelNum + ':' + 'LOAD' + ' ' + Load)
        self.resource.write('SOUR' + AWGChannelNum + ':FUNC ARB') ###Tells the AWG to select the ARB function as output
        self.resource.write('SOUR' + AWGChannelNum + ':' + 'FUNC:ARB ' + FuncName) ### select the desired ARB waveform
        #print('ARB points: ' + self.resource.query('SOUR' + AWGChannelNum + ':FUNC:ARB:POIN?'))
        self.resource.write('SOUR' + AWGChannelNum + ':' + 'FUNC:ARB:FILT ' + 'OFF')    
        #print('Filter: ' + self.resource.query('SOUR' + AWGChannelNum + ':FUNC:ARB:FILT?'))
        self.resource.write('SOUR' + AWGChannelNum + ':' + 'FUNC:ARB:SRAT ' + SampleRate) ### Sa/s
        #print('Sample Rate: ' + self.resource.query('SOUR' + AWGChannelNum + ':FUNC:ARB:SRAT?'))
        self.resource.write('SOUR' + AWGChannelNum + ':' + 'VOLT:HIGH ' + VHigh)
        self.VHigh = self.resource.query('SOUR' + AWGChannelNum + ':' + 'VOLT:HIGH?')
        self.resource.write('SOUR' + AWGChannelNum + ':' + 'VOLT:LOW ' + VLow) 
        self.VLow = self.resource.query('SOUR' + AWGChannelNum + ':' + 'VOLT:LOW?')
        print('Selected Function channel ' + AWGChannelNum + ' for ' + self.resource_name + ': ' + self.resource.query('SOUR' + AWGChannelNum + ':FUNC:ARB?'), end = '')
        print('VHigh: ' + self.VHigh + ' V, VLow: ' + self.VLow + ' V, Sample Rate: ' + SampleRate + ' Sa/s, Load: ' + Load + ' Ohm' + '\n')
        self.resource.write('*WAI')
        ### BURST commands.
        self.resource.write('SOUR' + AWGChannelNum + ':BURS:MODE TRIG')              
        self.resource.write('SOUR' + AWGChannelNum + ':BURS:NCYC 1') ### Burst cycles
        self.resource.write('TRIG' + AWGChannelNum + ':SOUR ' + self.triggersource)  ### BUS trigger allows to have repetition of waveform as much as NCYC
        self.resource.write('SOUR' + AWGChannelNum + ':BURS:STAT ON')  
        #if (float(VHigh)) < 5.2 and (float(VLow)) > -5.2:
        self.resource.write('OUTP' + AWGChannelNum + ' ON')
        self.resource.write('*WAI')
        #else: 
        #    print('Voltage out of range, Output OFF')
        #    self.resource.write('OUTP' + AWGChannelNum + ' OFF')
               
    def Trigger(self):
        ''' Applies a trigger to both AWG channels 
        (they output a waveform just if their output is on).
        If both channels are in BURTS mode, the outputs are 
        automatically synchronised.
        JUST A CAPTAIN CAN BE TRIGGERED THIS WAY.
        '''
        self.resource.write('*WAI')
        if self.role == 'Captain':
            if self.resource.query('*OPC?'):
                self.resource.write('*TRG')
                self.resource.write('*WAI')                
                print('TRIGGER!')
                #self.resource.write('OUTP:TRIG OFF') ### Does not switch off the trigger output, just disable it
            else: print('Communication still running between the computer and the devices. No trigger was otputted.')
        else: print('The selected device is not a Captain and cannot therefore be triggered')
           
    def PrintError(self):
        ''' Print eventual errors occurred. '''
        print(self.resource_name + ' Errors: ' + self.resource.query('SYST:ERR?'), end = '')
        
    def OffAndCloseAWG(self, ResMgCrt):
        ''' Switch off the Sync signal. '''
        if self.resource.query('OUTP:SYNC?'):
            self.resource.write('OUTP:SYNC OFF')
        print('Output ' + self.resource_name + ' Sync: ' + self.resource.query('OUTP:SYNC?'), end = '')
        ''' Set the output to off. '''
        if self.resource.query('OUTP1?'): 
            self.resource.write('OUTP1 OFF')
        print('Output ' + self.resource_name + ' channel 1: ' + self.resource.query('OUTP1?'), end = '')
        if self.resource.query('OUTP2?'): 
            self.resource.write('OUTP2 OFF')
        print('Output ' + self.resource_name + ' channel 2: ' + self.resource.query('OUTP2?'), end = '')
        ''' Close Resource session.  '''
        self.resource.close()
        print('Closing Resource: ', self.resource_name, '\n')
        ResMgCrt.RemoveResourceFromTheIndex(self.resource_name)
    
    def StoreWaveformToNotVolatileMemory():
        ''' Store a waveform to not-volatile memory. '''
        ### from volatile to not volatile memory. MMEMory:STORe:DATA stores instrument current setting as well
        ToBeBuilt
        
    def LoadWaveformFromNotVolatileMemory():
        ''' Load a waveform from not-volatile memory. '''
        ### from not volatile to volatile memory 
        ToBeBuilt

        
        
        
        