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

result_url = "https://members.iracing.com/memberstats/member/GetResults"
result_page_url="https://members.iracing.com/membersite/member/results.jsp"

def save_file(filename, obj):
    file = open(filename, "w+")
    file.write(obj)
    file.close()

browser = mechanicalsoup.StatefulBrowser(
   soup_config={'features': 'lxml'},
   raise_on_404=True,
   user_agent='MechanicalSoup User Agent',
   )
   
browser.open(result_page_url)
browser.select_form()
browser.form.set("username", username)
browser.form.set("password", password)

resp = browser.submit_selected()

starttime_high=str(int(time.time())*1000)

result_list_url = "https://members.iracing.com/memberstats/member/GetResults?custid=" + str(custid) + "&showraces=1&showquals=1&showtts=1&showops=1&showofficial=1&showunofficial=0&showrookie=1&showclassd=1&showclassc=1&showclassb=1&showclassa=1&showpro=1&showprowc=1&lowerbound=" + str(lowerbound) + "&upperbound=" + str(upperbound) + "&sort=start_time&order=desc&format=json&category%5B%5D=1&category%5B%5D=2&category%5B%5D=3&category%5B%5D=4&starttime_low="+ starttime_low +"&starttime_high=" + starttime_high

page = browser.open(result_list_url)
save_file("page"+str(lowerbound), page.text)

if not os.path.exists("csv"):
    os.makedirs("csv")

data = json.loads(page.text)
session_ids = []
for id in data["d"]["r"]:
    session = str(id["41"])
    session_ids.append(session)
    
    #session = session_ids[0]
    session_url = "https://members.iracing.com/membersite/member/GetEventResultsAsCSV?subsessionid=" + str(session) + "&simsesnum=0&includeSummary=1"

    res = browser.open(session_url)
    save_file(os.path.join("csv","session-"+str(session)), res.text)
   
save_file("session_ids", '\n'.join(session_ids))


