from flask import Flask,send_file,request
import requests,tempfile, os
from datetime import date,datetime,timedelta
from icalendar import Calendar, Event
from io import BytesIO
app = Flask(__name__)

def getAllCal(avdelning=0):
    api="https://redbergslid.scout.se/kalender/lista/?"
    parameters = {
    "tribe_event_category":"scout",
    "event-section":0,
    "tribe-bar-date":'1907-08-1',
    "ical":0
    }
    if avdelning!=0:
        parameters["event-section"]=avdelning
    calendars=[]
    currentdate=last_date=date.today()
    date1,date2=currentdate,currentdate+timedelta(days=1)
    while date1 < date2:
        r=requests.get(api,params=parameters)
        cal=Calendar.from_ical(r.text)
        for component in cal.walk():
            if component.name == 'VEVENT':
                last_date=component.get('dtstart').dt
        if isinstance(last_date,datetime):
            last_date=last_date.date()
        date1=date2
        date2=last_date
        parameters['tribe-bar-date']=last_date.strftime("%Y-%m-%d")
        calendars.append(cal)
    for parts in calendars[1:-1]:
        calendars[0].subcomponents.extend(parts.subcomponents[2:])
    return calendars[0].to_ical()

@app.route("/")
def index():
    base=request.url_root
    return ''.join((
        """<body><header>
                <div class="container">
                    <h1 class="logo">Kalendrar</h1>
                    <p>Klicka för att ladda ned fil, kopiera länkadress för att prenumerera på kalendern</p>
                    <strong><nav>
                        <ul class="menu">
                            <li><a href=\"""",base,'0',"""\">Hela Kalendern</a></li>
                            <li><a href=\"""",base,'sparare',"""\">Spårare</a></li>
                            <li><a href=\"""",base,'upptackare',"""\">Upptäckare</a></li>
                            <li><a href=\"""",base,'aventyrare',"""\">Äventyrare</a></li>
                            <li><a href=\"""",base,'utmanare',"""\">Utmanare</a></li>
                            <li><a href=\"""",base,'rover',"""\">Rover</a></li>
                            <li><a href=\"""",base,'ledare-funktionar',"""\">Funktionär</a></li>
                            <li><a href=\"""",base,'styrelse',"""\">Styrelse</a></li>
                        </ul>
                    </nav></strong>
                </div>
                </header>
            </body>"""
    ))

@app.route("/<avdelning>")
def giveFile(avdelning):
    calFile = BytesIO(getAllCal(avdelning))
    calFile.seek(0)
    return send_file(calFile,attachment_filename='redbergslid.ics', as_attachment=True)