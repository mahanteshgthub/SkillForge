from flask import Blueprint

trainer_bp = Blueprint('trainer', __name__, url_prefix='/trainer')

from . import routes
