from flask import Flask, request, send_from_directory, render_template
import os, csv, datetime, string

datapath = "data.csv"
logpath = "coffee.log"
template = {"coffee": 0, "tea": 0, "milk": 0}

app = Flask(__name__, static_url_path="")
app.debug = True

@app.route("/")
def top():
    return send_from_directory("static", "index.html")

@app.route("/data.csv")
def route_data():
    return send_from_directory("", "data.csv")

@app.route("/<path:path>")
def func(path):
    return send_from_directory("static", path)

@app.route("/submit", methods = ["POST"])
def route_form():
    parsed = parseForm(request.form)
    name = request.form["name"] if "name" in request.form else "unknown"
    name = name.translate(str.maketrans('', '', string.punctuation))
    row = updateData(data, name, parsed)
    writeData(datapath, data)
    with open(logpath, "a+") as fp:
        fp.write(str(datetime.datetime.now()) + " " + name + ": " + str(parsed) + "\n")
    return render_template("response.html", **row)


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


data = {}

if __name__ == '__main__':
    data = loadData(datapath)
    app.run(host="0.0.0.0")