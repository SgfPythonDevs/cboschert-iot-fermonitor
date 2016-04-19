from pymongo import MongoClient, DESCENDING
from bson.son import SON

COLL_NAME_TEMP_LOG = 'temp_log'


def farenheit_to_celcius(f_degrees):
    return (f_degrees - 32) / 1.8


def celcius_to_farenheit(c_degrees):
    return (c_degrees * 1.8) + 32


class DbRepo:
    def __init__(self, conn_string='mongodb://localhost:27017', db_name='pydev_demos'):
        self.client = MongoClient(conn_string)
        self.db = self.client[db_name]

    def __del__(self):
        self.db = None
        self.client.close()
        self.client = None

    def add_temp(self, when, where, temp_c, temp_f, humidity):
        col = self.db[COLL_NAME_TEMP_LOG]
        result = col.insert_one({
            "when": when,
            "where": where,
            "temp_c": temp_c,
            "temp_f": temp_f,
            "humidity": humidity
        })

        return result.inserted_id

    def get_locations(self):
        col = self.db[COLL_NAME_TEMP_LOG]
        cursor = col.aggregate([
            {"$group": {"_id": "$where",
                        "num_of_measures": { "$sum": 1 },
                        "most_recent": { "$max": "$when"}}}
            ])

        results = list(cursor)
                               
        return results
        

    def query_recent_temps(self, location, top_n=100):
        col = self.db[COLL_NAME_TEMP_LOG]
        cursor = col.find({'where': location}).sort("when", DESCENDING)

        if top_n:
            cursor = cursor.limit(top_n)

        results = list(cursor)

        return results

    def get_stats(self, location):
        # https://api.mongodb.org/python/current/examples/aggregation.html
        # https://docs.mongodb.org/manual/reference/operator/aggregation/
        col = self.db[COLL_NAME_TEMP_LOG]
        details = list(col.aggregate([
            {"$match": { "where": location}},
            {"$project": {"year": {"$year": "$when"},
                          "month": {"$month": "$when"},
                          "day": {"$dayOfMonth": "$when"},
                          "hour": {"$hour": "$when"},
                          "temp_c": 1, "temp_f": 1, "humidity": 1}},
            {"$group": {"_id": {"year": "$year", "month": "$month", "day": "$day", "hour": "$hour"},
                        "avg_c": {"$avg": "$temp_c"},
                        "avg_f": {"$avg": "$temp_f"},
                        "avg_rh": {"$avg": "$humidity"},
                        "num_of_measures": {"$sum": 1}}},
            {"$sort": SON([("_id.year", -1), ("_id.month", -1), ("_id.day", -1), ("_id.hour", -1)])},
            {"$limit": 168}
        ]))

        most_recent = col.find({'where': location}).sort("when", DESCENDING).limit(1)[0]

        return {
            "most_recent": most_recent,
            "details": details
        }

