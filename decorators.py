# decorators.py
from functools import wraps
from flask import abort
from flask_login import current_user

def trainer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['Trainer', 'Admin']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function