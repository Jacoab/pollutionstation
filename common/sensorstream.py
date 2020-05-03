from abc import ABC, abstractmethod
import board
from busio import I2C
import adafruit_bme680
import json
import time
from .sps30 import SPS30, eprint


class SensorStream:

    THIRTY_SECONDS = 30
    MINUTE = 60
    THIRTY_MINUTES = 30 * MINUTE
    HOUR = 2 * THIRTY_MINUTES
    TWELVE_HOURS = 12 * HOUR
    DAY = 2 * TWELVE_HOURS

    PM2p5_INDEX = {
        (0.0, 12.0): 'good',
        (12.1, 35.4): 'moderate',
        (35.5, 55.4): 'unhealthy for sensitive groups',
        (55.5, 150.4): 'unhealthy',
        (150.5, 250.4): 'very unhealthy',
        (250.5, 500.4): 'hazardous'
    }
    PM10p0_INDEX = {
        (0.0, 54.0): 'good',
        (55.0, 154.0): 'moderate',
        (155.0, 254.0): 'unhealthy for sensitive groups',
        (255.0, 354.0): 'unhealthy',
        (355.0, 424.0): 'very unhealthy',
        (400.0, 700.0): 'hazardous'
    }

    def __init__(self, use_sps30=True, use_bme680=True):
        self.use_sps30 = use_sps30
        self.use_bme680 = use_bme680

        if self.use_bme680:
            i2c = I2C(board.SCL, board.SDA)
            self.bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
            self.bme680.sea_level_pressure = 1013.25
        else:
            self.bme680 = None

        if self.use_sps30:
            self.sps30 = SPS30()
            self.sps30.readArticleCode() or exit(1)

            self.sps30.reset()
            time.sleep(0.1)  # note: needed after reset

            self.sps30.readSerialNr()
            self.sps30.readCleaningInterval()

            self.sps30.initialize()

    def get_data(self):
        data = {'bme680': {}, 'sps30': {}}
        if self.use_bme680:
            data['bme680'] = {
                'gas': self.bme680.gas,
                'temperature': self.bme680.temperature,
                'humidity': self.bme680.humidity,
                'pressure': self.bme680.pressure
            }

        if self.use_sps30:
            ret = self.sps30.readDataReady()
            if ret == -1:
                eprint('resetting...', end='')
                self.sps30.bigReset()
                self.sps30.initialize()

            if ret == 0:
                time.sleep(0.1)

            data['sps30'] = self.sps30.readPMValues()
            time.sleep(0.9)

        return data

    def time_avg(self, time_period):
        pm10p0_sum = 0.0
        pm2p5_sum = 0.0
        gas_sum = 0.0
        collection_count = 0

        t_end = time.time() + time_period
        while time.time() < t_end:
            state_dict = self.get_data()

            collection_count += 1
            pm10p0_sum += state_dict['pm2p5']
            pm2p5_sum += state_dict['pm10p0']
            gas_sum += state_dict['gas']

        return {'pm10p0_avg': pm10p0_sum/collection_count,
                'pm2p5_avg': pm2p5_sum/collection_count,
                'gas_avg': pm2p5_sum}

    def stream(self):
        while True:
            avg_data = self.time_avg()
            json_str = json.dumps(avg_data)
            yield json_str
