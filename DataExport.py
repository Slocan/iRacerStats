#!/usr/bin/python3

########## Manual Configuration #############3

# Username/Password to login to the interface
username = "<username>"
password = "<password>"

# The iRacing ID number
custid = "000000"

# Unix timestamp (*1000) for the start date to download
starttime_low= "1467356400000"

# To skip downloading the first races
lowerbound = 0
# Limit to the number of races to download
upperbound = 2000



###############


import mechanicalsoup
import json
import os
import time
import csv
import sys
import time
import pandas as pd
import math
import matplotlib.pyplot as plt

browser = mechanicalsoup.StatefulBrowser(
   soup_config={'features': 'lxml'},
   raise_on_404=True,
   user_agent='MechanicalSoup User Agent',
   )

result_url = "https://members.iracing.com/memberstats/member/GetResults"
result_page_url="https://members.iracing.com/membersite/member/results.jsp"
session_url = "https://members.iracing.com/membersite/member/GetEventResultsAsCSV?subsessionid={0}&simsesnum=0&includeSummary=1"  # Replace with session id
# Replace with season ID and race week
result_list_url = "https://members.iracing.com/memberstats/member/GetResults?custid={0}&showraces=1&showquals=1&showtts=1&showops=1&showofficial=1&showunofficial=0&showrookie=1&showclassd=1&showclassc=1&showclassb=1&showclassa=1&showpro=1&showprowc=1&lowerbound={1}&upperbound={2}&sort=start_time&order=desc&format=json&category%5B%5D=1&category%5B%5D=2&category%5B%5D=3&category%5B%5D=4&starttime_low={3}&starttime_high={4}"
series_race_results_url = "https://members.iracing.com/memberstats/member/GetSeriesRaceResults?seasonid={0}&raceweek={1}&invokedBy=SeriesRaceResults" 
subsession_result_url = "http://members.iracing.com/membersite/member/GetSubsessionResults?&subsessionID={0}&custid=0"

# Helper function
# Save file
def save_file(filename, obj):
    file = open(filename, "w+")
    file.write(obj)
    file.close()

# Helper function
# Login to the website
def login():
   browser.open(result_page_url)
   browser.select_form()
   browser.form.set("username", username)
   browser.form.set("password", password)
   resp = browser.submit_selected()
   if ("Authentication Failed" in resp.text):
        print("Invalid login")
        sys.exit(1)

# Helper function
# Download a specific session result, and saves it in a subfolder
def downloadSessionResults(sessionid, folder):
    # Download the session data info
    res = browser.get(subsession_result_url.format(sessionid))
    save_file(os.path.join(folder,"session-"+str(sessionid)+".json"), res.text)
    
    # Download the session race results
    res = browser.open(session_url.format(sessionid))
    save_file(os.path.join(folder,"session-"+str(sessionid)+".csv"), res.text)

# Helper function
# Transforms the lap time string into seconds
# Example: df["AvgLapTimeInSec"] = df["Average Lap Time"].apply(get_sec)
def get_sec(time_str):
    """Get Seconds from time."""
    if type(time_str) == float:
        return 0
    elif ":" in time_str:
        m, s = time_str.split(':')
        return int(m) * 60. + float(s)
    else:
        return float(time_str)

# Download all the results for a specific player
def getPlayerResults():
    # All the results between starttime_low and starttime_high
    starttime_high=str(int(time.time())*1000)

    url = result_list_url.format(str(custid), str(lowerbound), str(upperbound), str(starttime_low), str(starttime_high))

    page = browser.open(result_list_url)
    save_file("page"+str(lowerbound), page.text)

    if not os.path.exists("csv"):
        os.makedirs("csv")

    data = json.loads(page.text)
    session_ids = []
    # Parse the list, and downloads the corresponding result files
    for id in data["d"]["r"]:
        session = str(id["41"])
        session_ids.append(session)
        
        #session = session_ids[0]
        downloadSessionResults(session, "csv")
    
    # Save the session IDs, just in case
    save_file("player_session_ids", '\n'.join(session_ids))
    
# Download all the session files for a specific series seson and week (each series has a different id for the season)
def downloadSeriesResults(seriesSeason,week):
    ##(3123,1)
    url = series_race_results_url.format(seriesSeason, str(week))
    page = browser.open(url)
    data = json.loads(page.text)

    if not os.path.exists(str(seriesSeason)):
        os.makedirs(str(seriesSeason))

    # Parse the json result. 
    for session in data["d"]:
        # Grab the subsession id
        sessionid = session["5"]
        # Check if the file already exists, and skip if needed
        if not os.path.exists(os.path.join(str(seriesSeason),"session-"+str(sessionid)+".csv")):
            # Sleep for a little bit to not spam too much
            time.sleep(0.3)
            downloadSessionResults(sessionid, str(seriesSeason))
            

