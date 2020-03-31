from flask_restful import Resource
from flask_jwt import JWT, jwt_required, current_identity


class Config(Resource):
    SUCCESS = {"msg": "Success"}
    FAILURE = {"msg": "Failure"}
 
    def __init__(self, config):
        self.config = config

    def get(self):
        response = {"config": config}
        return response.update(SUCCESS)

    def put(self):
        pass


