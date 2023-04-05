from flask import Flask, request, Response
from decorators import *
from events import ClientEvent

app = Flask(__name__)

# https://spec.matrix.org/v1.6/application-service-api/#put_matrixappv1transactionstxnid
@app.put('/_matrix/app/v1/transactions/<string:txn_id>')
@authenticated
# @idempotent # there is a specific order we want, (if someone runs an unauthenticated query, we don't want it logged as already fulfilled)
# To be fair, the bridge will run fine most of the time without needing this
def process_events(txn_id):
    print("processing event", txn_id)
    events: list[ClientEvent] = (ClientEvent.from_dict(event) for event in request.json["events"])
    for event in events:
        # TODO: send to Zephyr
        print(event)
    return {}


# https://spec.matrix.org/v1.6/application-service-api/#get_matrixappv1roomsroomalias
@app.put('/_matrix/app/v1/rooms/<string:txn_id>')
@authenticated
def create_room(room_alias):
    # create room with nio and set permissions etc etc
    # authenticate with the right token (as_token i think)
    pass


# TODO: implement "thirdparty endpoints" (revert commit 4b12a963aa26f1f422eada928ac644dfcc394d87)
# I will not prioritize them since they don't seem to be used, even
app.run(debug=True)