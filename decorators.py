import functools
from flask import request
from config import config

# Flask decorators

def authenticated(func):
    """
    Check that a request from the homeserver
    to the bridge is authenticated correctly
    """
    # https://spec.matrix.org/v1.6/application-service-api/#authorization

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        if "Authorization" not in request.headers:
            return 401, {'errcode': 'edu.mit.sipb.zephyr_bridge_unauthorized'}
        token = request.headers["Authorization"].split(" ")[-1]
        if token != config["hs_token"]:
            return 403, {'errcode': 'edu.mit.sipb.zephyr_bridge_forbidden'}
        return func(*args, **kwargs)
    return wrapped


def idempotent(func):
    """
    Makes sure this function call occurs only once,
    by persisting the txnId after successfully completing
    [bridging], and checking the storage
    """

    # See https://spec.matrix.org/v1.6/application-service-api/#pushing-events

    @functools.wraps(func)
    def wrapped(txn_id, *args, **kwargs):
        # TODO: actually do something
        return func(txn_id, *args, **kwargs)
        # check if 200, then store it in the database
    return wrapped