# Process the data for a series after downloading
def processSeriesResults(seriesSeason):
    # List all the files for a series in the subfolder
    files = os.listdir(seriesSeason)
    files = list(filter(lambda f: f.endswith('.csv'), files))

    data = []
    firstFile = True
    
    # Go through all the file
    for filename in files:
        jsonFilename = filename.replace(".csv",".json")
        with open(os.path.join(str(seriesSeason),jsonFilename)) as json_file:
            json_data = json.load(json_file)
            session_data = ( ["weather_temp_value", "weather_wind_speed_value","weather_wind_dir", "weather_type"], [json_data["weather_temp_value"], json_data["weather_wind_speed_value"], json_data["weather_wind_dir"], json_data["weather_type"] ] )
        
        with open(os.path.join(str(seriesSeason),filename)) as f:
            index = 0
            reader = csv.reader(f)
            for row in reader:
                # First row in file is the header
                if index == 0:
                    header = row
                # If this is the first file we're reading, record the column names
                # Other files should have the same format
                if firstFile:
                    if index == 3:
                        print(session_data[0], header)
                        data.append(["Session ID",] + header + row + session_data[0])
                        firstFile = False
                # 2nd line of the file contains the race information
                if index == 1:
                    raceInfo = row
                # After the first 4 lines, we're finally recording the results, one line per player
                if index > 3:
                    raceData = row
                    data.append([filename] + raceInfo + raceData + session_data[1])
                index= index+1
        
    # Save all the races to a csv file
    df = pd.DataFrame(data = data[1:], columns=data[0])
    df.to_csv(seriesSeason+".csv")


   
login()
downloadSeriesResults("3135","1")

#getPlayerResults()
#downloadSeriesResults("3154","0")
#processSeriesResults("3154")

# Useful data queries
# df = pd.read_csv("3154.csv")
# dg = df[df['Race Week'] == 1]
# df["FastestLapTimeInSec"] = df["Fastest Lap Time"].apply(get_sec)
# df["FastestLapTimeInSec"] = df["Fastest Lap Time"].apply(get_sec)

# Show the Fastest lap time vs temperature:
#df_filt = df[ df["FastestLapTimeInSec"] != 0  ]
#df1 = df_filt.groupby("Session ID")["FastestLapTimeInSec"].min()
#df1 = pd.DataFrame(df1, columns = ["FastestLapTimeInSec"])
#merged = pd.merge(df, df1, on = ["Session ID", "FastestLapTimeInSec"])
#merged.plot(x="weather_temp_value", y="FastestLapTimeInSec")
#merged.plot.scatter(x="weather_temp_value", y="FastestLapTimeInSec", c="Old iRating", colormap='viridis')
#sns.lmplot(x="weather_temp_value", y="FastestLapTimeInSec", data=merged, aspect=2)

# Create new column for irating below and over 1600
#df["lowRating"] = df["Old iRating"] <= 1600
#sns.lmplot(x="weather_temp_value", y="FastestLapTimeInSec", data=merged, hue="lowRating", aspect=2)

# Sort values into bins:
#merged["iRatingBins"] = pd.cut(merged["Old iRating"],bins=4)
#sns.lmplot(x="weather_temp_value", y="FastestLapTimeInSec", data=merged, hue="iRatingBins", aspect=2)
#plt.show()

#>>> df["iRatingBins"] = pd.cut(df["Old iRating"],bins=[0,1000,1350,1600,2000,3000,5000,10000])
#>>> df["iRating"] = df["iRatingBins"].apply(str)
#>>> df["iRating"].unique()
#['(1600, 2000]', '(2000, 3000]', '(1350, 1600]', '(1000, 1350]', '(0, 1000]', '(5000, 10000]', '(3000, 5000]']
#Categories (7, object): ['(0, 1000]' < '(1000, 1350]' < '(1350, 1600]' < '(1600, 2000]' <
                         #'(2000, 3000]' < '(3000, 5000]' < '(5000, 10000]']
#>>> dg = df[ df["FastestLapTimeInSec"] > 0 ]
#>>> mint = dg.groupby(["Car", "iRating"])
#>>> dh = mint["FastestLapTimeInSec"].min().reset_index()
#>>> sns.scatterplot(data=dh, hue="Car", y="FastestLapTimeInSec", x="iRating")
#<AxesSubplot:xlabel='iRating', ylabel='FastestLapTimeInSec'>
#>>> plt.show()

#>>> df["iRatingBins"] = pd.cut(df["Old iRating"],bins=40])
#dg = df[ df["FastestLapTimeInSec"] > 0 ]
#df["iRating"] = df["iRatingBins"].apply(lambda x: x.right)
# mint = dg.groupby(["Car", "iRating"]).apply(lambda x: x.sort_values(by='FastestLapTimeInSec', ascending=True).head(3)) 
#sns.lmplot(data=dh, hue="Car", y="FastestLapTimeInSec", x="iRating", scatter=False, lowess=True)
#sns.boxplot(data=dg, hue="Car", y="FastestLapTimeInSec", x="iRating")

# Show the slope for each iRating bin
#>>> for bin in dg["iRating"].unique():
#...    tmp = dg[ dg["iRating"] == bin ]
#...    slope, intercept, r_value, pv, se = stats.linregress(tmp["weather_temp_value"],tmp["FastestLapTimeInSec"])
#...    print("Bin: ", bin, slope, intercept)
