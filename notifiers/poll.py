import smtplib
from email.mime.text import MIMEText
import json
import requests
from datetime import datetime, timedelta
import time
import sys


last_email_send_time=datetime.utcnow() - timedelta(800)
throttle=timedelta(0,600)
EMAIL_KEY_FILE="/var/lib/global-entry/email.key"
EMAIL_KEY=""

def readEmailKey():
    global EMAIL_KEY
    with open(EMAIL_KEY_FILE, "r") as fd:
        EMAIL_KEY = fd.readline().strip()
    
def sendEMail(data):
    global last_email_send_time

    # Send email at most once every 10 minutes
    if (last_email_send_time + throttle) > datetime.utcnow():
        print("too early to send another email....")
        return

    msg = MIMEText("Hello,\n\nThere is a global entry appointment available at Boston Logan. Hurry!!\n\nappt date: {}".format(str(data[0]["startTimestamp"])))

    msg['Subject'] = 'Available Global Entry Appt'
    msg['From'] = 'noreply@helmsdeep.com'
    msg['To'] = 'timbouvier1@gmail.com'

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login('helmsdeep011@gmail.com', EMAIL_KEY)
    server.sendmail('noreply@helmsdeep.com', 'timbouvier1@gmail.com', msg.as_string())
    server.close()
    last_email_send_time = datetime.utcnow()

def checkFOrAppts():
    global count
    url = "https://ttp.cbp.dhs.gov/schedulerapi/slots?orderBy=soonest&limit=1&locationId=5441&minimum=1"
    response = requests.get(url)
    data = response.json()
    print(response.text)
    print(str(len(data)))
    if (len(data) > 0):
        sendEMail(data)


readEmailKey()
thedate = datetime.utcnow()
delta = timedelta(0,20)

for i in range(0,6000):
    time.sleep(10)
    now = datetime.utcnow()

    # poll once every 20 seconds
    if (thedate+delta < now):
        thedate = datetime.utcnow()
        try:
            checkFOrAppts()
        except:
            print("Caught exception checking for appts...")


