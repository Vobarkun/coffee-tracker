from flask import Flask, request, send_from_directory, render_template
import os, csv, datetime, string

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

datapath = "data.csv"
logpath = "coffee.log"
template = {"coffee": 0, "tea": 0, "milk": 0}

SPREADSHEET_ID = '1hAvLsZLNnDxm-8b3Dc5MyE6chK1kBngeLFIME7fcr9o'
RANGE_NAME = 'Sheet1!A1:E100'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


app = Flask(__name__, static_url_path="")
app.debug = True

@app.route("/")
def route_top():
    return send_from_directory("static", "index.html")

@app.route("/data.csv")
def route_data():
    return send_from_directory("", "data.csv")

@app.route("/<path:path>")
def route_static(path):
    return send_from_directory("static", path)

@app.route("/submit", methods = ["POST"])
def route_form():
    row = updateGoogleSheet(request.form)

    # parsed = parseForm(request.form)
    # name = request.form["name"] if "name" in request.form else "unknown"

    # row = updateData(data, name, parsed)
    # writeData(datapath, data)
    # with open(logpath, "a+") as fp:
    #     fp.write(str(datetime.datetime.now()) + " " + ": " + str(parsed) + "\n")
    if row:
        return render_template("response.html", message = "You now have:", message2 = f"Coffee: {row[1]}, Tea: {row[2]}, Milk: {50*row[3]+250*row[4]}ml")
    else:
        return render_template("response.html", message = "Name not found")


def parseForm(form):
    result = template.copy()
    for key in form:
        if key == "coffee1":
            result["coffee"] += 1
        elif key == "coffee2":
            result["coffee"] += 2
        elif key == "tea1":
            result["tea"] += 1
        elif key == "milk50":
            result["milk"] += 50
        elif key == "milk250":
            result["milk"] += 250
    return result

def updateData(data, name, parsed):
    if not name in data:
        data[name] = template.copy()
    for key, value in parsed.items():
        data[name][key] += value
    return data[name]


def loadData(path):
    if os.path.isfile(path):
        with open(path, "r") as fp:
            reader = csv.reader(fp, delimiter = ",", quotechar = '"')
            rows = [row for row in reader if len(row) > 1]
            fieldnames = rows.pop(0)

            return {row[0]: {f: int(r) for f, r in zip(fieldnames[1:], row[1:])} for row in rows}
    else:
        writeData(path, {})
    return {}

def writeData(path, data):
    with open(path, "w+") as fp:
        writer = csv.DictWriter(fp, delimiter=",", fieldnames = ["name"] + [key for key in template])
        writer.writeheader()
        for key, value in data.items():
            writer.writerow({"name": key, **value})

def updateGoogleSheet(form):
    name = request.form["name"]

    values = getGoogleSheetValues()
    names = [v[0] for v in values]

    column_Names = [v.lower() for v in values[0]]

    if name in names[1:]:
        index = names[1:].index(name) + 1
        row = values[index]

        for key in form:
            if key == "coffee1":
                row[column_Names.index("coffee")] += 1
            elif key == "coffee2":
                row[column_Names.index("coffee")] += 2
            elif key == "tea1":
                row[column_Names.index("tea")] += 1
            elif key == "milk50":
                row[column_Names.index("milk 50 ml")] += 1
            elif key == "milk250":
                row[column_Names.index("milk 250 ml")] += 1
        
        sheet.values().update(spreadsheetId=SPREADSHEET_ID, range = f"Sheet1!B{index+1}:E{index+1}", body={'values': [row[1:]]}, valueInputOption = "RAW").execute()
        return row
    else:
        return False


def getGoogleSheetValues():
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME, valueRenderOption="UNFORMATTED_VALUE").execute()
    values = result.get('values', [])
    for i in range(len(values)):
        if len(values[i]) == 0:
            values[i] = ["", 0, 0, 0, 0]
    return values

def getCreds():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


data = {}

creds = getCreds()

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

if __name__ == '__main__':
    data = loadData(datapath)
    app.run(host="0.0.0.0")
