from flask import session, redirect
from functools import wraps

BASE = "/diploma/fertilizer_recommendation"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(BASE + "/login")
        return f(*args, **kwargs)

    return decorated_function
