import os
import math
from datetime import datetime
from flask import Flask, redirect, url_for, request, render_template, session, jsonify, flash
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import arrow
import acp_times
import config
import logging

app = Flask(__name__)

client = MongoClient(os.environ.get('DB_PORT_27017_TCP_ADDR', 'db'), 27017)
db = client.brevetdb

CONFIG = config.configuration()
app.secret_key = CONFIG.SECRET_KEY

###
# Pages
###


@app.route("/")
def index():
    app.logger.debug("Main page entry")
    return render_template('calc.html')


@app.route("/controls")
def display_controls():
    controls = list(db.controls.find({}, {"_id": False}))
    return render_template("controls.html", controls=controls, error=None)


@app.route("/submit", methods=["POST"])
def submit_controls():
    brevet_distance = request.form.get("distance", type=int)
    if brevet_distance not in acp_times.VALID_DISTANCES:
        flash("Select a valid brevet distance.")
        return redirect(url_for("index"))

    begin_date = request.form.get("begin_date", "")
    begin_time = request.form.get("begin_time", "")
    datetime.strptime("{} {}".format(begin_date, begin_time), "%Y-%m-%d %H:%M")
    brevet_start = "{}T{}-00:00".format(begin_date, begin_time)

    miles_values = request.form.getlist("miles")
    km_values = request.form.getlist("km")
    locations = request.form.getlist("location")
    if not (len(miles_values) == len(km_values) == len(locations)):
        flash("Control row data is incomplete.")
        return redirect(url_for("index"))
    documents = []

    for miles, km, location in zip(miles_values, km_values, locations):
        if not km.strip():
            continue
        control_km = float(km)
        if not math.isfinite(control_km) or not 0 <= control_km:
            flash("Control distances must be a nonnegative number.")
            return redirect(url_for("index"))

        open_time = acp_times.open_time(control_km, brevet_distance, brevet_start)
        close_time = acp_times.close_time(control_km, brevet_distance, brevet_start)
        document = {
            "brevet_distance": brevet_distance,
            "begin_date": begin_date,
            "begin_time": begin_time,
            "km": control_km,
            "location": location.strip(),
            "open": open_time,
            "close": close_time,
        }
        if miles.strip():
            control_miles = float(miles)
            if not math.isfinite(control_miles) or control_miles <= 0:
                flash("Miles must be a nonnegative number.")
                return redirect(url_for("index"))
            document["miles"] = control_miles
        documents.append(document)

    if not documents:
        flash("Enter at least one control distance before submitting.")
        return redirect(url_for("index"))

    db.controls.insert_many(documents)

    flash("Saved {} control time(s) to the database.".format(len(documents)))
    return redirect(url_for("index"))


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    session['linkback'] = url_for("index")
    return render_template('404.html'), 404


###############
#
# AJAX request handlers
#   These return JSON, rather than rendering pages.
#
###############
@app.route("/_calc_times")
def _calc_times():
    """
    Calculates open/close times from miles, using rules
    described at https://rusa.org/octime_alg.html.
    Expects one URL-encoded argument, the number of miles.
    """
    app.logger.debug("Got a JSON request")
    km = request.args.get('km', 999, type=float)
    brevet_distance = request.args.get('brevet_distance', 200, type=int)
    begin_date = request.args.get('begin_date', type=str)
    begin_time = request.args.get('begin_time', type=str)
    app.logger.debug("km={}".format(km))
    app.logger.debug("request.args: {}".format(request.args))
    open_time = acp_times.open_time(km, brevet_distance, begin_date + "T" + begin_time + "-00:00")
    close_time = acp_times.close_time(km, brevet_distance, begin_date + "T" + begin_time + "-00:00")
    result = {"open": open_time, "close": close_time}
    return jsonify(result=result)


#############

app.debug = CONFIG.DEBUG
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    print("Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=CONFIG.PORT, host="0.0.0.0")
