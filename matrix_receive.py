from flask import Flask, request, Response
from decorators import *
from events import ClientEvent
from config import config
from util import get_zephyr_location, send_zephyr_message, get_zephyr_user
import sys
import matrix
from constants import *

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
        if event.type == 'm.room.message':
            zephyr_location = get_zephyr_location(event.room_id)
            if zephyr_location is None:
                print(f"Not bridging unknown event from {event.sender} in {event.room_id}", file=sys.stderr)
            cls, instance = zephyr_location
            send_zephyr_message(
                message=event.content['body'], # TODO: handle formatting, m.emote, etc
                cls=cls,
                instance=instance,
                display_name=matrix.get_display_name(event.room_id, event.sender),
                sender=get_zephyr_user(event.sender),

                # Matrix uses m.notice for (some) automated messages
                # Zephyr uses the AUTO opcode as metadata to indicate automated messages
                # Honor this metadata for both networks
                opcode='AUTO' if event.content['msgtype'] == 'm.notice' else DEFAULT_OPCODE,
            )


# https://spec.matrix.org/v1.6/application-service-api/#get_matrixappv1roomsroomalias
@app.put('/_matrix/app/v1/rooms/<string:txn_id>')
@authenticated
def create_room(room_alias):
    # create room with nio and set permissions etc etc
    # authenticate with the right token (as_token i think)
    pass


# TODO: implement "thirdparty endpoints" (revert commit 4b12a963aa26f1f422eada928ac644dfcc394d87)
# I will not prioritize them since they don't seem to be used, even