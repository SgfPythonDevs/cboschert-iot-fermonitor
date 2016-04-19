#!/usr/bin/python
import argparse
import json
from datetime import datetime

from bson import objectid
from common import DbRepo
from flask import Flask, render_template

'''In a production solution, you will not want to use the development
   web server. You may want authentication as well. Check out these links
   for more information'''
# Host in Tornado: http://hilpisch.com/rpi/03_web_apps.html
# Basic Auth: http://flask.pocoo.org/snippets/8/

# The Flask class is a WSGI application
app = Flask(__name__)


class CustomEncoder(json.JSONEncoder):
    """A C{json.JSONEncoder} subclass to encode documents that have fields of
    type C{bson.objectid.ObjectId}, C{datetime.datetime}"""
    def default(self, obj):
        if isinstance(obj, objectid.ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


# app.route() decorator routes requests for a URL to a Python function
@app.route('/')
def index():
    repo = DbRepo()
    locs = repo.get_locations()

    # Quick dev - just string together some anchor tags; most browsers won't complain.
    # Don't do this in the real world.
    bein_lazy = ['<a href="./dashboard/{0}">{0}</a> - {1} measurements, last on {2}'.format(x["_id"], x["num_of_measures"], x['most_recent']) for x in locs]
    
    return '<br />'.join(bein_lazy), 200


# Example of providing default rounds
@app.route('/recent/<where>', defaults={'max': 10})
@app.route('/recent/<where>/<int:max>')
def recent(where, max):
    repo = DbRepo()
    results = repo.query_recent_measurements(where, max)
    enc = CustomEncoder()

    # Return the results as JSON
    return enc.encode(results), 200, {'Content-Type': 'text/json; charset=utf-8'}


@app.route('/stats/<where>')
def stats(where):
    repo = DbRepo()
    results = repo.get_stats(where)
    enc = CustomEncoder()

    return enc.encode(results), 200, {'Content-Type': 'text/json; charset=utf-8'}


@app.route('/dashboard/<where>')
def dashboard(where):
    """Flask can actually serve web pages too. It uses Jinja2 templates"""
    # http://flask.pocoo.org/docs/0.10/tutorial/templates/
    repo = DbRepo()
    results = repo.get_stats(where)
    enc = CustomEncoder()

    return render_template('dashboard.html', ctx=results)


if __name__ == '__main__':
    # Parse command line arguments to get server settings
    parser = argparse.ArgumentParser(
        description="Starts the Fermonitor API",
        prog="api.py")
    parser.add_argument('--d', '--debug', help='Launches API web server in debug mode. DEFAULT %(default)s', default=False, action='store_true')

    args = parser.parse_args()

    # Start the Flask web server; host='0.0.0.0' exposes the endpoints externally.
    app.run(host='0.0.0.0', debug=args.d)
