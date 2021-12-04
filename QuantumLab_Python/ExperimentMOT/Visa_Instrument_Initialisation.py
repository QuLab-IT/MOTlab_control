# -*- coding: utf-8 -*-
"""
Created on Wed Jul  3 12:32:59 2019

@author: Ruggero


This file serve as a instrument test:
    Detects all the Visa resources connected and test if they can communicate
    properly with the computer. Then Close all the resources.

"""

### Standard library imports
import matplotlib.pyplot as plt
import time
import sys
import numpy as np
import csv
from struct import unpack
### Third party imports
import visa
### Local application imports
from MultiResources import ResourceManagerCreator, ResourceSession, AWGSession, OscilloscopeSession, CreateArbitraryWaveformVectorFromCSVFile, SelectWaveform

# %% INITIALISATION

AWGChannelsToBeUsed = ['AWG1_1', 'AWG2_1', 'AWG3_1', 'AWG5_2']

Mg = ResourceManagerCreator() ### Create Resource Manager
if 'AWG1_1' in AWGChannelsToBeUsed or 'AWG1_2' in AWGChannelsToBeUsed: DS_AWG1 = AWGSession(Mg, 'AWG1', 'Captain') ### DS: DeviceSession
if'AWG2_1' in AWGChannelsToBeUsed or 'AWG2_2' in AWGChannelsToBeUsed: DS_AWG2 = AWGSession(Mg, 'AWG2')
if 'AWG3_1' in AWGChannelsToBeUsed or 'AWG43_2' in AWGChannelsToBeUsed: DS_AWG3 = AWGSession(Mg, 'AWG3')
if 'AWG4_1' in AWGChannelsToBeUsed or 'AWG4_2' in AWGChannelsToBeUsed: DS_AWG4 = AWGSession(Mg, 'AWG4')
if 'AWG5_1' in AWGChannelsToBeUsed or 'AWG5_2' in AWGChannelsToBeUsed: DS_AWG5 = AWGSession(Mg, 'AWG5')
time.sleep(0.5)

Mg.WhoIsUp() 
time.sleep(0.5)

if 'AWG1' in Mg.OpenedResourceNames: DS_AWG1.PrintError()
if 'AWG2' in Mg.OpenedResourceNames: DS_AWG2.PrintError()
if 'AWG3' in Mg.OpenedResourceNames: DS_AWG3.PrintError()
if 'AWG4' in Mg.OpenedResourceNames: DS_AWG4.PrintError()
if 'AWG5' in Mg.OpenedResourceNames: DS_AWG5.PrintError()
time.sleep(0.5)

# %% CLOSE DEVICES 
if 'AWG1' in Mg.OpenedResourceNames: DS_AWG1.OffAndCloseAWG(Mg)
if 'AWG2' in Mg.OpenedResourceNames: DS_AWG2.OffAndCloseAWG(Mg)
if 'AWG3' in Mg.OpenedResourceNames: DS_AWG3.OffAndCloseAWG(Mg)
if 'AWG4' in Mg.OpenedResourceNames: DS_AWG4.OffAndCloseAWG(Mg)
if 'AWG5' in Mg.OpenedResourceNames: DS_AWG5.OffAndCloseAWG(Mg)

Mg.WhoIsUp()
if Mg.OpenedResources == 0: Mg.CloseResourceManager()  
