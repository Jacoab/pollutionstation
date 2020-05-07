from abc import ABC, abstractmethod
import board
from busio import I2C
import adafruit_bme680
import json
import time
#from sps30 import SPS30, eprint


class SensorStream:

    TEN_SECONDS = 10
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
        (400.0, 1000000.0): 'hazardous'
    }
    GAS_INDEX = {
        (521177.0, 431331.0): 'good',
        (431331.0, 213212.0): 'moderate',
        (213212.0, 54586.0): 'unhealthy for sensitive groups',
        (54586.0, 27080.0): 'unhealthy',
        (27080.0, 13591.0): 'very unhealthy',
        (13591.0, 8000.0): 'hazardous'
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
        data = {}
        if self.use_bme680:
            data = {
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
            data['sps30']['pm2p5'] = (data['sps30']['pm2p5'] - data['sps30']['nc2p5'])/11000
        return data

    def time_avg(self, time_period):
        #pm10p0_sum = 0.0
        #pm2p5_sum = 0.0
        gas_sum = 0.0
        collection_count = 0

        t_end = time.time() + time_period
        while time.time() < t_end:
            state_dict = self.get_data()
            #print(state_dict)
            collection_count += 1

            #pm10p0_sum += state_dict['sps30']['pm10p0']
            #pm2p5_sum += state_dict['sps30']['pm2p5']
            gas_sum += state_dict['gas']

        return gas_sum/collection_count

    def get_quality(self, avg):
        quality = {}
        for key in self.PM2p5_INDEX.keys():
            if key[0] <= avg['pm2p5_avg'] <= key[1]:
                quality['quality'] = self.PM2p5_INDEX[key]

        for key in self.GAS_INDEX:
            if key[0] >= avg >= key[1]:
                quality['quality'] = self.GAS_INDEX[key]

        return quality


if __name__ == '__main__':
    streamer = SensorStream()

    while True:
        avg_data = streamer.time_avg(SensorStream.TEN_SECONDS)
        quality = streamer.get_quality(avg_data)

        print('Air Quality: ', quality['quality'])
    #print('PM10p5 Quality: ', quality['pm10p0_quality'])
