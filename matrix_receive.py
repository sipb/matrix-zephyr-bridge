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
@app.put('/transactions/<string:txn_id>')
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
            if not zephyr_location:
                print(f"Not bridging unknown event from {event.sender} in {event.room_id}", file=sys.stderr)
            cls, instance = zephyr_location
            send_zephyr_message(
                message=event.content['body'], # TODO: handle formatting, m.emote, etc
                cls=cls,
                instance=instance,
                display_name=matrix.get_room_display_name(event.room_id, event.sender),
                sender=get_zephyr_user(event.sender),

                # Matrix uses m.notice for (some) automated messages
                # Zephyr uses the AUTO opcode as metadata to indicate automated messages
                # Honor this metadata for both networks
                opcode='AUTO' if event.content['msgtype'] == 'm.notice' else DEFAULT_OPCODE,
            )
    return {}, 200


# https://spec.matrix.org/v1.6/application-service-api/#get_matrixappv1roomsroomalias
# @app.put('/rooms/<string:room_alias>')
# @app.put('/_matrix/app/v1/rooms/<string:room_alias>')
# The endpoing above does NOT work, because of slashes in the mxid being confused for path slashes
# The endpoint below DOES work
zephyr_class_instance_mxid = f'#{config.zephyr_room_prefix}<string:cls>{config.class_instance_separator}<string:instance>:{config.homeserver}'
@app.get(f'/rooms/{zephyr_class_instance_mxid}')
@app.put(f'/_matrix/app/v1/rooms/{zephyr_class_instance_mxid}')
@authenticated
# def create_room(room_alias):
def create_room(cls, instance):
    # print(f"Asked for room {room_alias}")
    # if not matrix.get_room_id(room_alias):
    if True: # TODO: fix lmao - actually check if it exists although the homeserver has no reason to call this if it exists
        # TODO: handle space creation for briding entire classes, etc
        # location = get_zephyr_location(room_alias)
        # if not location:
            # print(f"Returning 404, does not exist in Zephyr")
            # return {'errcode': 'edu.sipb.mit.not_implemented'}, 404
        # cls, instance = location
        # TODO: actually subscribe to it (to do zephyr->matrix bridging)
        # keep track of subscriptions somewhere??! (yaml? json? sqlite?)
        # TODO: tweak room options for good user experience (history visibility, public, do we want federation? etc)
        print(f"Actually creating room")
        room_id = matrix.create_room(
            alias_localpart=f'{config.zephyr_room_prefix}{cls}{config.class_instance_separator}{instance}',
            name=f'-c {cls} -i {instance}', # TODO: use a friendlier name
            preset='public_chat',
        )
        if not room_id:
            return {'errcode': 'edu.sipb.mit.unknown'}, 500
        print("Done creating", cls, instance)
    return {}


# TODO: implement "thirdparty endpoints" (revert commit 4b12a963aa26f1f422eada928ac644dfcc394d87)
# I will not prioritize them since they don't seem to be used, even