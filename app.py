from flask import Flask, Response
from flask_restful import Resource, Api
#from resources import Config
import json
import board
import busio
import adafruit_bme680
import time

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c)

# Initialization operations
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

app = Flask(__name__)
api = Api(app)

# Views for the REST API
@app.route('/data')
def data_stream():
    def generate():
        while True:
            yield '{}'.format(sensor.gas)
            time.sleep(3)

    return Response(generate(), mimetype='text/event-stream') 

@app.route('/test')
def test():
    return "TEST BALLZ"

# Resources for the REST API
#api.add_resource(Config, '/config')

# URL Argument parsing for requests
#api.add_argument('username', type=Config)

# Main loop
if __name__ == '__main__':  
    app.run(host='0.0.0.0', debug=config["debug"]) 
