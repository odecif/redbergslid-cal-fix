from flask import Flask, send_file, request  # notera request requests skillnad
import requests
from datetime import date, datetime, timedelta
from icalendar import Calendar
from io import BytesIO
from bs4 import BeautifulSoup
from urllib.request import urlopen
app = Flask(__name__)


# Basfunktion för att hämta kalendersidan inför parsening
def getSite(url="https://redbergslid.scout.se/kalender/lista/?"):
    page = urlopen(url)
    html = page.read().decode("utf-8")
    return BeautifulSoup(html, "html.parser")


# Hämta alla kalendertyper/avdelningar för kåren
def getDepartmentsList():
    soup = getSite()
    avdelningar = []
    for line in soup.find_all("span", {"class": "js-event-section"}):
        avdelning = [line.string, line["data-slug"]]
        avdelningar.append(avdelning)

    return avdelningar


# Hämta alla högre kalendar (kår, distrikt, nationell)
def getCategories():
    soup = getSite()
    organlista = []
    for line in soup.find_all("span", {"class": "js-event-category"}):
        organ = [line.string, line["data-slug"]]
        organlista.append(organ)

    return organlista


def getAllCal(avdelning=0, tribe_event_category="scout",
              api="https://redbergslid.scout.se/kalender/lista/?"):
    parameters = {
        "tribe_event_category": tribe_event_category,
        "event-section": avdelning,
        "tribe-bar-date": '1907-08-1',
        "ical": 0
    }
    calendars = []
    currentdate = last_date = date.today()
    date1, date2 = currentdate, currentdate+timedelta(days=1)
    while date1 < date2:
        r = requests.get(api, params=parameters)
        cal = Calendar.from_ical(r.text)
        for component in cal.walk():
            if component.name == 'VEVENT':
                last_date = component.get('dtstart').dt
        if isinstance(last_date, datetime):
            last_date = last_date.date()
        date1 = date2
        date2 = last_date
        parameters['tribe-bar-date'] = last_date.strftime("%Y-%m-%d")
        calendars.append(cal)
    for parts in calendars[1:-1]:
        calendars[0].subcomponents.extend(parts.subcomponents[2:])
    return calendars[0].to_ical()


@app.route("/")
def index():
    base = request.url_root
    return_object = [
        """<body><header>
            <div class="container">
                <h1 class="logo">Avdelningskalendrar</h1>
                <p>Klicka för att ladda ned fil,
                kopiera länkadress för att prenumerera på kalendern</p>
                <strong><nav>
                    <ul class="menu">
        """]
    for avdelning in getDepartmentsList():
        return_object.append(
                ''.join(["<li><a href=\"", base, "avd/", avdelning[1], "\">",
                        avdelning[0], "</a></li>"]))

    return_object.append("</ul></nav></strong></div>")

    return_object.append(
            ''.join("""<div class="container">
                <h1 class="logo">Andra kalendrar</h1>
                <p>OBS! Nationella kalendern fungerar ej!</p>
                <strong><nav>
                    <ul class="menu">
            """))
    for category in getCategories():
        return_object.append(
                ''.join(["<li><a href=\"", base, "cat/", category[1], "\">",
                        category[0], "</a></li>"]))

    return_object.append("</nav></strong></div>")

    return_object.append("</headers></body>")

    return ''.join(return_object)


@app.route("/avd/<avdelning>")
def giveAvdFile(avdelning):
    calFile = BytesIO(getAllCal(avdelning))
    calFile.seek(0)
    return send_file(
            calFile, attachment_filename='redbergslid.ics', as_attachment=True)


@app.route("/cat/<category>")
def giveCatFile(category):
    api = "https://redbergslid.scout.se/kalender/lista/?"
    if category == "district":
        api = "https://www.gbgscout.se/kalender/lista/?"
    # TODO: Nationella kalendern är i gamla formatet och kan inte exporteras
    # på samma vis som de andra kalendrarna.
    elif category == "national":
        api = "http://scoutservice.se/kalendarium"
    calFile = BytesIO(getAllCal(0, category, api))
    calFile.seek(0)
    return send_file(
            calFile, attachment_filename='redbergslid.ics', as_attachment=True)


# Nedan för att testa på localhost
# if __name__ == "__main__":
#     app.run(host="127.0.0.1", port=8080, debug=True)
