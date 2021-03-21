#!/usr/bin/python3

# Display various stats about the player exported previously

import pandas as pd
from numpy import random
import matplotlib.pyplot as plt
import sys
import matplotlib

df = pd.read_csv("racer.csv", index_col=0)

df.info()

# Display most used Car
print("Most used Car")
print(df["Car"].value_counts())
print()
print()

print("Most used tracks")
print(df["Track"].value_counts()[:10])
print()
print()

print("Average incident per race")
print(df["Inc"].mean())
print()
print()

# Calculate iRating gain
df["DiffIRating"] = (df["New iRating"]-df["Old iRating"])

test=df.groupby("Car")
print("Average incident per car per race")
print(test.mean()["Inc"].sort_values(ascending=False))
print()
print()

def get_sec(time_str):
    """Get Seconds from time."""
    if ":" in time_str:
        m, s = time_str.split(':')
        return int(m) * 60. + float(s)
    else:
        return float(time_str)
    
# Transform Average lap time to seconds
df["AvgLapTimeInSec"] = df["Average Lap Time"].apply(get_sec)

# Calculate each race length in seconds
df["RaceLength"] = df["Laps Comp"]*df["AvgLapTimeInSec"]

print("Total time spent in races")
print(df["RaceLength"].sum())
print(test["RaceLength"].sum())
print()
print()

print("Incidents per hour per car")
print( (test["Inc"].sum()*3600/test["RaceLength"].sum()).sort_values(ascending=False) )
print()
print()

# Create a python datetime index
df["Datetime"] = pd.to_datetime(df["Start Time"])
df.plot(x="Datetime", y="New iRating")
plt.show()

print("Irating gain per Car")
test.sum()["DiffIRating"].sort_values(ascending=False).plot(x="Car", y="DiffIRating", kind="bar")
plt.show()

