from datetime import datetime
import json

class TimestampEncoder(json.JSONEncoder):
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%s %s" % (self.DATE_FORMAT, 
                                           self.TIME_FORMAT))

        return super(TimestampEncoder, self).default(obj)

class DataLog():

    def __init__(self, gas, temperature=None, humidity=None, pressure=None):
        self.gas = gas
        self.temperature = temperature
        self.humidity = humidity
        self.pressure = pressure
        
