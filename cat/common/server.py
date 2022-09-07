import gevent.monkey

gevent.monkey.patch_all()
import os
import logging
from argparse import ArgumentParser
from flask import (Flask, )
from flask_cors import CORS
from flask_jwt_extended import JWTManager

import sys
sys.path.insert(0, './')

# RESTful apis
from cat.api.api import blueprint as api_v1
from cat.api.apis import auth as auth_ns

# socket.io namespaces
# REMOVED: Simulation from the frontend is disabled
# from flask_socketio import SocketIO
# from flask_restplus.inputs import boolean
# from threading import Thread
# from cat.api.sockets.simulation import SimulationNamespace

logger = logging.getLogger('api')


class RestApi:
    rest_app = None
    socketio_app = None

    def __init__(self,
                 host='localhost',
                 port=5001,
                 debug=True,
                 secret='secret',
                 passphrase='passphrase',
                 use_reloader=False,
                 cors_allowed_origins=[],
                 use_auth=False):
        self.secret = secret
        self.passphrase = passphrase
        self.host = host
        self.rest_port = port
        self.debug = debug
        self.use_reloader = use_reloader
        self.jwt_manager = JWTManager()
        self.cors_allowed_origins = cors_allowed_origins
        os.environ['JWT_ON'] = str(use_auth)
        os.environ['JWT_PASSPHRASE'] = self.passphrase

    def run_server(self):
        self.rest_app = Flask('REST API')
        self.configure_app(self.rest_app)
        self.rest_app.register_blueprint(api_v1)
        self.rest_app.run(host=self.host, port=self.rest_port, debug=self.debug, use_reloader=self.use_reloader)

    def configure_app(self, app):
        app.config['JWT_SECRET_KEY'] = self.secret
        app.config['JWT_TOKEN_LOCATION'] = ['cookies']
        app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
        app.config['JWT_REFRESH_COOKIE_PATH'] = f'{api_v1.root_path}/{auth_ns}/refresh'
        self.jwt_manager.init_app(app)
        CORS(app, resources={r'{api}/*'.format(api=api_v1.url_prefix): {'origins': self.cors_allowed_origins}})


if __name__ == '__main__':
    argparser = ArgumentParser()
    argparser.add_argument('-i', '--interface', default='127.0.0.1', type=str, help='Hostname to run server on')
    argparser.add_argument('-p', '--port', default=5001, type=int, help='Port to run REST API on')
    argparser.add_argument('-vv', '--debug', default=False, type=bool, help='Enable debug mode')
    argparser.add_argument('-j', '--jwt_on', default=False, type=bool, help='Wether to use JWT authentication for endpoints')
    argparser.add_argument('-s', '--jwt_secret', default='secret', type=str, help='The secret to protect api endpoints')
    argparser.add_argument('-a', '--jwt_passphrase', default='passphrase', type=str,
                           help='The secret to protect API endpoints with')
    argparser.add_argument('-c', '--cors_allowed_origins', default='*', type=str, help='Origins that are allowed to server')
    args = argparser.parse_args()

    rest = RestApi(host=args.interface, port=args.port, debug=args.debug, secret=args.jwt_secret,
                   passphrase=args.jwt_passphrase, cors_allowed_origins=args.cors_allowed_origins,
                   use_auth=args.jwt_on)
    rest.run_server()
