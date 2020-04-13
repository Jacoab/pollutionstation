from datetime import datetime
import json

class DataLog():
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def __init__(self, gas, temperature=None, humidity=None,
                 pressure=None):
        self.gas = gas
        self.temperature = temperature
        self.humidity = humidity
        self.pressure = pressure
        self.timestamp = datetime.utcnow()

