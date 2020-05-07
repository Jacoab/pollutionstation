from flask import Flask, Response, request
from flask_restful import Resource, Api
from flask_cors import CORS
from sensorstream import SensorStream
#from resources import Config
import json
import board
from busio import I2C
import adafruit_bme680
import time

app = Flask(__name__)
api = CORS(app)

streamer = SensorStream()

'''
def get_data():
    return {
        'gas': bme680.gas,
        'temperature': bme680.temperature,
        'humidity': bme680.humidity,
        'pressure': bme680.pressure
    }


def time_avg(time_period):
    gas_sum = 0.0
    collection_count = 0

    t_end = time.time() + time_period
    while time.time() < t_end:
        state_dict = get_data()
        collection_count += 1

        gas_sum += state_dict['gas']

    return gas_sum / collection_count


def get_quality(avg):
    quality = {}

    for key in GAS_INDEX:
        if key[0] >= avg >= key[1]:
            quality['quality'] = GAS_INDEX[key]

    return quality


# Views for the REST API
@app.route('/data/raw')
def raw_stream():
    def generate():
        streamer = SensorStream()
        while True:
            raw_data = streamer.get_data()
            json_str = json.dumps(raw_data)
            formatted_data = 'data: ' + json_str + '\n\n'
            yield formatted_data

    return Response(generate(), mimetype='text/event-stream')
'''


@app.route('/data')
def quality_stream():
    interval = int(request.args.get('interval'))
    def generate():
        while True:
            avg_data = sensorstream.time_avg(interval)
            quality = sensorstream.get_quality(avg_data)
            json_str = json.dumps(quality)
            formatted_data = 'data: ' + json_str + '\n\n'
            yield formatted_data

    return Response(generate(), mimetype='text/event-stream')


    # Resources for the REST API
#api.add_resource(Config, '/config')

# URL Argument parsing for requests
#api.add_argument('username', type=Config)

# Main loop
if __name__ == '__main__':  
    app.run(host='0.0.0.0', debug=True)
