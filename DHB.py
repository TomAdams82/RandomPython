#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 11:09:39 2020

@author: sparky
"""

import shapefile
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.patches as mpatches
import datetime
from matplotlib import gridspec

normalise = False

shpfn = '/home/sparky/Documents/Covid19/simpleDHBs.shp'
mohDataFn = '/home/sparky/Documents/Covid19/covid-cases-1_apr_2020.xlsx'
popDHBdata = '/home/sparky/Documents/Covid19/DHBpopulations.csv'
imgFolder = '/home/sparky/Documents/Covid19/images/'

DateColHeader = 'Date of report'
SkipExcelHeaderRows = 3
maxDay = 0

#As per shapefile (not Nelson and Marlborough are combined)
DHBnames = {'Auckland' : 1, 'Bay of Plenty' : 2,'Canterbury' : 3,'Capital and Coast' : 4,
            'Counties Manukau' : 5, "Hawke's Bay" : 6,"Hutt" : 7,"Lakes" : 8,"Midcentral" : 9,
            "Nelson Marlborough" : 10,"Northland" : 11, "South Canterbury" : 12,
            "Southern" : 13,"Tairawhiti" : 14,"Taranaki" : 15 ,"Waikato" : 16,
            "Wairarapa" : 17, "Waitemata" : 18,"West Coast" : 19,"Whanganui" : 20}
#As per MoH data
DHBalias = {'Auckland' : 1, 'Bay of Plenty' : 2,'Canterbury' : 3,'Capital and Coast' : 4,
            'Counties Manukau' : 5, "Hawke's Bay" : 6,"Hutt Valley" : 7,"Lakes" : 8,"MidCentral" : 9,
            "Nelson Marlborough" : 10,"Northland" : 11, "South Canterbury" : 12,
            "Southern" : 13,"Tairawhiti" : 14,"Taranaki" : 15 ,"Waikato" : 16,
            "Wairarapa" : 17, "Waitemata" : 18,"West Coast" : 19,"Whanganui" : 20}

#DHBpopulations in 2020
df = pd.read_csv(popDHBdata)
DHBpop = dict(zip(list(df.DHB), list(df.pop2020)))

#read MoH data
df = pd.read_excel(mohDataFn, sheetname='Confirmed', skiprows = SkipExcelHeaderRows)
df2 = pd.read_excel(mohDataFn, sheetname='Probable', skiprows = SkipExcelHeaderRows)
#time span
startDate = np.min(df[DateColHeader]).to_pydatetime()
endDateA = np.max(df[DateColHeader]).to_pydatetime()
endDateB = np.max(df2[DateColHeader]).to_pydatetime()
endDate = np.max([endDateA,endDateB])
duration = (endDate-startDate).days+1

nDHBs = len(DHBnames)
cases = np.zeros([nDHBs,duration]) # Matrix of cases by DHB, by day

#confirmed
for d,dhb in zip(df[DateColHeader],df['DHB']):
    caseDay = d.to_pydatetime()
    j = (caseDay-startDate).days
    i = DHBalias[dhb]-1
    cases[i,j]+=1

# Repeat for probable
for d,dhb in zip(df2[DateColHeader],df2['DHB']):
    caseDay = d.to_pydatetime()
    j = (caseDay-startDate).days
    i = DHBalias[dhb]-1
    cases[i,j]+=1

# find cumulative cases
cumulativeCases = np.zeros([nDHBs,duration]) # Cumulative cases by DHB, by day
for i in range(duration):
    cumulativeCases[:,i]= np.sum(cases[:,:i+1],axis = 1)

totalCases = np.sum(cumulativeCases,axis=0)

if normalise:
    totalPop = 0
    casesNormalised = np.zeros(cases.shape)
    for dhb in DHBnames:
        casesNormalised[DHBnames[dhb]-1,:]=cases[DHBnames[dhb]-1,:]/DHBpop[dhb]
        totalPop += DHBpop[dhb]
    cases = casesNormalised * 100000
    # redo cumulative cases and scale total cases
    cumulativeCases = np.zeros([nDHBs,duration]) # Cumulative cases by DHB, by day
    for i in range(duration):
        cumulativeCases[:,i]= np.sum(cases[:,:i+1],axis = 1)
    totalCases=(totalCases/totalPop)*100000

maxCases = np.max(cumulativeCases)
    
#Set up legend
nGraduations = 10
x = np.linspace(0,1,nGraduations+1)
y = (np.round(x * maxCases)).astype(int)
legend_patches = []
if normalise:
    legend_patches.append(mpatches.Patch(color=[1,1,1], label='Cases per 100,000 people'))
else:
    legend_patches.append(mpatches.Patch(color=[1,1,1], label='Cumulative Cases'))
for i in range(nGraduations):
    if normalise:
        col = [1,1-x[i],1-x[i]]
    else:
        col = [1-x[i],1-x[i],1]
    lbl = str(y[i]) + ' - ' + str(y[i+1])
    legend_patches.append(mpatches.Patch(color=col, label=lbl))

    
sf = shapefile.Reader(shpfn)

for dy in range(maxDay,duration,1):
    print (str(dy+1)+'/'+str(duration))
    Ddate = startDate + datetime.timedelta(days=dy+1)
    dispDate = Ddate.strftime("%d/%m/%Y")

    #Just plot first part of multipart
    plt.figure(figsize=(9, 12), facecolor='w', edgecolor='w')
    gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1]) 
    for shape in sf.shapeRecords():
        nm = shape.record.NAME
        i_start = shape.shape.parts[0]
        if len(shape.shape.parts)==1:
            i_end = len(shape.shape.points)
        else:
            i_end = shape.shape.parts[1]
        x = [i[0] for i in shape.shape.points[i_start:i_end]]
        y = [i[1] for i in shape.shape.points[i_start:i_end]]
        dhbIndex = DHBnames[nm]-1
        nCases = cumulativeCases[dhbIndex,dy]
        if normalise:
            fillClr = [1,1-nCases/maxCases,1-nCases/maxCases]
        else:
            fillClr = [1-nCases/maxCases,1-nCases/maxCases,1]
        ax0 = plt.subplot(gs[0])
        ax0.fill(x,y, edgecolor='k', linewidth=1, facecolor=fillClr)
        ax0.axis('off')
        plt.title(dispDate,fontsize=20)
        dayStr = str(1000+dy)[2:]
        plt.legend(handles=legend_patches)
        ax1 = plt.subplot(gs[1])
        ax1.plot(np.linspace(0,duration-1,duration),totalCases,'b-')
        ax1.plot(dy,totalCases[dy],'bo',markersize=10,fillstyle='none')
        ax1.text(dy+1,int(totalCases[dy]+np.max(totalCases)/100),str(int(totalCases[dy])),fontsize=14)
        ax1.set_xlim([0,duration+5])
        ax1.set_ylim([int(np.max(totalCases)/-5),int(np.max(totalCases)+np.max(totalCases)/10)])
        ax1.set_xlabel('Day')
        ax1.set_ylabel('Cases')
        if normalise:
            ax1.set_title("Cases Per 100,000 people",fontsize=14)
            imgfn = imgFolder + 'normalised/img_' + dayStr + '.png'
        else:
            ax1.set_title("Total Confirmed and Probable Cases",fontsize=14)
            imgfn = imgFolder + 'img_' + dayStr + '.png'
        plt.savefig(imgfn)
        
    plt.close()
print('Done!')    
    


