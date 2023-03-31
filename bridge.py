from flask import Flask, request, Response
from decorators import *
from events import ClientEvent

app = Flask(__name__)

# https://spec.matrix.org/v1.6/application-service-api/#put_matrixappv1transactionstxnid
@idempotent
@authenticated
@app.put('/_matrix/app/v1/transactions/<txn_id:string>')
def process_events(txn_id):
    events = (ClientEvent.from_dict(event) for event in request.json)
    for event in events:
        # TODO: send to Zephyr
        print(event)
    return {}


# https://spec.matrix.org/v1.6/application-service-api/#get_matrixappv1roomsroomalias
@authenticated
@app.put('/_matrix/app/v1/rooms/<room_alias:string>')
def create_room(room_alias):
    # create room with nio and set permissions etc etc
    # authenticate with the right token (as_token i think)
    pass


"""
All the following endpoints are supposedly used by the homeserver
to present clients with more information about the bridge. 

Most of this should be unnecessary, since for practical purposes,
everything can be determined easily from the room/user names

So they'll be here as stubs that return 501 (not implemented) for now

Also for now, generate_registration.py will not tell the homeserver that it 
supports the protocol so the homeserver should not query these yet.

This seems to match the behavior of other bridges.

What is more, I'm not sure if any Matrix clients actually render this information
"""

# https://spec.matrix.org/v1.6/application-service-api/#get_matrixappv1thirdpartylocation
@authenticated
@app.get('/_matrix/app/v1/thirdparty/location')
def get_zephyr_location():
    # TODO: implement
    # if hardcoded behavior, simply string processing
    # otherwise, query the database to check
    return 501


# https://spec.matrix.org/v1.6/application-service-api/#get_matrixappv1thirdpartylocationprotocol
@authenticated
@app.get('/_matrix/app/v1/thirdparty/location/zephyr')
def get_matrix_location():
    # TODO: implement
    return 501


# https://spec.matrix.org/v1.6/application-service-api/#get_matrixappv1thirdpartyprotocolprotocol
@authenticated
@app.get('/_matrix/app/v1/thirdparty/protocol/zephyr')
def get_zephyr_info():
    # TODO: implement
    return 501


# https://spec.matrix.org/v1.6/application-service-api/#get_matrixappv1thirdpartyuser
@authenticated
@app.get('/_matrix/app/v1/thirdparty/user')
def get_zephyr_user():
    # TODO: implement
    return 501


@authenticated
@app.get('/_matrix/app/v1/thirdparty/user/zephyr')
def get_matrix_user():
    # TODO: implement
    return 501
