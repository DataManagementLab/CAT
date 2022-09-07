from flask import Blueprint
from flask_restplus import Api

from .apis.auth import api as auth_ns
from .apis.database import api as database_ns
from .apis.nl import api as nl_ns
from .apis.rasa import api as rasa_ns

blueprint = Blueprint('apis', __name__, url_prefix='/api/v1')
api = Api(blueprint,
          title='Transactional Database Chatbot API',
          version='1.0',
          description='An API to analyze and annotate database schemas, generate training data and '
                      'train a RASA chatbot to perform database transactions with stored procedures'
          )

api.add_namespace(auth_ns, path=auth_ns.path)
api.add_namespace(database_ns, path=database_ns.path)
api.add_namespace(nl_ns, path=nl_ns.path)

# api.add_namespace(rasa_ns, path=rasa_ns.path)
