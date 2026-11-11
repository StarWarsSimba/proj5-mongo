import os
from flask import Flask, redirect, url_for, request, render_template, session, jsonify
from pymongo import MongoClient
import arrow
import acp_times
import config
import logging

app = Flask(__name__)

client = MongoClient(os.environ.get('DB_PORT_27017_TCP_ADDR', 'db'), 27017)
db = client.tododb

CONFIG = config.configuration()
app.secret_key = CONFIG.SECRET_KEY

###
# Pages
###


@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Main page entry")
    return render_template('calc.html')


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
    print(begin_date, begin_time, arrow.now().isoformat())
    app.logger.debug("request.args: {}".format(request.args))
    # FIXME: These probably aren't the right open and close times
    # and brevets may be longer than 200km
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
