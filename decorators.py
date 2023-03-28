import functools
from flask import request

# Flask decorators

def authenticated(func):
    """
    Check that a request from the homeserver
    to the bridge is authenticated correctly
    """
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        if "Authorization" not in request.headers:
            return 401
        token = request.headers["Authorization"].split(" ")[-1]
        # TODO: check token and if wrong, return 403
        return func(*args, **kwargs)
    return wrapped
