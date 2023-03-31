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


# TODO: implement "thirdparty endpoints" (revert commit 4b12a963aa26f1f422eada928ac644dfcc394d87)
# I will not prioritize them since they don't seem to be used, even