# -*- coding: utf-8 -*-
"""
Created on Thu May 23 16:35:04 2019

@author: ruggero

Script used to output simple built-in functions from AWGs.

ALWAYS CHECK VOLTAGE LIMITS AND LOADS!!!
"""

import numpy as np
from struct import unpack
import time
import visa
from MultiResources import ResourceManagerCreator, ResourceSession, AWGSession,  OscilloscopeSession

# %% INITIALISATION   ### DS: DeviceSession.
Mg = ResourceManagerCreator() ### Create Manager.
'''
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
'''
#OSC = OscilloscopeSession(Mg, 'OSC_MDO3024')

# %% OUTPUT
'''
DS_AWG1.ApplyDCVoltage(Load ='1000', AWGChannelNum = '1', Volt = '1')
DS_AWG1.ApplyDCVoltage(Load ='1000', AWGChannelNum = '2', Volt = '3.9')

DS_AWG2.ApplyDCVoltage(Load ='1000', AWGChannelNum = '1', Volt = '5')
DS_AWG2.ApplyDCVoltage(Load ='1000', AWGChannelNum = '2', Volt = '5')

DS_AWG3.ApplyDCVoltage(Load ='1000', AWGChannelNum = '1', Volt = '4')
DS_AWG3.ApplyDCVoltage(Load ='1000', AWGChannelNum = '2', Volt = '9')

DS_AWG4.ApplyDCVoltage(Load ='50', AWGChannelNum = '1', Volt = '0')
DS_AWG4.ApplyDCVoltage(Load ='1000', AWGChannelNum = '2', Volt = '7')

DS_AWG5.ApplyDCVoltage(Load ='INF', AWGChannelNum = '1', Volt = '0')
DS_AWG5.ApplyDCVoltage(Load ='INF', AWGChannelNum = '2', Volt = '0')
'''

#DS_AWG3.ApplyBuiltinWaveform(Load = '1000', AWGChannelNum = '2', FunctionType = 'TRI', Freq = '0.5', Vpp = '8', Offset = '5')


# %% CLOSE EVERY OUTPUT AND RESOURCE

#OSC.CloseResource(Mg)

#DS_AWG2.OutputOff('1')

#DS_AWG4.Clear()

'''
### OUTPUTS do not get to 0 at the end of the arb waveform.
if 'AWG1' in Mg.OpenedResourceNames: DS_AWG1.OffAndCloseAWG(Mg)
if 'AWG2' in Mg.OpenedResourceNames: DS_AWG2.OffAndCloseAWG(Mg)
if 'AWG3' in Mg.OpenedResourceNames: DS_AWG3.OffAndCloseAWG(Mg)
if 'AWG4' in Mg.OpenedResourceNames: DS_AWG4.OffAndCloseAWG(Mg)
if 'AWG5' in Mg.OpenedResourceNames: DS_AWG5.OffAndCloseAWG(Mg)

Mg.WhoIsUp()
if Mg.OpenedResources == 0: Mg.CloseResourceManager()   
'''
