from pymongo import MongoClient, DESCENDING
from bson.son import SON

COLL_NAME_TEMP_LOG = 'temp_log'
COLL_NAME_CONFIG = 'config'


def fahrenheit_to_celsius(f_degrees):
    return (f_degrees - 32) / 1.8


def celsius_to_fahrenheit(c_degrees):
    return (c_degrees * 1.8) + 32


class DbRepo:
    """Provides a simple facade to our database."""
    def __init__(self, conn_string='mongodb://localhost:27017', db_name='pydev_demos'):
        # Establis class level connection to the MongoDB instance and database
        self.client = MongoClient(conn_string)
        self.db = self.client[db_name]

    def __del__(self):
        # Release DB connection when no longer needed
        self.db = None
        self.client.close()
        self.client = None

    def set_target_temp(self, temp_c):
        col = self.db[COLL_NAME_CONFIG]

        if temp_c:
            result = col.update({"_id": "target_temp"}, {"_id": "target_temp", "value": temp_c}, upsert=True)
            return result.n == 1
        else:
            result = col.remove("target_temp")
            return True

    def get_target_temp(self):
        col = self.db[COLL_NAME_CONFIG]
        target = col.find_one("target_temp")
        if target:
            return target["value"]

        return None

    def add_measurement(self, when, where, temp_c, temp_f, humidity):
        """Writes a single temperature and humidity reading to the DB."""
        # In MongoDB collections are similar to tables in relational DBs.
        # We need get a reference to the collection before performing operations
        # on it.
        col = self.db[COLL_NAME_TEMP_LOG]

        # No need to define a schema for your collection, just start writing
        # documents to it!
        result = col.insert_one({
            "when": when,
            "where": where,
            "temp_c": temp_c,
            "temp_f": temp_f,
            "humidity": humidity
        })

        # Most operations return some sort of results
        return result.inserted_id

    def query_recent_measurements(self, location, top_n=100):
        """Returns the most recent measurements from the DB for the requested location."""
        col = self.db[COLL_NAME_TEMP_LOG]

        # Build a query to find the most recent measurements. The query isn't
        # actually executed until we iterate over the returned cursor instance...
        cursor = col.find({'where': location}).sort("when", DESCENDING)

        # ...this allows us to append additional operations to the cursor before
        # executing the query.
        if top_n:
            cursor = cursor.limit(top_n)

        # list() will iterator over the cursor causing the query to be executed
        # and results returned to the client.
        results = list(cursor)

        return results

    def get_locations(self):
        """Measurements are taken for locations (where attribute.) This
        function returns all the locations in the database with basic stats."""
        col = self.db[COLL_NAME_TEMP_LOG]

        # MongoDB has a powerful data aggregation pipeline for calculating
        # statistics. Here we're aggregating measurements by location (where.)
        cursor = col.aggregate([
            {"$group": {"_id": "$where",
                        "num_of_measures": { "$sum": 1 },
                        "most_recent": { "$max": "$when"}}}
            ])

        results = list(cursor)

        return results

    def get_stats(self, location):
        """Returns hourly statistics for a requested location (where.)"""

        # Helpful documentation for aggregation
        # https://api.mongodb.org/python/current/examples/aggregation.html
        # https://docs.mongodb.org/manual/reference/operator/aggregation/

        col = self.db[COLL_NAME_TEMP_LOG]

        # Notice the data pipeline provided by MongoDB's aggregation engine. Results
        # from one step feed into the next and so on through the pipeline.
        details = list(col.aggregate([
            # $match will filter documents
            {"$match": { "where": location}},
            # $project transforms the document, creating new attributes or
            # filtering out unnecessary attributes.
            {"$project": {"year": {"$year": "$when"},
                          "month": {"$month": "$when"},
                          "day": {"$dayOfMonth": "$when"},
                          "hour": {"$hour": "$when"},
                          "temp_c": 1, "temp_f": 1, "humidity": 1}},
            # $group will perform calculations for the specified key's granularity.
            {"$group": {"_id": {"year": "$year", "month": "$month", "day": "$day", "hour": "$hour"},
                        "avg_c": {"$avg": "$temp_c"},
                        "avg_f": {"$avg": "$temp_f"},
                        "avg_rh": {"$avg": "$humidity"},
                        "num_of_measures": {"$sum": 1}}},
            # Sort the results. In python, use SON() for sorting because Python
            # dictionaries are unordered.
            {"$sort": SON([("_id.year", -1), ("_id.month", -1), ("_id.day", -1), ("_id.hour", -1)])},
            # Lastly we limit to the most recent 168 hours of readings (7 days.)
            {"$limit": 168}
        ]))

        # Grab the most recent reading as well
        most_recent = col.find({'where': location}).sort("when", DESCENDING).limit(1)[0]

        return {
            "most_recent": most_recent,
            "details": details
        }
