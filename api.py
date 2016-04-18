#!/usr/bin/python
import argparse
import json
from datetime import datetime

from bson import objectid
from common import celcius_to_farenheit
from common import DbRepo
from flask import Flask, render_template

# Host in Tornado: http://hilpisch.com/rpi/03_web_apps.html
# Basic Auth: http://flask.pocoo.org/snippets/8/

app = Flask(__name__)

class CustomEncoder(json.JSONEncoder):
    """A C{json.JSONEncoder} subclass to encode documents that have fields of
    type C{bson.objectid.ObjectId}, C{datetime.datetime}
    """
    def default(self, obj):
        if isinstance(obj, objectid.ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


@app.route('/')
def index():
    return '<a href="./recent/random/5">Go to API</a>', 200


@app.route('/recent/<where>', defaults={'max': 10})
@app.route('/recent/<where>/<int:max>')
def recent(where, max):
    # Power Query (M) sample query for charting in Excel
    '''let
    Source = Json.Document(Web.Contents("http://127.0.0.1:5000/recent/random/100")),
    #"Converted to Table" = Table.FromList(Source, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    #"Expanded Column1" = Table.ExpandRecordColumn(#"Converted to Table", "Column1", {"temp_f", "when"}, {"temp_f", "when"}),
    #"Sorted Rows" = Table.Sort(#"Expanded Column1",{{"when", Order.Ascending}}),
    #"Reordered Columns" = Table.ReorderColumns(#"Sorted Rows",{"when", "temp_f"}),
    #"Changed Type" = Table.TransformColumnTypes(#"Reordered Columns",{{"when", type datetime}, {"temp_f", type number}})
in
    #"Changed Type"'''

    repo = DbRepo()
    results = repo.query_recent_temps(where, max)
    enc = CustomEncoder()

    return enc.encode(results), 200, {'Content-Type': 'text/json; charset=utf-8'}


@app.route('/dashboard/<where>')
def dashboard(where):
    # http://flask.pocoo.org/docs/0.10/tutorial/templates/
    repo = DbRepo()
    results = repo.get_stats(where)
    enc = CustomEncoder()

    #return enc.encode(results), 200, {'Content-Type': 'text/json; charset=utf-8'}
    return render_template('dashboard.html', ctx=results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Starts the Fermonitor API",
        prog="api.py")
    parser.add_argument('--d', '--debug', help='Launches API web server in debug mode. DEFAULT %(default)s', default=False, action='store_true')

    args = parser.parse_args()

    app.run(host='0.0.0.0', debug=args.d)