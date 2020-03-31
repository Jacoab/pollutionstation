import json
import datetime

class DataLogEncoder(json.JSONEncoder):
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def __init__(self, config):
        self.config = config

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return {
                "timestamp": obj.strftime("%s %s" % (
                    self.DATE_FORMAT, self.TIME_FORMAT
                )),
                "username": config.username

            }

        return super(DataLogEncoder, self).default(obj)


#class DataLogDecoder(json.JSONDecoder):


