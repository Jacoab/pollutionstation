from flask import Flask
from flask_restful import Resource, Api
import json

# Initialization operations
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

app = Flask(__name__)
api = Api(app)

# Resources for the REST API

# Main loop
if __name__ == '__main__':
    app.run(debug=config.debug) 
