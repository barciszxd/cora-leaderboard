import importlib

from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Import all route modules to register them with the blueprint
for module_name in ['athletes', 'challenges', 'classification', 'exchange_token', 'health', 'webhook']:
    importlib.import_module(f'.{module_name}', __name__)
