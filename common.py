from pymongo import MongoClient, DESCENDING

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

    def query_recent_temps(self, location, top_n=100):
        col = self.db[COLL_NAME_TEMP_LOG]
        cursor = col.find({'where': location}).sort("when", DESCENDING)

        if top_n:
            cursor = cursor.limit(top_n)

        results = list(cursor)

        return results