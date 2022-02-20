# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 13:50:35 2019

@author: MOT_User
"""

import os
import matplotlib.pyplot as plt
from PIL import Image ###usefull to convert np.array in images when saving them
#from scipy.optimize import curve_fit
import numpy as np
from scipy import ndimage, optimize
import cv2
from tifffile import imsave
import copy

#%% GENERAL FUNCTIONS

def Gauss(x,a,x0,sigma,k):
    return a*np.exp(-(x-x0)**2/(2*sigma**2)) + k

def FlatTopGauss(x,a,x0,sigma,k):
    return a*np.exp(-((x-x0)**2/(2*sigma**2))**2) + k

def SaturatedExp(x, N, g, c):
    return N*(1 - np.exp(-g*x)) + c

def std_dev(lst):
    """returns the standard deviation of lst"""
    mn = np.mean(lst)
    variance = sum([(e-mn)**2 for e in lst]) / (len(lst)-1)
    return np.sqrt(variance)

def SubtractImgs(Img1, Img2):
    ''' Returns a ndarray as a result of Img1 - Img2.
    '''
    img_1 = copy.deepcopy(Img1)
    img_2 = copy.deepcopy(Img2)
    ###
    Img_sub = np.zeros((img_1.shape[0], img_1.shape[1]))
    for i in range(0, img_1.shape[0]):
        for j in range(0, img_1.shape[1]):
            if img_1[i,j] > img_2[i,j]: Img_sub[i,j] = img_1[i,j] - img_2[i,j]
            else: Img_sub[i,j] = 0
    return Img_sub

def LogImg(Img1):
    '''Log of an Image'''
    img_1 = copy.deepcopy(Img1)
    ###
    Img_log = np.zeros((img_1.shape[0], img_1.shape[1]))
    for i in range(0, img_1.shape[0]):
        for j in range(0, img_1.shape[1]):
            if img_1[i, j] != 0: Img_log[i,j] = np.log(img_1[i,j])
            else: Img_log[i,j] = 0
            if Img_log[i,j] < 0: Img_log[i,j] = 0
    return Img_log

def DivideImgs(Img1, Img2, cut = 0, lim = 0.8):
    ''' Returns a ndarray as a result of Img1/Img2.
    Cuts lowest value of each image because a division
    of small intensity is higly sensitive to noise.
    When img_2[i,j] = 0, substitute 0 with lim.
    '''
    img_1 = copy.deepcopy(Img1)
    img_2 = copy.deepcopy(Img2)
    img_1.astype(float)
    img_2.astype(float)
    ###
    Img_div = np.zeros((img_1.shape[0], img_1.shape[1]))
    Img_div = Img_div.astype(float)
    for i in range(0, img_1.shape[0]):
        for j in range(0, img_1.shape[1]):
            if img_1[i,j] <= cut: img_1[i,j] = 0
            if img_2[i,j] <= cut: img_2[i,j] = 0
            if img_1[i,j] == 0: 
                Img_div[i,j] = 0
            elif img_2[i,j] == 0: 
                img_2[i,j] = lim  
                Img_div[i,j] = img_1[i,j]/img_2[i,j]                             
            else: Img_div[i,j] = img_1[i,j]/img_2[i,j]
    return Img_div

def DivideImgs_Avg(Img1, Img2, cut = 0):
    ''' Returns a ndarray as a result of Img1/Img2.
    Cuts lowest value of each image because a division
    of small intensity is higly sensitive to noise.
    When img_2[i,j] = 0, performs an average of pixels
    in the neighbourhood.
    '''
    img_1 = copy.deepcopy(Img1)
    img_2 = copy.deepcopy(Img2)
    img_1.astype(float)
    img_2.astype(float)
    ###
    Img_div = np.zeros((img_1.shape[0], img_1.shape[1]))
    Img_div = Img_div.astype(float)
    for i in range(0, img_1.shape[0]):
        for j in range(0, img_1.shape[1]):
            if img_1[i,j] <= cut: img_1[i,j] = 0
            if img_2[i,j] <= cut: img_2[i,j] = 0
            if img_1[i,j] == 0: 
                Img_div[i,j] = 0
            elif img_2[i,j] == 0: 
                s = 1
                while s != 0:
                    count = 0
                    no_zero = 0
                    for k in range(0-s, 1+s):
                        for l in range(0-s, 1+s):
                            if img_2[i+k,j+l] != 0:
                                count = count + img_2[i+k,j+l]
                                no_zero += 1
                    if no_zero != 0: 
                        img_2[i,j] = count / no_zero 
                        Img_div[i,j] = img_1[i,j]/img_2[i,j]
                        s = 0
                    else: s += 1                                  
            else: Img_div[i,j] = img_1[i,j]/img_2[i,j]
    return Img_div

#%% PANSHOTS

def PanShotAbsorption(ImgAbs, ImgBkg, folder_path, PanShotName = 'none'):
    ''' Create a Figure with 4 subplot containing the absorption coefficient and
    the optical density pictures. 
    ImgAbs is the absorption, while the ImgBkg cointains the laser not absorbed (background).
    '''
    img_abs = copy.deepcopy(ImgAbs)
    img_bkg = copy.deepcopy(ImgBkg)
    ###
    fig = plt.figure()
    fig.suptitle('Absorption Experiment') 
    plt.subplot(221)
    plt.tight_layout()
    plt.title('Absorption')
    plt.gray() 
    plt.imshow(img_abs)
    plt.colorbar()
    plt.ylabel('row [pixel]')
    plt.xlabel('col [pixel]')
    plt.subplot(222)
    plt.tight_layout()
    plt.title('Background')
    plt.gray() 
    plt.imshow(img_bkg)
    plt.colorbar()
    plt.ylabel('row [pixel]')
    plt.xlabel('col [pixel]')
    ### Absorption Coefficient
    I_abs = SubtractImgs(img_bkg, img_abs)
    abs_coeff = DivideImgs(I_abs, img_bkg)
    plt.subplot(223)
    plt.tight_layout()
    plt.title('Absorption Coefficient')
    AbsPlot = plt.imshow(abs_coeff , cmap= 'rainbow')
    AbsPlot.set_clim(0, 1)
    plt.colorbar() 
    plt.ylabel('row [pixel]')
    plt.xlabel('col [pixel]')
    ### Optical Density
    div = DivideImgs(img_bkg, img_abs)
    opt = np.zeros((div.shape[0], div.shape[1]))
    for i in range(0, div.shape[0]):
        for j in range(0, div.shape[1]):
            if div[i, j] != 0: opt[i,j] = np.log(div[i,j])
            else: opt[i,j] = 0
            if opt[i,j] < 0: opt[i,j] = 0
    plt.subplot(224)
    plt.tight_layout()
    plt.title('Optical Density')
    plt.imshow(opt, cmap= 'rainbow')
    plt.colorbar()
    plt.ylabel('row [pixel]')
    plt.xlabel('col [pixel]')
    ### SAVING PICTURE
    if PanShotName != 'none':
        plt.savefig(folder_path + '\\' + PanShotName)
    ###Just OPT
    '''
    plt.figure()
    plt.title('Optical Density')
    plt.imshow(opt, cmap= 'rainbow')
    plt.colorbar()
    plt.ylabel('row [pixel]')
    plt.xlabel('col [pixel]')
    '''
    ###Just I_abs
    '''
    plt.figure()
    plt.title('Absorbed Intensity')
    plt.imshow(I_abs, cmap= 'rainbow')
    plt.colorbar()
    plt.ylabel('row [pixel]')
    plt.xlabel('col [pixel]')
    '''
    #plt.savefig(folder_path + '\\' + 'Opt_density')
    ### RETURNS
    return abs_coeff, opt

def PanShotAbsorptionReduced(ImgAbs, ImgBkg, folder_path, PanShotName = 'none'):
    ''' Create a Figure with 2 subplot containing the absorption coefficient and
    the optical density pictures. 
    ImgAbs is the absorption, while the ImgBkg cointains the laser not absorbed (background).
    '''
    img_abs = copy.deepcopy(ImgAbs)
    img_bkg = copy.deepcopy(ImgBkg)
    ### Absorption Coefficient
    I_abs = SubtractImgs(img_bkg, img_abs)
    abs_coeff = DivideImgs(I_abs, img_bkg)
    ### Optical Density
    div = DivideImgs(img_bkg, img_abs)
    opt = np.zeros((div.shape[0], div.shape[1]))
    for i in range(0, div.shape[0]):
        for j in range(0, div.shape[1]):
            if div[i, j] != 0: opt[i,j] = np.log(div[i,j])
            else: opt[i,j] = 0
            if opt[i,j] < 0: opt[i,j] = 0
    ### Plot
    '''
    plt.figure() 
    plt.subplot(121)
    plt.tight_layout()
    plt.title('Absorption Coefficient')
    AbsPlot = plt.imshow(abs_coeff , cmap= 'rainbow')
    AbsPlot.set_clim(0, 1)
    plt.colorbar() 
    plt.ylabel('row [pixel]')
    plt.xlabel('col [pixel]')
    plt.subplot(122)
    plt.tight_layout()
    plt.title('Optical Density')
    plt.imshow(opt, cmap= 'rainbow')
    plt.colorbar()
    plt.ylabel('row [pixel]')
    plt.xlabel('col [pixel]') 
    '''
    ###Just I_abs
    plt.figure()
    plt.title('Absorbed Intensity')
    plt.imshow(I_abs, cmap= 'rainbow')
    plt.colorbar()
    plt.ylabel('row [pixel]')
    plt.xlabel('col [pixel]')
       
    ###Just OPT
    '''
    plt.figure()
    plt.title('Optical Density')
    plt.imshow(opt, cmap= 'rainbow')
    plt.colorbar()
    plt.ylabel('row [pixel]')
    plt.xlabel('col [pixel]')
    '''
    ### SAVING PICTURE
    if PanShotName != 'none':
        plt.savefig(folder_path + '\\' + PanShotName)
    ### RETURNS
    return abs_coeff, opt
    

#%% CLASS

class Image_Matrix():
    def __init__(self, ImageName = 'none', Array = 'none', folder_path = 'none'):
        '''Acquires an image(.bmp) with given Imagename or acquires an ndarray.
        Allows to perform some operations on the image.
        ImageName is a string of the type 'MOT_0_2_270919.bmp'.
        Matrix [row, column] notation is used. 
        '''
        if Array is 'none' and ImageName == 'none':
            print('!!!No array or image given!!!')
        else: 
            if Array is 'none':
                if folder_path is 'none':
                    print('!!!No path to folder specified!!!')
                else: 
                    self.path = folder_path
                    self.ImageName = ImageName
                    self.image = plt.imread(os.path.join(self.path, self.ImageName))  ### returns a ndarray  
                    self.row_len = self.image.shape[0]
                    self.col_len = self.image.shape[1]       
            if ImageName == 'none':
                self.image = Array
                self.ImageName = 'Array'
                self.row_len = self.image.shape[0]
                self.col_len = self.image.shape[1] 
            #print('\n Image acquired: ' + self.ImageName)

    def ImagePlot(self):
        ''' Plot the image. '''
        plt.figure()
        plt.gray()
        plt.imshow(self.image) ### lower is in the xy configuration
        plt.ylabel('row [pixel]')
        plt.xlabel('col [pixel]')
        plt.title(self.ImageName) 
        
    def RedLineImagePlot(self,  hor_ver, pos, row_lims = 'none', col_lims = 'none', new_fig = 'Y'):
        ''' Plot the image with a red line where you take the profile.
        Lims should be passed as a two value list [-,-].
        hor_ver tells if you want the red line along 'hor' or 'ver' direction
        '''
        if row_lims == 'none': row_lims = [0, self.row_len]
        if col_lims == 'none': col_lims = [0, self.col_len]
        if new_fig == 'Y': plt.figure()
        plt.gray()
        plt.imshow(self.image[row_lims[0]:row_lims[1], col_lims[0]:col_lims[1]], extent=[col_lims[0], col_lims[1], row_lims[1], row_lims[0]])
        plt.ylabel('row [pixel]')
        plt.xlabel('col [pixel]')
        plt.title(self.ImageName)  
        ### Draw the line where the profile is obtained
        x_ax = []
        y_ax = []
        if hor_ver == 'hor':
            for i in range(col_lims[0], col_lims[1]): 
                x_ax.append(i)
                y_ax.append(pos)
        if hor_ver == 'ver':    
            for i in range(row_lims[0], row_lims[1]): 
                x_ax.append(pos)
                y_ax.append(i)
        plt.plot(x_ax, y_ax, 'r-')
        
    
    def GetTotalIntensity(self):
        ''' Takes a pic array and print the total pixel integrated intensity'''
        counter = 0
        for j in range(self.row_len):
            for k in range(self.col_len):
                counter = counter + self.image[j,k]
        print('Total integrated intensity of the image: ', counter)
        
    def HorProfile(self, pos, col_lims = 'none'):
        ''' Slices a picture horizontally.'''
        y_ax = []
        x_ax = []
        if col_lims == 'none': col_lims = [0, self.col_len]
        for i in range(col_lims[0], col_lims[1]):
            x_ax.append(i)
            y_ax.append(self.image[pos, i])
        return y_ax, x_ax
    
    def VerProfile(self, pos, row_lims = 'none'):
        ''' Slices a picture vertically.'''
        y_ax = []
        x_ax = []
        if row_lims == 'none': row_lims = [0, self.row_len]
        for i in range(row_lims[0], row_lims[1]):
            x_ax.append(i)
            y_ax.append(int(self.image[i, pos]))
        return y_ax, x_ax
                     
    def ProfilePlot(self, hor_ver, pos, lims = 'none', new_fig = 'Y'):
        ''' Plot the Profile of a image slice, vertically or horizontally.'''
        y_ax = []
        x_ax = []
        if hor_ver == 'hor': [y_ax, x_ax] = self.HorProfile(pos, lims)
        if hor_ver == 'ver': [y_ax, x_ax] = self.VerProfile(pos, lims)
        if new_fig == 'Y': plt.figure()  
        plt.plot(x_ax, y_ax)
        plt.ylabel('Intensity [a.u.]')
        if hor_ver == 'hor':  plt.xlabel('col [pixel]')
        if hor_ver == 'ver':  plt.xlabel('row [pixel]')
        plt.title(self.ImageName) 
    
    def FitProfilePlot(self, hor_ver, pos, fit_function, init_guess, lims = 'none', new_fig = 'Y' ):
        ''' Plot the Profile of a image slice,  vertically or horizontally,
        and fits it with a Gaussian.
        '''
        y_ax = []
        x_ax = []
        if hor_ver == 'hor': [y_ax, x_ax] = self.HorProfile(pos, lims)
        if hor_ver == 'ver': [y_ax, x_ax] = self.VerProfile(pos, lims)
        if new_fig == 'Y': plt.figure()  
        plt.plot(x_ax, y_ax)
        plt.ylabel('Intensity [a.u.]')
        if hor_ver == 'hor':  plt.xlabel('col [pixel]')
        if hor_ver == 'ver':  plt.xlabel('row [pixel]')
        plt.title(self.ImageName) 
        ### FIT
        popt, pcov = optimize.curve_fit(fit_function, x_ax, y_ax, p0 = init_guess, method = 'trf')
        print('Fit Parameters:', popt) ### [a,x0,sigma]
        fit_array = (fit_function(x_ax, *popt))
        plt.plot(x_ax, fit_array, 'r-')
        ### Contrast
        print('Contrast [Max/Min]: ' + str(max(fit_array)/min(fit_array)))
        ### FWHM 
        '''
        ext = optimize.fsolve(fit_function-((max(fit_array)+min(fit_array))/2), [popt[1]-2*popt[2],popt[1]+2*popt[2]], popt)
        print('FWHM [pixel]: ', str(abs(ext[1]-ext[0])))
        '''
        

#%%

#folder_path = r'C:\Users\MOT_User\Documents\MOT\QuantumLabPython\ExperimentMOT_special\Output' + '\\' + 'Pump_and_Probe'
'''
ImageCam1 = Image_Matrix('Cam0_0_1.bmp')
ImageCam2 = Image_Matrix('Cam0_0_2.bmp')
ImageCam3 = Image_Matrix('Cam0_0_3.bmp')
abs_coeff, opt = PanShotAbsorption(SubtractImgs(ImageCam1.image, ImageCam2.image), folder_path, SubtractImgs(ImageCam3.image, ImageCam2.image), 'PanShot_cam0_exp0')        
'''      
        
'''     
ImageCam = Image_Matrix('Cam0_2_1.bmp')   
ImageCam.ImagePlot() 

ImageCam.GetTotalIntensity()  
plt.figure()
plt.subplot(121)
ImageCam.RedLineImagePlot(hor_ver = 'hor', pos = 120, row_lims ='none', col_lims ='none', new_fig = 'N')
plt.subplot(122)
ImageCam.FitProfilePlot(hor_ver = 'hor', pos = 120, fit_function = FlatTopGauss, init_guess = [-50, 150, 10, 100], lims = 'none', new_fig = 'N')
plt.tight_layout()
'''











