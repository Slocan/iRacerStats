#!/usr/bin/python3

# Filter all the sessions to grab race data about one particular user
# And export to panda csv files

################ Manual Configuration ####

# The playername, exactly as displayed in the iRacing interface
playerName = 'First Latename'

###############

import os, glob
import csv

files = os.listdir("csv/")

data = []

raceIndex = 0
firstFile = True
for filename in files:
    with open("csv/"+filename) as f:
        index = 0
        reader = csv.reader(f)
        for row in reader:
            if index == 0:
                header = row
            if firstFile:
                if index == 3:
                    data.append(["Session ID",] + header + row)
                    firstFile = False
            if index == 1:
                raceInfo = row
            if index >= 3:
                if row[7] == playerName:
                    raceData = row
            index= index+1
    
    if not raceInfo[7] == "":
        data.append([filename] + raceInfo + raceData)
    raceIndex = raceIndex+1
#print(data)
    


# Import all libraries needed for the tutorial
import pandas as pd


df = pd.DataFrame(data = data[1:], columns=data[0])
print(df[:10])

df.to_csv("racer.csv")

